`timescale 1ns / 1ps

`include "constants.svh"

package types;

	typedef struct packed {
		logic [`PHYS_MEM_BITS-1:0] addr;
		logic [31:0] write_data;
		logic [3:0] wen;
		logic ren;
		logic resp_ready;
	} mem_req_interface;

	typedef struct packed {
		logic [31:0] read_data;
		logic resp_valid;
		logic req_ready;
	} mem_resp_interface;

endpackage