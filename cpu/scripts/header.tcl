set fpga_part "xc7a200tsbg484-1"

set root_dir [file normalize "./cpu"]
set build_dir "${root_dir}/build"
set rtl_dir "${root_dir}/rtl"
set constraints_dir "${root_dir}/constraints"
set testbench_dir "${root_dir}/testbench"
set scripts_dir "${root_dir}/scripts"
set ip_dir "${root_dir}/ip"

set_param general.maxThreads 8

set rtl_files {
	"constants.svh"
	"types.sv"
	"top.sv"
	"lib/debouncer.sv"
	"lib/edge_detector_pos.sv"
}

set_part $fpga_part

cd $build_dir

read_ip "${ip_dir}/cache_bram.xci"

# set needs_ip 0

# if { ![file exists "${ip_dir}/cache_ram.xci"] } {
# 	set needs_ip 1
# }

# if { $needs_ip } {
# 	create_project -in_memory
# }

# CONFIG.Coe_File {"${testbench_dir}/instructions.coe"} \
# 		CONFIG.Load_Init_File {true} \

# if { ![file exists "${ip_dir}/cache_bram.xci"] } {
# 	create_ip -name blk_mem_gen -vendor xilinx.com -library ip -version 8.4 -module_name cache_bram
# 	set_property -dict [list \
# 		CONFIG.Byte_Size {8} \
# 		CONFIG.Register_PortA_Output_of_Memory_Core {false} \
# 		CONFIG.Register_PortA_Output_of_Memory_Primitives {true} \
# 		CONFIG.Use_Byte_Write_Enable {true} \
# 		CONFIG.Use_REGCEA_Pin {false} \
# 		CONFIG.Use_RSTA_Pin {false} \
# 		CONFIG.Write_Depth_A {32} \
# 		CONFIG.Write_Width_A {128} \
# 	] [get_ips cache_bram]
# 	# generate_target {instantiation_template} [get_files "${ip_dir}/cache_bram.xci"]

# 	generate_target all [get_ips]
# 	synth_ip [get_ips]
# }