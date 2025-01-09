set fpga_part "xc7a200tsbg484-1"

set root_dir [file normalize "./cpu"]
set build_dir "${root_dir}/build"
set rtl_dir "${root_dir}/rtl"
set rtl_lib_dir "${rtl_dir}/lib"
set constraints_dir "${root_dir}/constraints"

set_param general.maxThreads 8

# RTL Sources
read_verilog -sv "${rtl_dir}/top.sv"
read_verilog -sv "${rtl_lib_dir}/debouncer.sv"
read_verilog -sv "${rtl_lib_dir}/edge_detector_pos.sv"

# Constraints
read_xdc "${constraints_dir}/nexys.xdc"

# Syn
synth_design -top "top" -part ${fpga_part}

# PAR
opt_design
place_design
route_design

# Write
write_bitstream -force "${build_dir}/bitstream.bit"