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


void play_video(Connector& connector, std::string filename)
{
  while(true) {
    boost::optional<ControlMessage> message;
    {
      Player player;
      message = player.play(filename, connector);
    }
    LOG(message ? "GOTMESSAGE" : "NOMESSAGE");
    if(message && (*message).type == ControlMessage::Type::PLAY) {
      LOG("PLAY");
      LOG((*message).payload.c_str());
      filename = (*message).payload;
    } else {
      break;
    }
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
  play_video(connector, video);
  return 0;
}


