#include "player.hh"
#include "log.hh"

#include <exception>
#include <sstream>

namespace {

bool check_messages(Connector& connector) {
  auto message = connector.message();
  if(message) {
    switch((*message).type) {
    case ControlMessage::Type::QUIT:
      LOG("MESSAGEQUIT");
      return false;
    default:
      break;
    }
  }
  return true;
}

template<typename A>
std::string formatMessage(std::stringstream& ss, A arg) {
  ss << arg;
  return ss.str();
}


template<typename A, typename ... Args>
std::string formatMessage(std::stringstream& ss, A arg, Args ... args) {
  ss << arg;
  return formatMessage(ss, args...);
}

template<typename ... Args>
std::string formatMessage(Args ... args) {
  std::stringstream ss;
  return formatMessage(ss, args...);
}
} // anonymous namespace

IClientHelper::IClientHelper() 
  : client(nullptr)
{
  OMX_Init();
  client = ilclient_init();
  if(!client) {
    throw std::runtime_error("client couldn't be created");
  }
}

IClientHelper::~IClientHelper() 
{
  ilclient_destroy(client);
  OMX_Deinit();
}


ComponentHelper::ComponentHelper(
    IClientHelper& client, 
    const char* name, 
    ILCLIENT_CREATE_FLAGS_T flags) 
  : component(nullptr)
{
  if(ilclient_create_component(
	 client.client, 
	  &component, 
	  const_cast<char*>(name), 
	 flags) != 0) {
    throw std::runtime_error(
	formatMessage("component ", name, " couldn't be created"));
  }
}

ComponentHelper::~ComponentHelper() 
{
  assert(component == nullptr);
}

void ComponentHelper::changeState(OMX_STATETYPE state)
{
  if(ilclient_change_component_state(component, state) != 0) {
    throw std::runtime_error("component couldn't change state");
  }
}

template<typename ... CH>
void ComponentHelper::cleanup(CH& ... components)
{
  std::vector<COMPONENT_T*> list{components.component ...};
  list.push_back(nullptr);
  ilclient_cleanup_components(list.data());
}

template<typename ... CH>
void ComponentHelper::stateTransition(OMX_STATETYPE state, CH& ... components) 
{
  std::vector<COMPONENT_T*> list{components.component ...};
  list.push_back(nullptr);
  ilclient_state_transition(list.data(), state);
}


Player::Player() 
  : _iclient{}
  , _video_decode{
    _iclient, 
      "video_decode", 
      static_cast<ILCLIENT_CREATE_FLAGS_T>(ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS)
      }
  , _video_scheduler{
    _iclient, 
      "video_scheduler", 
      static_cast<ILCLIENT_CREATE_FLAGS_T>(ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS)
      }
  , _video_render{
    _iclient, 
      "video_render", 
      static_cast<ILCLIENT_CREATE_FLAGS_T>(ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS)
      }
  , _clock{
    _iclient, 
      "clock", 
      static_cast<ILCLIENT_CREATE_FLAGS_T>(ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS)
      }
{
  OMX_VIDEO_PARAM_PORTFORMATTYPE format;
  OMX_TIME_CONFIG_CLOCKSTATETYPE cstate;

  memset(_tunnel, 0, sizeof(_tunnel));
  memset(&cstate, 0, sizeof(cstate));  
  memset(&format, 0, sizeof(format));
  
  if(OMX_Init() != OMX_ErrorNone)
  {
    throw std::runtime_error("OMX_Init failed");
  }
  
  cstate.nSize = sizeof(cstate);
  cstate.nVersion.nVersion = OMX_VERSION;
  cstate.eState = OMX_TIME_ClockStateWaitingForStartTime;
  cstate.nWaitMask = 1;
  if(OMX_SetParameter(
	 ILC_GET_HANDLE(_clock.component), 
	 OMX_IndexConfigTimeClockState, 
	 &cstate
     ) != OMX_ErrorNone) {
    throw std::runtime_error("clock not working");
  }

  set_tunnel(_tunnel, _video_decode.component, 131, _video_scheduler.component, 10);
  set_tunnel(_tunnel+1, _video_scheduler.component, 11, _video_render.component, 90);
  set_tunnel(_tunnel+2, _clock.component, 80, _video_scheduler.component, 12);

  if(ilclient_setup_tunnel(_tunnel+2, 0, 0) != 0) {
    throw std::runtime_error("clock tunnel setup failed");
  }  

  ilclient_change_component_state(_clock.component, OMX_StateExecuting);
  ilclient_change_component_state(_video_decode.component, OMX_StateIdle);

  format.nSize = sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE);
  format.nVersion.nVersion = OMX_VERSION;
  format.nPortIndex = 130;
  format.eCompressionFormat = OMX_VIDEO_CodingAVC;

  if(OMX_SetParameter(
	 ILC_GET_HANDLE(_video_decode.component), 
	 OMX_IndexParamVideoPortFormat, 
	 &format) != OMX_ErrorNone ||
     ilclient_enable_port_buffers(_video_decode.component, 130, NULL, NULL, NULL) != 0) {
    throw std::runtime_error("Couldn't setup compression format");
  }

}

Player::~Player() 
{
  ilclient_flush_tunnels(_tunnel, 0);
  LOG("TUNNELSFLUSHED");
  
  ilclient_disable_tunnel(_tunnel);
  ilclient_disable_tunnel(_tunnel+1);
  ilclient_disable_tunnel(_tunnel+2);
  ilclient_disable_port_buffers(_video_decode.component, 130, NULL, NULL, NULL);
  ilclient_teardown_tunnels(_tunnel);
  
  ComponentHelper::stateTransition(OMX_StateIdle, _video_decode, _video_scheduler, _video_render, _clock);
  ComponentHelper::stateTransition(OMX_StateLoaded, _video_decode, _video_scheduler, _video_render, _clock);
  ComponentHelper::cleanup(_video_decode, _video_scheduler, _video_render, _clock);
  
  // this is a workaround for the GCC bug that prevents me from unpacking
  // the variadic template args in cleanup
  for(auto pComponent : { &_video_decode, &_video_scheduler, &_video_render, &_clock }) {
    pComponent->component = nullptr;
  }
}

void Player::play(const std::string& filename, Connector& connector)
{
  FILE *in;
  if((in = fopen(filename.c_str(), "rb")) == NULL) {
    throw std::runtime_error("couldn't open file");
  }

  LOG("RUNNING");

  bool port_settings_changed = false;
  bool first_packet = true;
  bool running = true;  
  int data_len = 0;
  OMX_BUFFERHEADERTYPE *buf;

  _video_decode.changeState(OMX_StateExecuting);

  while(running && (buf = ilclient_get_input_buffer(_video_decode.component, 130, 1)) != NULL) {
    running = check_messages(connector);
    // feed data and wait until we get port settings changed
    unsigned char *dest = buf->pBuffer;
    LOG("READ_DATA");
    data_len += fread(dest, 1, buf->nAllocLen-data_len, in);
      
    if(!port_settings_changed &&
       ((data_len > 0 && ilclient_remove_event(_video_decode.component, OMX_EventPortSettingsChanged, 131, 0, 0, 1) == 0) ||
	(data_len == 0 && ilclient_wait_for_event(_video_decode.component, OMX_EventPortSettingsChanged, 131, 0, 0, 1, ILCLIENT_EVENT_ERROR | ILCLIENT_PARAMETER_CHANGED, 10000) == 0)))  {
      LOG("PORT_SETTINGS_CHANGED");
      port_settings_changed = true;
      if(ilclient_setup_tunnel(_tunnel, 0, 0) != 0) {
	throw std::runtime_error("couldn't setup tunnel for decoder");
      }
      _video_scheduler.changeState(OMX_StateExecuting);
      // now setup tunnel to video_render
      if(ilclient_setup_tunnel(_tunnel+1, 0, 1000) != 0) {
	throw std::runtime_error("couldn't setup tunnel for renderer");
      }
      _video_render.changeState(OMX_StateExecuting);
    }

    if(!data_len || !running) {
      LOG("!DATA_LEN || !RUNNING");
      break;
    }
    buf->nFilledLen = data_len;
    data_len = 0;
    
    buf->nOffset = 0;
    if(first_packet) {
      buf->nFlags = OMX_BUFFERFLAG_STARTTIME;
      first_packet = false;
    } else {
      buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN;
    }
    if(OMX_EmptyThisBuffer(ILC_GET_HANDLE(_video_decode.component), buf) != OMX_ErrorNone) {
      throw std::runtime_error("couldn't empty decode buffer");
    }
  }
  LOG("AFTERRUNNING");
  buf->nFilledLen = 0;
  buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN | OMX_BUFFERFLAG_EOS;

  if(OMX_EmptyThisBuffer(ILC_GET_HANDLE(_video_decode.component), buf) != OMX_ErrorNone) {
    throw std::runtime_error("can't empty decode buffer");
  }
  // wait for EOS from render
  LOG("BEFOREWAIT");
  while(running && 
	ilclient_wait_for_event(
	    _video_render.component, 
	    OMX_EventBufferFlag, 90, 0, OMX_BUFFERFLAG_EOS, 0,
	    ILCLIENT_BUFFER_FLAG_EOS, 100) != 0) {
      running = check_messages(connector);
      LOG("DURINGWAIT");
  }
  
  // need to flush the renderer to allow video_decode to disable its input port
  LOG("AFTERWAIT");
  fclose(in);
}
