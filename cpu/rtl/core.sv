`timescale 1ns / 1ps

`include "constants.svh"

import types::*;

module core(
	input logic clk, rst,

	output logic [`PHYS_MEM_BITS-1:0] imem_req_addr,
	input logic imem_req_ready,
	output logic imem_req_valid,

	input logic [127:0] imem_resp_data,
	output logic imem_resp_ready,
	input logic imem_resp_valid
);

	// PC Gen

	logic [31:0] pc_i;
	logic stall_i;

	always_ff @(posedge clk) begin
		if (rst) begin
			pc_i <= 32'hC0;
		end
		else begin
			if (~stall_i) begin
				pc_i <= pc_i + 4;
			end
		end
	end

	// Instruction Fetch

	logic [31:0] pc_d;
	logic [31:0] inst_d;
	logic icache_ready;
	logic icache_valid;

	logic [31:0] imem_req_addr_virt;
	assign imem_req_addr = imem_req_addr_virt[`PHYS_MEM_BITS+3:4];
	assign stall_i = ~icache_ready;

	icache icache(
		.clk(clk), .rst(rst),
		
		.req_addr(pc_i),
		.req_ready(icache_ready),
		.req_valid(1'b1),

		.resp_data(inst_d),
		.resp_ready(1'b1),
		.resp_valid(icache_valid),

		.ext_mem_req_addr(imem_req_addr_virt),
		.ext_mem_req_ready(imem_req_ready),
		.ext_mem_req_valid(imem_req_valid),

		.ext_mem_resp_data(imem_resp_data),
		.ext_mem_resp_ready(imem_resp_ready),
		.ext_mem_resp_valid(imem_resp_valid)
	);

	always_ff @(posedge clk) begin
		if (rst) begin
			pc_d <= 32'b0;
		end
		else begin
			pc_d <= pc_i;
		end
	end

endmodule