cmake_minimum_required (VERSION 3.0)
project (MPU6050)
include(FindPkgConfig)
set(CMAKE_CXX_STANDARD 11)
#set(CMAKE_CXX_FLAGS "-std=c++11 -DUSE_VCHIQ_ARM -DHAVE_LIBBCM_HOST -DUSE_EXTERNAL_LIBBCM_HOST")
set(CMAKE_C_FLAGS "-DSTANDALONE -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -DTARGET_POSIX -D_LINUX -fPIC -DPIC -D_REENTRANT -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -U_FORTIFY_SOURCE -Wall -g -DHAVE_LIBOPENMAX=2 -DOMX -DOMX_SKIP64BIT -ftree-vectorize -pipe -DUSE_EXTERNAL_OMX -DHAVE_LIBBCM_HOST -DUSE_EXTERNAL_LIBBCM_HOST -DUSE_VCHIQ_ARM -Wno-psabi")
LINK_DIRECTORIES(/opt/vc/lib)

#pkg_search_module(JSONCPP REQUIRED jsoncpp)

add_library(
	ilclient
	ilclient/ilclient.c
	ilclient/ilcore.c
)

target_include_directories(
	ilclient SYSTEM PRIVATE 
	/opt/vc/include
	/opt/vc/include/interface/vcos/pthreads
	/opt/vc/include/interface/vmcs_host/linux
	/opt/vc/include/interface/vchiq_arm
	)

target_link_libraries(
	ilclient
	GLESv2
	EGL
	openmaxil
	vcos
	vchiq_arm
	bcm_host
	pthread
)

add_executable(simple-videoplayer
   src/main.c
)


target_include_directories(
	simple-videoplayer SYSTEM PRIVATE 
	src 
	ilclient
	/opt/vc/include
	/opt/vc/include/interface/vcos/pthreads
	/opt/vc/include/interface/vmcs_host/linux
	/opt/vc/include/interface/vchiq_arm
#	"${JSONCPP_INCLUDE_DIRS}"
)


target_link_libraries(
	simple-videoplayer
	ilclient
	boost_program_options	
)




