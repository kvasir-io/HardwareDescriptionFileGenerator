# If testing is enabled
# For each generated header, add this test target (has dependency on all generated targets
# Then compile the target

add_custom_target(
  test_headers_generated
  ALL
  COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_LIST_DIR}/glom_all_headers.py ${CMAKE_BINARY_DIR} ${CMAKE_CURRENT_BINARY_DIR}/test_headers.cpp
)

add_executable(test_headers ${CMAKE_CURRENT_BINARY_DIR}/test_headers.cpp)
file(GLOB_RECURSE svd_files "${CMAKE_SOURCE_DIR}/data/*.svd")
add_dependencies(test_headers test_headers_generated)
foreach(svd_file ${svd_files})
  hdfg_parse_device_name(${svd_file} device_name)
  add_dependencies(test_headers ${device_name}_generated test_headers_generated)
  # TODO Install kvasir
  target_include_directories(test_headers PUBLIC ${CMAKE_BINARY_DIR}/include ${CMAKE_BINARY_DIR}/Lib)
endforeach()
