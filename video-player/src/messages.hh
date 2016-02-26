#pragma once

#include <string>

struct ControlMessage {
  enum class Type {
    QUIT,
    PLAY,
    PAUSE,
    CONTINUE,
    NOP
  };

  Type type;
  std::string payload;
};
