source [file normalize "./cpu/scripts/header.tcl"]

foreach file $rtl_files {
	read_verilog -sv "${rtl_dir}/${file}"
}

read_xdc "${constraints_dir}/nexys.xdc"

open_hw_manager
connect_hw_server
current_hw_target
open_hw_target
set_property PROGRAM.FILE "${build_dir}/bitstream.bit" [current_hw_device]
program_hw_devices [current_hw_device]