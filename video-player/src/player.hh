#pragma once

#include "connector.hh"

#include "bcm_host.h"
#include "ilclient.h"

struct IClientHelper {
  ILCLIENT_T *client;

  IClientHelper();
  ~IClientHelper();
};

struct ComponentHelper {
  COMPONENT_T *component;

  ComponentHelper(IClientHelper&, const char* name, ILCLIENT_CREATE_FLAGS_T flags);
  ~ComponentHelper();
  ComponentHelper(const ComponentHelper&) = delete;
  ComponentHelper operator=(const ComponentHelper&) = delete;

  void changeState(OMX_STATETYPE state);

  template<typename ... CH>
  static void cleanup(CH& ... components);

  template<typename ... CH>
  static void stateTransition(OMX_STATETYPE, CH& ... components);

};

class Player {

public:
  Player();
  ~Player();
  void play(const std::string& filename, Connector& connector);

private:
  IClientHelper _iclient;
  ComponentHelper _video_decode, _video_scheduler, _video_render, _clock;

  TUNNEL_T _tunnel[4];
};
