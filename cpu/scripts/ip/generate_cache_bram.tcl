source [file normalize "./cpu/scripts/header.tcl"]

create_ip -name blk_mem_gen -vendor xilinx.com -library ip -version 8.4 -module_name cache_bram
set_property -dict [list \
  CONFIG.Byte_Size {8} \
  CONFIG.Use_Byte_Write_Enable {true} \
  CONFIG.Write_Depth_A {32} \
  CONFIG.Write_Width_A {128} \
] [get_ips cache_bram]
# generate_target {instantiation_template} [get_files "${ip_dir}/cache_bram.xci"]
generate_target {instantiation_template} [get_ips cache_bram]
config_ip_cache -export [get_ips -all cache_bram]
export_ip_user_files -of_objects [get_ips cache_bram] -no_script -sync -force -quiet