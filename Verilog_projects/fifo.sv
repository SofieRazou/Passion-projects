module fifo(
    input clk,
    input rst,
    input wr_en,
    input rd_en,
    input [7:0] buf_in,
    output reg [7:0] buf_out,
    output reg buf_empty,
    output reg buf_full,
    output reg [5:0] fifo_counter
);

    reg [7:0] buf_mem [63:0]; // 64 x 8-bit memory
    reg [5:0] wr_ptr, rd_ptr;

    // Update empty/full flags combinationally
    always @(*) begin
        buf_empty = (fifo_counter == 0);
        buf_full  = (fifo_counter == 64);
    end

    // FIFO counter update
    always @(posedge clk or posedge rst) begin
        if (rst)
            fifo_counter <= 0;
        else begin
            case ({wr_en && !buf_full, rd_en && !buf_empty})
                2'b10: fifo_counter <= fifo_counter + 1; // write only
                2'b01: fifo_counter <= fifo_counter - 1; // read only
                2'b11: fifo_counter <= fifo_counter;     // read & write simultaneously
                default: fifo_counter <= fifo_counter;  // no operation
            endcase
        end
    end

    // Write pointer update
    always @(posedge clk or posedge rst) begin
        if (rst)
            wr_ptr <= 0;
        else if (wr_en && !buf_full)
            wr_ptr <= wr_ptr + 1;
    end

    // Read pointer update
    always @(posedge clk or posedge rst) begin
        if (rst)
            rd_ptr <= 0;
        else if (rd_en && !buf_empty)
            rd_ptr <= rd_ptr + 1;
    end

    // Write data to memory
    always @(posedge clk) begin
        if (wr_en && !buf_full)
            buf_mem[wr_ptr] <= buf_in;
    end

    // Read data from memory
    always @(posedge clk or posedge rst) begin
        if (rst)
            buf_out <= 0;
        else if (rd_en && !buf_empty)
            buf_out <= buf_mem[rd_ptr];
    end

endmodule
