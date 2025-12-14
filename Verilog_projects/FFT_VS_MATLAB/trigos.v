`timescale 1ns/1ps

// Simple LUT for arctangent values (Q1.31 fixed point)
module lut_arctan(
    input  wire [4:0] idx,       // 0..31
    output reg  [31:0] atan_val
);
    always @(*) begin
        case(idx)
            5'd0:  atan_val = 32'h3243F6A9; // atan(2^-0) ≈ 45 deg
            5'd1:  atan_val = 32'h1DAC6705; // atan(2^-1)
            5'd2:  atan_val = 32'h0FADBAFC; // atan(2^-2)
            5'd3:  atan_val = 32'h07F56EA6;
            5'd4:  atan_val = 32'h03FEAB76;
            5'd5:  atan_val = 32'h01FFD55B;
            5'd6:  atan_val = 32'h00FFFABA;
            5'd7:  atan_val = 32'h007FFFD5;
            5'd8:  atan_val = 32'h003FFFFF;
            5'd9:  atan_val = 32'h001FFFFF;
            5'd10: atan_val = 32'h000FFFFF;
            5'd11: atan_val = 32'h0007FFFF;
            5'd12: atan_val = 32'h0003FFFF;
            5'd13: atan_val = 32'h0001FFFF;
            5'd14: atan_val = 32'h0000FFFF;
            5'd15: atan_val = 32'h00007FFF;
            default: atan_val = 32'h0;
        endcase
    end
endmodule


// Iterative CORDIC for cos and sin
module cordic_cos #(
    parameter WIDTH = 32,
    parameter ITER  = 16       // Number of iterations
)(
    input  wire                 clk,
    input  wire                 rst,
    input  wire [WIDTH-1:0]     angle_in,  // Q1.31 fixed-point
    output reg  [WIDTH-1:0]     cos_out,   // Q1.31
    output reg  [WIDTH-1:0]     sin_out    // Q1.31
);

    // Scaling factor K ≈ 0.607252 (Q1.31)
    localparam [WIDTH-1:0] K = 32'h4DBA76D0;

    // Iteration registers
    reg [WIDTH-1:0] x, y, z;
    reg [4:0] i;
    reg busy;

    wire [WIDTH-1:0] atan_val;
    lut_arctan arctan_lookup(.idx(i[4:0]), .atan_val(atan_val));

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            x       <= 0;
            y       <= 0;
            z       <= 0;
            i       <= 0;
            busy    <= 0;
            cos_out <= 0;
            sin_out <= 0;
        end else begin
            if (!busy) begin
                // Initialize vector
                x    <= K;
                y    <= 0;
                z    <= angle_in;
                i    <= 0;
                busy <= 1;
            end else if (i < ITER) begin
                // Rotation
                if (z[WIDTH-1] == 0) begin // z >= 0
                    x <= x - (y >>> i);
                    y <= y + (x >>> i);
                    z <= z - atan_val;
                end else begin
                    x <= x + (y >>> i);
                    y <= y - (x >>> i);
                    z <= z + atan_val;
                end
                i <= i + 1;
            end else begin
                // Done
                cos_out <= x;
                sin_out <= y;
                busy <= 0;
            end
        end
    end

endmodule
