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

  ControlMessage parseMessage(const char* buf, int len) {
    std::string command;
    std::string payload;
    ControlMessage res;
    int separator = 0;
    for(;separator < len; separator++) {
      if(buf[separator] == '=') {
	break;
      }
    }
    command = std::string(buf, separator);
    separator += 1;
    if(separator < len) {
      payload = std::string(buf + separator, len - separator);
    }
    if(command == "quit") {
      res.type = ControlMessage::Type::QUIT;
    } else if(command == "play") {
      res.type = ControlMessage::Type::PLAY;
      res.payload = payload;
    }
    return res;
  }
}

Connector::Connector(const std::string& uri) 
  : _socket(-1)
  , _endpoint(-1)
  , _running(true)
  , _pollTimeout(100)
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
  _running = false;
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

boost::optional<ControlMessage> Connector::message() {
  std::lock_guard<std::mutex> lock(_messageMutex);
  boost::optional<ControlMessage> result;
  if(_message) {
    result = _message;
    _message = boost::none;
  }
  return result;
}

void Connector::setMessage(const ControlMessage& message) {
  std::lock_guard<std::mutex> lock(_messageMutex);
  _message = message;
}

void Connector::work() {
  struct nn_pollfd pollData;
  pollData.fd = _socket;
  pollData.events = NN_POLLIN | NN_POLLOUT;

  while(_running) {
    pollData.revents = 0;
    auto rc = nn_poll(&pollData, 1, _pollTimeout);
    raise_on_error(rc == -1);
    if(pollData.revents & NN_POLLIN) {
      void *buf = NULL;
      auto len = nn_recv(_socket, &buf, NN_MSG, 0);
      _running = false;
      if(len > 0) {
	setMessage(parseMessage(reinterpret_cast<const char*>(buf), len));
	nn_freemsg(buf);
      }
    }
  }
}
