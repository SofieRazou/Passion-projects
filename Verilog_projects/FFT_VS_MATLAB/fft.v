`timescale 1ns/1ps

module fft #(
    parameter WIDTH = 32,
    parameter N     = 8,
    parameter LOG2N = 3,
    parameter ITER  = 16  // CORDIC iterations
)(
    input  wire                  clk,
    input  wire                  rst,
    input  wire signed [WIDTH-1:0] x_r [0:N-1],
    input  wire signed [WIDTH-1:0] x_i [0:N-1],
    output reg  signed [WIDTH-1:0] X_r [0:N-1],
    output reg  signed [WIDTH-1:0] X_i [0:N-1]
);

    // Internal registers
    integer i, s, k, j;
    reg signed [WIDTH-1:0] u_r, u_i;
    reg signed [WIDTH-1:0] t_r, t_i;

    // Twiddle angle in Q1.31
    reg [31:0] angle_q31;

    // Sequential control
    reg [LOG2N:0] stage;
    reg [31:0] step;

    // CORDIC outputs
    reg start_cordic;
    wire [WIDTH-1:0] cos_val;
    wire [WIDTH-1:0] sin_val;
    wire busy;

    cordic_cos #(
        .WIDTH(WIDTH),
        .ITER(ITER)
    ) cordic_inst (
        .clk(clk),
        .rst(rst),
        .angle_in(angle_q31),
        .cos_out(cos_val),
        .sin_out(sin_val)
    );

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            stage <= 0;
            step  <= 0;
            start_cordic <= 0;

            for (i = 0; i < N; i = i + 1) begin
                X_r[i] <= x_r[i];
                X_i[i] <= x_i[i];
            end
        end else begin
            // Sequential FFT computation
            for (s = 1; s <= LOG2N; s = s + 1) begin
                integer m = 1 << s;

                for (k = 0; k < N; k = k + m) begin
                    for (j = 0; j < m/2; j = j + 1) begin
                        // Compute twiddle angle θ = -2π j / m in Q1.31
                        angle_q31 <= (32'sd2147483647 * (-2 * 3_14159265 * j / m));

                        // Wait for CORDIC to finish
                        if (!busy) begin
                            u_r = X_r[k + j];
                            u_i = X_i[k + j];

                            t_r = (cos_val * X_r[k + j + m/2] - sin_val * X_i[k + j + m/2]) >>> 31;
                            t_i = (cos_val * X_i[k + j + m/2] + sin_val * X_r[k + j + m/2]) >>> 31;

                            // Update butterfly
                            X_r[k + j]       <= u_r + t_r;
                            X_i[k + j]       <= u_i + t_i;
                            X_r[k + j + m/2] <= u_r - t_r;
                            X_i[k + j + m/2] <= u_i - t_i;
                        end
                    end
                end
            end
        end
    end

endmodule
