set root_dir [file normalize "./cpu"]
set build_dir "${root_dir}/build"

open_hw_manager
connect_hw_server
current_hw_target
open_hw_target
set_property PROGRAM.FILE "${build_dir}/bitstream.bit" [current_hw_device]
program_hw_devices [current_hw_device]