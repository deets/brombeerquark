#pragma once

#include <string>
#include <thread>
#include <atomic>

class Connector {

public:
  Connector(const std::string& uri);
  ~Connector();

  bool running() const;

private:

  void work();

  int _socket;
  int _endpoint;
  std::atomic<bool> _running;

  std::thread _listenThread;

  int _pollTimeout;
};
