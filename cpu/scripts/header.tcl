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
	"core.sv"
	"icache.sv"
	"lib/debouncer.sv"
	"lib/edge_detector_pos.sv"
}

set_part $fpga_part

file mkdir $build_dir
cd $build_dir

read_ip "${ip_dir}/cache_bram/cache_bram.xci"
read_ip "${ip_dir}/cache_tag_bram/cache_tag_bram.xci"