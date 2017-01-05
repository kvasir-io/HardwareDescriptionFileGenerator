# Generate targets for all .svd files
# If the name ends in .svd, generate a target for it
# If the data/extensions directory includes a .json file with the same target name,
# add that as a target name

include(cmake/hdfg_generate_device.cmake)

function(hdfg_generate_targets_for_directory input_dir target_dir)
  file(GLOB_RECURSE svd_files "${input_dir}/*.svd")
  foreach(svd_file ${svd_files})
    hdfg_parse_device_name(${svd_file} device_name)

    set(extension "")
    # Look for the device under data/extensions and pass the extension if it exists
    file(GLOB_RECURSE extension_files "${input_dir}/extensions/*.json")
    foreach(extension_file ${extension_files})
      hdfg_parse_device_name(${extension_file} ext_device_name)
      if(${device_name} EQUAL ${ext_device_name})
        set(extension ${extension_file})
      endif()
    endforeach()

    hdfg_generate_device(
      ${svd_file}
      ${target_dir}
      ${extension}
    )
  endforeach()
endfunction()
