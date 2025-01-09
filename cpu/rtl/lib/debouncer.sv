module debouncer #(parameter TIME=10000, CLOCK_PERIOD=10) (
	input logic clk,
	input logic in,
	output logic out
);

	parameter CYCLES = TIME / CLOCK_PERIOD;

	logic [$clog2(CYCLES)-1:0] current_count = 0;

	assign out = current_count == CYCLES;

	always_ff @(posedge clk) begin
		if (in) begin
			if (current_count != CYCLES) begin
				current_count <= current_count + 1;
			end
		end
		else begin
			current_count <= 0;
		end
	end

endmodule