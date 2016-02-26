#pragma once

#include "messages.hh"

#include <boost/optional.hpp>

#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <condition_variable>

class Connector {

public:
  Connector(const std::string& uri);
  ~Connector();

  ControlMessage waitForMessage();
  boost::optional<ControlMessage> message();

private:

  void work();
  void setMessage(const ControlMessage& message);

  int _socket;
  int _endpoint;
  std::atomic<bool> _running;

  std::thread _listenThread;

  int _pollTimeout;

  boost::optional<ControlMessage> _message;
  std::mutex _messageMutex;
  std::condition_variable _messageSignal;
};
