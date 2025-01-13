`timescale 1ns / 1ps

`include "constants.svh"

import types::*;

module top(
	input logic clk, rst,
	input mem_resp_interface tb_mem_resp,
	output mem_req_interface tb_mem_req
);

	logic [31:0] pc;

	assign tb_mem_req.addr = pc[`PHYS_MEM_BITS-1+2:2];
	assign tb_mem_req.write_data = 32'bX;
	assign tb_mem_req.wen = 4'b0000;
	assign tb_mem_req.ren = 1'b1;
	assign tb_mem_req.resp_ready = 1'b1;

	always_ff @(posedge clk) begin
		if (rst) begin
			pc <= 32'h50;
		end
		else begin
			pc <= pc + 4;
		end
	end

endmodule