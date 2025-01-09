`timescale 1ns / 1ps

module top(
	input logic clk,
	input logic btnr, btnl,
	output logic [7:0] led
);

	logic [7:0] current_count;
	logic btnr_debounced, btnl_debounced;
	logic btnr_just_pressed, btnl_just_pressed;

	debouncer #(.TIME(10000), .CLOCK_PERIOD(10)) btnr_debouncer(.clk(clk), .in(btnr), .out(btnr_debounced));
	debouncer #(.TIME(10000), .CLOCK_PERIOD(10)) btnl_debouncer(.clk(clk), .in(btnl), .out(btnl_debounced));

	edge_detector_pos btnr_edge_detector(.clk(clk), .in(btnr_debounced), .out(btnr_just_pressed));
	edge_detector_pos btnl_edge_detector(.clk(clk), .in(btnl_debounced), .out(btnl_just_pressed));

	assign led = current_count;
	
	always_ff @(posedge clk) begin
		if (btnr_just_pressed) begin
			current_count <= current_count + 1;
		end
		else if (btnl_just_pressed) begin
			current_count <= current_count - 1;
		end
	end
	
endmodule