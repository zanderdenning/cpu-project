source [file normalize "./cpu/scripts/header.tcl"]

generate_target {synthesis} [get_ips]

foreach file $rtl_files {
	read_verilog -sv "${rtl_dir}/${file}"
}

read_xdc "${constraints_dir}/nexys.xdc"

# Syn
synth_design -top "top" -part ${fpga_part}

# PAR
opt_design
place_design
route_design

# Write
write_bitstream -force "${build_dir}/bitstream.bit"