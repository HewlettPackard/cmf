cmake_minimum_required(VERSION 3.22)
project(cmflib-fortran-lib VERSION "0.0.1")
enable_language(C)
enable_language(Fortran)

if(NOT CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
  set(CMAKE_Fortran_MODULE_DIRECTORY "${CMAKE_INSTALL_PREFIX}/include")
endif()

include(GNUInstallDirs)
include(CMakePrintHelpers)

# Configure Python
set (Python3_FIND_VIRTUALENV FIRST)
find_package(Python3 COMPONENTS Interpreter Development)

# Print Python related variables for troubleshooting
cmake_print_variables(Python3_LIBRARIES)
cmake_print_variables(Python3_INCLUDE_DIRS)

# Compile into a shared library
set(C_SRC
  libsrc/log_metric/log_metric.c
  libsrc/log_metric/log_metric.F90
)
add_library(cmflib SHARED ${C_SRC})
target_include_directories(cmflib PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/>
  $<INSTALL_INTERFACE:include/>
  ${Python3_INCLUDE_DIRS}
)
target_link_libraries(cmflib PRIVATE ${Python3_LIBRARIES})
set_property(TARGET cmflib PROPERTY PUBLIC_HEADER include/log_metric.h)
install(TARGETS cmflib)

# Compile the C example
add_executable(cmf-c-example examples/compiled-applications/main.c)
target_link_libraries(cmf-c-example PRIVATE cmflib)
target_include_directories(cmf-c-example PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Compile the Fortran example
add_executable(cmf-fortran-example examples/compiled-applications/main.F90)
target_link_libraries(cmf-fortran-example PRIVATE cmflib)
target_include_directories(cmf-fortran-example PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)