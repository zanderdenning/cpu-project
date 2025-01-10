set fpga_part "xc7a200tsbg484-1"

set root_dir [file normalize "./cpu"]
set build_dir "${root_dir}/build"
set rtl_dir "${root_dir}/rtl"
set constraints_dir "${root_dir}/constraints"
set testbench_dir "${root_dir}/testbench"
set scripts_dir "${root_dir}/scripts"

set_param general.maxThreads 8

set rtl_files {
	"top.sv"
	"lib/debouncer.sv"
	"lib/edge_detector_pos.sv"
}

cd $build_dir