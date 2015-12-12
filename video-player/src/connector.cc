#include "connector.hh"

#include <nanomsg/nn.h>
#include <nanomsg/pair.h>

#include <cassert>
#include <stdexcept>
#include <iostream>

namespace {
  void raise_on_error(bool has_error) {
    if(has_error) {
      int error = nn_errno();
      throw std::runtime_error(nn_strerror(error));
    }
  }
}

Connector::Connector(const std::string& uri) 
  : _socket(-1)
  , _endpoint(-1)
  , _running(true)
{
  _socket = nn_socket(AF_SP, NN_PAIR);
  raise_on_error(_socket == -1);
  _endpoint = nn_bind(_socket, uri.c_str());
  raise_on_error(_endpoint == -1);

  _listenThread = std::thread([this]() {
      work();
    });

}

Connector::~Connector()
{
  _listenThread.join();
  if(_endpoint != -1) {
    nn_shutdown(_socket, _endpoint);
    _endpoint = -1;
  }
  if(_socket != -1) {
    nn_close(_socket);
    _socket = -1;
  }
}

bool Connector::running() const {
  return _running;
}

void Connector::work() {
  void *buf = NULL;
  auto len = nn_recv(_socket, &buf, NN_MSG, 0);
  _running = false;
  if(len > 0) {
    nn_freemsg(buf);
  }
}
