`timescale 1ns/1ps

module fft_tb;

    localparam WIDTH = 32;
    localparam N     = 8;
    localparam LOG2N = 3;

    reg clk;
    reg rst;

    // Input arrays
    reg signed [WIDTH-1:0] x_r [0:N-1];
    reg signed [WIDTH-1:0] x_i [0:N-1];

    // FFT output arrays
    wire signed [WIDTH-1:0] X_r [0:N-1];
    wire signed [WIDTH-1:0] X_i [0:N-1];

    integer i;

    // Flattened registers for VCD dumping
    reg signed [WIDTH-1:0] X_R_flat0, X_R_flat1, X_R_flat2, X_R_flat3,
                           X_R_flat4, X_R_flat5, X_R_flat6, X_R_flat7;

    reg signed [WIDTH-1:0] X_I_flat0, X_I_flat1, X_I_flat2, X_I_flat3,
                           X_I_flat4, X_I_flat5, X_I_flat6, X_I_flat7;

    // LUTs for test signal
    reg signed [WIDTH-1:0] cos_lut [0:N-1];
    reg signed [WIDTH-1:0] sin_lut [0:N-1];

    // Instantiate FFT
    fft #(
        .WIDTH(WIDTH),
        .N(N),
        .LOG2N(LOG2N)
    ) uut (
        .clk(clk),
        .rst(rst),
        .x_r(x_r),
        .x_i(x_i),
        .X_r(X_r),
        .X_i(X_i)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Assign flattened outputs for VCD
    always @(*) begin
        X_R_flat0 = X_r[0]; X_R_flat1 = X_r[1]; X_R_flat2 = X_r[2]; X_R_flat3 = X_r[3];
        X_R_flat4 = X_r[4]; X_R_flat5 = X_r[5]; X_R_flat6 = X_r[6]; X_R_flat7 = X_r[7];

        X_I_flat0 = X_i[0]; X_I_flat1 = X_i[1]; X_I_flat2 = X_i[2]; X_I_flat3 = X_i[3];
        X_I_flat4 = X_i[4]; X_I_flat5 = X_i[5]; X_I_flat6 = X_i[6]; X_I_flat7 = X_i[7];
    end

    // Initialize LUTs and inputs
    initial begin
        rst = 1;

        // Example: cos[n] + j*sin[n] test signal
        cos_lut[0] = 32'sd2147483647;  sin_lut[0] = 32'sd0;
        cos_lut[1] = 32'sd1518500249;  sin_lut[1] = 32'sd1518500249;
        cos_lut[2] = 32'sd0;           sin_lut[2] = 32'sd2147483647;
        cos_lut[3] = -32'sd1518500249; sin_lut[3] = 32'sd1518500249;
        cos_lut[4] = -32'sd2147483647; sin_lut[4] = 32'sd0;
        cos_lut[5] = -32'sd1518500249; sin_lut[5] = -32'sd1518500249;
        cos_lut[6] = 32'sd0;           sin_lut[6] = -32'sd2147483647;
        cos_lut[7] = 32'sd1518500249;  sin_lut[7] = -32'sd1518500249;

        for (i = 0; i < N; i = i + 1) begin
            x_r[i] = cos_lut[i];
            x_i[i] = sin_lut[i];
        end

        #20;
        rst = 0;

        // Wait enough cycles for sequential FFT + CORDIC
        #2000;

        // Display FFT output
        $display("FFT Output:");
        for (i = 0; i < N; i = i + 1) begin
            $display("X[%0d] = %0d + j%0d", i, X_r[i], X_i[i]);
        end

        #20;
        $finish;
    end

    // VCD dump
    initial begin
        $dumpfile("fft_tb.vcd");

        // Dump entire testbench
        $dumpvars(0, fft_tb);

        // Dump flattened FFT outputs
        $dumpvars(0, fft_tb.X_R_flat0);
        $dumpvars(0, fft_tb.X_R_flat1);
        $dumpvars(0, fft_tb.X_R_flat2);
        $dumpvars(0, fft_tb.X_R_flat3);
        $dumpvars(0, fft_tb.X_R_flat4);
        $dumpvars(0, fft_tb.X_R_flat5);
        $dumpvars(0, fft_tb.X_R_flat6);
        $dumpvars(0, fft_tb.X_R_flat7);

        $dumpvars(0, fft_tb.X_I_flat0);
        $dumpvars(0, fft_tb.X_I_flat1);
        $dumpvars(0, fft_tb.X_I_flat2);
        $dumpvars(0, fft_tb.X_I_flat3);
        $dumpvars(0, fft_tb.X_I_flat4);
        $dumpvars(0, fft_tb.X_I_flat5);
        $dumpvars(0, fft_tb.X_I_flat6);
        $dumpvars(0, fft_tb.X_I_flat7);
    end

endmodule
