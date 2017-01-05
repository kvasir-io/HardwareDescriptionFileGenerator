cmake_minimum_required(VERSION 3.2.0)
project(HardwareDescriptionFileGenerator)
include(cmake/hdfg_generate_targets_for_directory.cmake)

# Default behavior will be to generate headers for everything in data/

# TODO set up the Python dependencies properly with Pip (beautiful soup)

find_package(PythonInterp)

# TODO Filtering options? What should the interface look like?
hdfg_generate_targets_for_directory("data" ${CMAKE_CURRENT_BINARY_DIR})

# Test: try to compile all of the resulting targets
