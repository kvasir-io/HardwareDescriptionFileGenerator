cmake_minimum_required(VERSION 3.2.0)
project(HardwareDescriptionFileGenerator)
include(cmake/hdfg_generate_targets_for_directory.cmake)

set(DATA_DIRECTORY "deps/chip/chips")

# Options
# BOARDS
# VENDORS
if(DEFINED BOARDS)
  if(NOT DEFINED TARGET_DIRS)
    set(TARGET_DIRS "")
  endif()

  foreach(board ${BOARDS})
    # TODO HmmMMmmM
    file(GLOB_RECURSE target_boards "${DATA_DIRECTORY}/*/${board}.svd")
    list(APPEND TARGET_DIRS ${target_boards})
  endforeach()
endif()

if(DEFINED VENDORS)
  if(NOT DEFINED TARGET_DIRS)
    set(TARGET_DIRS "")
  endif()

  foreach(vendor ${VENDORS})
    file(GLOB_RECURSE target_boards ${DATA_DIRECTORY}/${vendor}/*.svd)
    list(APPEND TARGET_DIRS ${target_boards})
  endforeach()
endif()

if(NOT DEFINED TARGET_DIRS)
  file(GLOB_RECURSE svd_files "${DATA_DIRECTORY}/*.svd")
  set(TARGET_DIRS ${svd_files})
endif()

message(STATUS "Generating targets for ${TARGET_DIRS}")
hdfg_generate_targets_for_directory(${TARGET_DIRS} ${CMAKE_BINARY_DIR}/include)

if(${BUILD_TESTING})
  add_subdirectory(test)
endif()
