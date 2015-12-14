#pragma once

enum SEVERITY {
  DEBUG,
  INFO,
  ERROR
};

void setupLogging();

void LOG(const char* message);
