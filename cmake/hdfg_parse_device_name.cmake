# parse the extension from a file path
function(hdfg_parse_device_name filename device_name)
  # TODO not portable!
  string(REPLACE "/" ";" split_filename ${filename})

  # Get the last element
  list(LENGTH split_filename path_length)
  math(EXPR index "${path_length} - 1")
  list(GET split_filename ${index} relative_path)
  string(REPLACE "." ";" split_list ${relative_path})
  list(GET split_list 0 parsed_device_name)

  set(${device_name} ${parsed_device_name} PARENT_SCOPE)
endfunction()
