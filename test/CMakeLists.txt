# If testing is enabled
# For each generated header, add this test target (has dependency on all generated targets)
# Then compile the target

file(GLOB_RECURSE svd_files "${CMAKE_SOURCE_DIR}/data/*.svd")

foreach(svd_file ${svd_files})
  hdfg_parse_device_name(${svd_file} device_name)
  if(TARGET test_headers_generated_${device_name})
    message(WARNING "Tried to add test test_headers_generated_${device_name} which already exists.")
  elseif(TARGET ${device_name}_generated)
    add_custom_target(
      test_headers_generated_${device_name}
      ALL
      COMMAND python2 ${CMAKE_CURRENT_LIST_DIR}/glom_all_headers.py
      ${CMAKE_CURRENT_BINARY_DIR}/${device_name}/test_headers.hpp ${svd_file})

    add_executable(test_headers_${device_name} test_headers.cpp)
    add_dependencies(test_headers_${device_name} test_headers_generated_${device_name})
    add_dependencies(test_headers_${device_name} ${device_name}_generated)
    target_include_directories(test_headers_${device_name} PUBLIC
      ${CMAKE_BINARY_DIR}/include ${CMAKE_SOURCE_DIR}/deps/Kvasir/Lib ${CMAKE_CURRENT_BINARY_DIR}/${device_name}/)
    target_compile_options(test_headers_${device_name} PUBLIC "-std=c++11")
  endif()

endforeach()
