source [file normalize "./cpu/scripts/header.tcl"]

foreach file $rtl_files {
	exec xvlog -sv "${rtl_dir}/${file}"
}

exec xvlog -sv "${testbench_dir}/cpu_testbench.sv"

exec xelab -debug typical cpu_testbench
exec xsim cpu_testbench --tclbatch "${scripts_dir}/xsim_conf.tcl"