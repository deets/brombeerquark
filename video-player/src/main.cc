#include "log.hh"
#include "connector.hh"
#include "player.hh"

#include "bcm_host.h"
#include "ilclient.h"

#include <boost/program_options.hpp>

#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>


void play_video(Connector& connector)
{
  ControlMessage message;
  message.type = ControlMessage::Type::NOP;
  bool running = true;
  while(running) {
    switch(message.type) {
    case ControlMessage::Type::PLAY:
      LOG("PLAY");
      {
	Player player;
	message = player.play(message.payload, connector);
      }
      break;
    case ControlMessage::Type::QUIT:
      LOG("QUIT");
      running = false;
      break;
    default:
      LOG("WAITFORMESSAGE");
      message = connector.waitForMessage();
    }
  }
} // anonymous namespace

namespace po = boost::program_options;

int main (int argc, char **argv)
{
  const auto OPT_HELP = "help";
  const auto OPT_URI = "uri";

  std::string uri;

  po::options_description desc("Allowed options");
  desc.add_options()
    (OPT_HELP, "produce help message")
    (OPT_URI, po::value<std::string>(&uri), "nanomsg uri to serve data on")
    ;

  po::variables_map vm;
  po::store(po::parse_command_line(argc, argv, desc), vm);
  po::notify(vm);

  if(vm.count(OPT_HELP) || !vm.count(OPT_URI)) {
    std::cout << desc << "\n";
    return 1;
  }

  setupLogging();
  bcm_host_init();
  Connector connector(uri);
  play_video(connector);
  return 0;
}


