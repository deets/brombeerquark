#include "subprocess.hpp"
#include <chrono>
#include <thread>

int main(int argc, char *argv[])
{
  using namespace std::chrono_literals;
  while(true)
  {
    std::string buf;
    subprocess::popen cmd("vcgencmd", {"measure_temp"});
    std::getline(cmd.stdout(), buf);
    std::cout << buf << "\n";
    cmd.wait();
    std::this_thread::sleep_for(1s);
  }
  return 0;
}
