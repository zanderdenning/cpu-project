module edge_detector_pos(
	input logic clk,
	input logic in,
	output logic out
);

	logic last_value;

	assign out = ~last_value & in;

	always_ff @(posedge clk) begin
		last_value <= in;
	end

endmodule