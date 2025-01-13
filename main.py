import sys
import os

sys.path.append(".")

from asm import asm, asm_to_hex, link
from debugger import debugger
from lang import compiler

def vivado_script(script: str):
	os.system(f"vivado -mode batch -source cpu/scripts/{script}.tcl -log cpu/build/log/vivado.log -journal cpu/build/log/vivado.jou")

if __name__ == "__main__":
	command = sys.argv[1]
	if command == "debug":
		debugger.run_debugger()
	elif command == "asm":
		in_file = sys.argv[2]
		out_file = sys.argv[3]
		asm.Assembler().assemble_file(in_file, out_file)
	elif command == "link":
		in_files = sys.argv[2:-1]
		out_file = sys.argv[-1]
		link.Linker().link_files(in_files, out_file)
	elif command == "compile":
		in_file = sys.argv[2]
		out_file = sys.argv[3]
		compiler.Compiler().compile(in_file, out_file)
	elif command == "asm_to_hex":
		in_file = sys.argv[2]
		out_file = sys.argv[3]
		asm_to_hex.asm_to_hex(in_file, out_file)
	elif command == "cpu_build":
		vivado_script("build")
	elif command == "cpu_program":
		vivado_script("program")
	elif command == "cpu_sim":
		vivado_script("sim")
	elif command == "cpu_ip_gen":
		vivado_script(f"ip/generate_{sys.argv[2]}")
	elif command == "cpu_waveform":
		os.system("gtkwave ./cpu/build/dump.vcd")