#pragma once

#include <string>

struct ControlMessage {
  enum class Type {
    QUIT,
    PLAY,
    PAUSE,
    CONTINUE
  };

  Type type;
  std::string payload;
};
