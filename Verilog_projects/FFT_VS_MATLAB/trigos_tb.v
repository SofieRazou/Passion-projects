`timescale 1ns/1ps

module trigos_tb;

    reg clk;
    reg rst;
    reg [31:0] angle_in;
    wire [31:0] cos_out;
    wire [31:0] sin_out;

    // Instantiate the CORDIC module
    cordic_cos uut (
        .clk(clk),
        .rst(rst),
        .angle_in(angle_in),
        .cos_out(cos_out),
        .sin_out(sin_out)
    );

    // Clock generation: 10 ns period
    initial clk = 0;
    always #5 clk = ~clk;

    // Test stimulus
    initial begin
        // Initialize
        rst = 1;
        angle_in = 0;
        #20;
        rst = 0;

        // Test angles in Q1.31 format
        // 0 rad
        angle_in = 32'd0;
        #200;

        // pi/4 rad ~ 0.785398 in Q1.31
        angle_in = 32'd67108864; // approximate 2^31 * 0.785398 / pi
        #200;

        // pi/2 rad ~ 1.5708
        angle_in = 32'd134217728; 
        #200;

        // pi rad ~ 3.14159
        angle_in = 32'd268435456;
        #200;

        // 3*pi/2 rad ~ 4.71239
        angle_in = 32'd402653184;
        #200;

        // End simulation
        $finish;
    end

    // VCD dump
    initial begin
        $dumpfile("trigos_tb.vcd");
        $dumpvars(0, trigos_tb.uut);
    end

endmodule
