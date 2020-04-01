### Project info
cmake_minimum_required(VERSION 3.15)

project(cpp-subprocess)

add_executable(
  cpp-subprocess
  src/cpp-subprocess.cpp
  )

target_compile_features(cpp-subprocess PRIVATE cxx_std_17)
target_compile_options(cpp-subprocess PRIVATE -fconcepts)
target_link_libraries(cpp-subprocess PRIVATE pthread)

install(TARGETS cpp-subprocess RUNTIME DESTINATION ${DESTDIR}/usr/bin)
