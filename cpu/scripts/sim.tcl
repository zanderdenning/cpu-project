source [file normalize "./cpu/scripts/header.tcl"]

generate_target {simulation} [get_ips]

foreach file [glob "../build/ip/*/simulation/*.v"] {
	exec echo "${file}"
	exec xvlog "${file}"
}

foreach file [glob "../build/ip/*/sim/*.v"] {
	exec xvlog "${file}"
}

foreach file $rtl_files {
	exec xvlog -sv "${rtl_dir}/${file}" -i "${rtl_dir}"
}

exec xvlog -sv "${testbench_dir}/cpu_testbench.sv" -i "${rtl_dir}"

exec xelab -debug typical cpu_testbench
exec xsim cpu_testbench --tclbatch "${scripts_dir}/xsim_conf.tcl"