`timescale 1ns/1ps

module fifo #(parameter DATA_WIDTH=8, parameter DEPTH=128)(
    input clk,
    input rst_n,
    input wr_en,
    input rd_en,
    input [DATA_WIDTH-1:0] din,
    output reg [DATA_WIDTH-1:0] dout,
    output full,
    output empty
);
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    reg [$clog2(DEPTH)-1:0] wr_ptr = 0;
    reg [$clog2(DEPTH)-1:0] rd_ptr = 0;
    reg [$clog2(DEPTH+1)-1:0] count = 0;

    assign full = (count == DEPTH);
    assign empty = (count == 0);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0; rd_ptr <= 0; count <= 0; dout <= 0;
        end else begin
            if (wr_en && !full) begin
                mem[wr_ptr] <= din;
                wr_ptr <= (wr_ptr + 1) % DEPTH;
                count <= count + 1;
            end
            if (rd_en && !empty) begin
                dout <= mem[rd_ptr];
                rd_ptr <= (rd_ptr + 1) % DEPTH;
                count <= count - 1;
            end
        end
    end
endmodule

module conv2d_3x3_fifo_full #(
    parameter IMG_W = 128,
    parameter PIXEL_BITS = 8,
    parameter K00=1, K01=0, K02=-1,
    parameter K10=2, K11=0, K12=-2,
    parameter K20=1, K21=0, K22=-1
)(
    input clk,
    input rst_n,
    input [PIXEL_BITS-1:0] pixel_in,
    input pixel_valid,
    output reg [PIXEL_BITS-1:0] out_pixel,
    output reg out_valid
);
    wire [PIXEL_BITS-1:0] fifo_out1, fifo_out2;

    fifo #(PIXEL_BITS, IMG_W) linebuf1 (
        .clk(clk), .rst_n(rst_n),
        .wr_en(pixel_valid), .rd_en(pixel_valid),
        .din(pixel_in), .dout(fifo_out1),
        .full(), .empty()
    );

    fifo #(PIXEL_BITS, IMG_W) linebuf2 (
        .clk(clk), .rst_n(rst_n),
        .wr_en(pixel_valid), .rd_en(pixel_valid),
        .din(fifo_out1), .dout(fifo_out2),
        .full(), .empty()
    );

    reg [PIXEL_BITS-1:0] w00, w01, w02;
    reg [PIXEL_BITS-1:0] w10, w11, w12;
    reg [PIXEL_BITS-1:0] w20, w21, w22;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            w00<=0; w01<=0; w02<=0;
            w10<=0; w11<=0; w12<=0;
            w20<=0; w21<=0; w22<=0;
            out_pixel<=0; out_valid<=0;
        end else if (pixel_valid) begin
            w00<=w01; w01<=w02; w02<=fifo_out2;
            w10<=w11; w11<=w12; w12<=fifo_out1;
            w20<=w21; w21<=w22; w22<=pixel_in;

            out_pixel <= (w00*K00 + w01*K01 + w02*K02
                        + w10*K10 + w11*K11 + w12*K12
                        + w20*K20 + w21*K21 + w22*K22) >>> 4;
            out_valid <= 1;
        end else begin
            out_valid <= 0;
        end
    end
endmodule
