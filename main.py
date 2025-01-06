import sys

sys.path.append(".")

from asm import asm, link
from debugger import debugger
from lang import compiler

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