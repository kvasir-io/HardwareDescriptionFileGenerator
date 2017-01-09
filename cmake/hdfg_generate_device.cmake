include(cmake/hdfg_parse_device_name.cmake)

function(hdfg_generate_device input_file output_directory)
  # Generate the output files using parse_device.py
  # and retrieve the names of the generated files
  # ARGN represents optional arguments
  set(extra_args ${ARGN})
  list(LENGTH extra_args n_args)
  if(${n_args} GREATER 0)
    list(GET extra_args 0 extension_filename)
  else()
    set(extension_filename "")
  endif()

  # TODO: install the module and have a separate Python 'scripts' folder to invoke these
  set(module_directory ${CMAKE_SOURCE_DIR}/src/svd_parser)

  hdfg_parse_device_name(${input_file} device_name)
  # MESSAGE(STATUS "generating code for ${device_name}")

  # Split on .
  add_custom_command(
    OUTPUT ${device_name}_generated_
    COMMAND ${PYTHON_EXECUTABLE} ${module_directory}/parse_device.py ${input_file} ${output_directory} ${extension_filename}
    COMMAND ${CMAKE_COMMAND} -E touch ${device_name}_generated_
    DEPENDS ${input_file} ${extension_filename}
    ${module_directory}/parse_device.py
    ${module_directory}/parser_utils.py
    ${module_directory}/format_utils.py
    ${module_directory}/templates/io.hpp.template
    ${module_directory}/templates/peripheral.hpp.template
  )

  add_custom_target(${device_name}_generated DEPENDS ${device_name}_generated_)

  # add_executable(test_headers_${device_name} /tmp/test_headers.cpp)
  # add_dependencies(test_headers_${device_name} ${device_name}_generated)
endfunction()

