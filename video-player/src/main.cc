#include "log.hh"
#include "connector.hh"

#include "bcm_host.h"
#include "ilclient.h"

#include <boost/program_options.hpp>

#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

int play_video(Connector& connector, const std::string& filename)
{
   OMX_VIDEO_PARAM_PORTFORMATTYPE format;
   OMX_TIME_CONFIG_CLOCKSTATETYPE cstate;
   COMPONENT_T *video_decode = NULL, *video_scheduler = NULL, *video_render = NULL, *clock = NULL;
   COMPONENT_T *list[5];
   TUNNEL_T tunnel[4];
   ILCLIENT_T *client;
   FILE *in;
   int status = 0;
   unsigned int data_len = 0;

   memset(list, 0, sizeof(list));
   memset(tunnel, 0, sizeof(tunnel));
   if((in = fopen(filename.c_str(), "rb")) == NULL)
      return -2;

   if((client = ilclient_init()) == NULL)
   {
      fclose(in);
      return -3;
   }

   if(OMX_Init() != OMX_ErrorNone)
   {
      ilclient_destroy(client);
      fclose(in);
      return -4;
   }

   // create video_decode
   if(ilclient_create_component(
	  client, 
	  &video_decode, 
	  const_cast<char*>("video_decode"), 
	  static_cast<ILCLIENT_CREATE_FLAGS_T>(ILCLIENT_DISABLE_ALL_PORTS | ILCLIENT_ENABLE_INPUT_BUFFERS)) != 0)
      status = -14;
   list[0] = video_decode;

   // create video_render
   if(status == 0 && ilclient_create_component(client, &video_render, const_cast<char*>("video_render"), ILCLIENT_DISABLE_ALL_PORTS) != 0)
      status = -14;
   list[1] = video_render;

   // create clock
   if(status == 0 && ilclient_create_component(client, &clock, const_cast<char*>("clock"), ILCLIENT_DISABLE_ALL_PORTS) != 0)
      status = -14;
   list[2] = clock;

   memset(&cstate, 0, sizeof(cstate));
   cstate.nSize = sizeof(cstate);
   cstate.nVersion.nVersion = OMX_VERSION;
   cstate.eState = OMX_TIME_ClockStateWaitingForStartTime;
   cstate.nWaitMask = 1;
   if(clock != NULL && OMX_SetParameter(ILC_GET_HANDLE(clock), OMX_IndexConfigTimeClockState, &cstate) != OMX_ErrorNone)
      status = -13;

   // create video_scheduler
   if(status == 0 && ilclient_create_component(client, &video_scheduler, const_cast<char*>("video_scheduler"), ILCLIENT_DISABLE_ALL_PORTS) != 0)
      status = -14;
   list[3] = video_scheduler;

   set_tunnel(tunnel, video_decode, 131, video_scheduler, 10);
   set_tunnel(tunnel+1, video_scheduler, 11, video_render, 90);
   set_tunnel(tunnel+2, clock, 80, video_scheduler, 12);

   // setup clock tunnel first
   if(status == 0 && ilclient_setup_tunnel(tunnel+2, 0, 0) != 0)
      status = -15;
   else
      ilclient_change_component_state(clock, OMX_StateExecuting);

   if(status == 0)
      ilclient_change_component_state(video_decode, OMX_StateIdle);

   memset(&format, 0, sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE));
   format.nSize = sizeof(OMX_VIDEO_PARAM_PORTFORMATTYPE);
   format.nVersion.nVersion = OMX_VERSION;
   format.nPortIndex = 130;
   format.eCompressionFormat = OMX_VIDEO_CodingAVC;

   LOG("BEGIN");
   if(status == 0 &&
      OMX_SetParameter(ILC_GET_HANDLE(video_decode), OMX_IndexParamVideoPortFormat, &format) == OMX_ErrorNone &&
      ilclient_enable_port_buffers(video_decode, 130, NULL, NULL, NULL) == 0)
   {
      OMX_BUFFERHEADERTYPE *buf;
      int port_settings_changed = 0;
      int first_packet = 1;

      ilclient_change_component_state(video_decode, OMX_StateExecuting);

      LOG("RUNNING");
      bool running = true;
      while(running && (buf = ilclient_get_input_buffer(video_decode, 130, 1)) != NULL)
      {
	running = check_messages(connector);
         // feed data and wait until we get port settings changed
         unsigned char *dest = buf->pBuffer;
	 LOG("READ_DATA");
         data_len += fread(dest, 1, buf->nAllocLen-data_len, in);

         if(port_settings_changed == 0 &&
            ((data_len > 0 && ilclient_remove_event(video_decode, OMX_EventPortSettingsChanged, 131, 0, 0, 1) == 0) ||
             (data_len == 0 && ilclient_wait_for_event(video_decode, OMX_EventPortSettingsChanged, 131, 0, 0, 1,
                                                       ILCLIENT_EVENT_ERROR | ILCLIENT_PARAMETER_CHANGED, 10000) == 0)))
         {
	   LOG("PORT_SETTINGS_CHANGED");
            port_settings_changed = 1;

            if(ilclient_setup_tunnel(tunnel, 0, 0) != 0)
            {
               status = -7;
               break;
            }

            ilclient_change_component_state(video_scheduler, OMX_StateExecuting);

            // now setup tunnel to video_render
            if(ilclient_setup_tunnel(tunnel+1, 0, 1000) != 0)
            {
               status = -12;
               break;
            }

            ilclient_change_component_state(video_render, OMX_StateExecuting);
         }
	 
         if(!data_len || !running) {
	   LOG("!DATA_LEN || !RUNNING");
            break;
         }

         buf->nFilledLen = data_len;
         data_len = 0;

         buf->nOffset = 0;
         if(first_packet)
         {
            buf->nFlags = OMX_BUFFERFLAG_STARTTIME;
            first_packet = 0;
         }
         else
            buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN;

         if(OMX_EmptyThisBuffer(ILC_GET_HANDLE(video_decode), buf) != OMX_ErrorNone)
         {
            status = -6;
            break;
         }
      }
      LOG("AFTERRUNNING");
      buf->nFilledLen = 0;
      buf->nFlags = OMX_BUFFERFLAG_TIME_UNKNOWN | OMX_BUFFERFLAG_EOS;

      if(OMX_EmptyThisBuffer(ILC_GET_HANDLE(video_decode), buf) != OMX_ErrorNone)
         status = -20;

	// wait for EOS from render
      LOG("BEFOREWAIT");
      while(running && ilclient_wait_for_event(video_render, OMX_EventBufferFlag, 90, 0, OMX_BUFFERFLAG_EOS, 0,
                              ILCLIENT_BUFFER_FLAG_EOS, 100) != 0)
	{
	  running = check_messages(connector);
	  LOG("DURINGWAIT");
	}

      // need to flush the renderer to allow video_decode to disable its input port
      LOG("AFTERWAIT");
      ilclient_flush_tunnels(tunnel, 0);
      LOG("TUNNELSFLUSHED");
   }

   fclose(in);

   ilclient_disable_tunnel(tunnel);
   ilclient_disable_tunnel(tunnel+1);
   ilclient_disable_tunnel(tunnel+2);
   ilclient_disable_port_buffers(video_decode, 130, NULL, NULL, NULL);
   ilclient_teardown_tunnels(tunnel);

   ilclient_state_transition(list, OMX_StateIdle);
   ilclient_state_transition(list, OMX_StateLoaded);

   ilclient_cleanup_components(list);

   OMX_Deinit();

   ilclient_destroy(client);
   return status;
}
} // anonymous namespace

namespace po = boost::program_options;

int main (int argc, char **argv)
{
  const auto OPT_HELP = "help";
  const auto OPT_URI = "uri";
  const auto OPT_VIDEO = "video";

  std::string uri;
  std::string video;

  po::options_description desc("Allowed options");
  desc.add_options()
    (OPT_HELP, "produce help message")
    (OPT_URI, po::value<std::string>(&uri), "nanomsg uri to serve data on")
    (OPT_VIDEO, po::value<std::string>(&video), "the initial file to run")
    ;

  po::variables_map vm;
  po::store(po::parse_command_line(argc, argv, desc), vm);
  po::notify(vm);

  if(vm.count(OPT_HELP) || !vm.count(OPT_VIDEO) || !vm.count(OPT_URI)) {
    std::cout << desc << "\n";
    return 1;
  }

  setupLogging();
  bcm_host_init();
  Connector connector(uri);
  return play_video(connector, video);
}


