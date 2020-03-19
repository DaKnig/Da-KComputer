;;// This buffer is for text that is not saved, and for Lisp evaluation.
;;// To create a file, visit it with C-o and enter text in its buffer.

module tmds_encoder(
    input wire PIXEL_CLK,
    input wire RESET,
    input wire ACTIVE,
    input wire HSYNC,
    input wire VSYNC,
    input wire [7:0] DATA,
    output wire [9:0] TMDS_DATA
);

`define SIGNAL_C00 10'b1101010100
`define SIGNAL_C01 10'b0010101011
`define SIGNAL_C10 10'b0101010100
`define SIGNAL_C11 10'b1010101011

wire [3:0] ones_count_s1;
wire use_xnor_s1;
wire [8:0] data_s2;
wire invert_output_s3;
wire add_two_s3;
wire needs_rebalance_s3;
wire negative_rebalance_s3;
wire [4:0] diff_s3;

reg [4:0] disparity;
reg [7:0] data_s2r;
reg [3:0] ones_count_s2r;
reg use_xnor_s2r;
reg active_s2r;
reg vsync_s2r;
reg hsync_s2r;
reg [8:0] data_s3r;
reg [3:0] ones_count_s3r;
reg [3:0] diff_s3r;
reg active_s3r;
reg vsync_s3r;
reg hsync_s3r;
reg [9:0] output_data;

assign ones_count_s1 = ((DATA[0] + DATA[1]) + (DATA[2] + DATA[3])) + ((DATA[4] + DATA[5]) + (DATA[6] + DATA[7]));
assign use_xnor_s1 = (ones_count_s1 > 4) || (ones_count_s1 == 4 && DATA[0] == 0);
assign data_s2[0] = data_s2r[0];
assign data_s2[1] = use_xnor_s2r ? (data_s2r[0] ~^ data_s2r[1]) : (data_s2r[0] ^ data_s2r[1]);
assign data_s2[2] = use_xnor_s2r ? (data_s2[1] ~^ data_s2r[2]) : (data_s2[1] ^ data_s2r[2]);
assign data_s2[3] = use_xnor_s2r ? (data_s2[2] ~^ data_s2r[3]) : (data_s2[2] ^ data_s2r[3]);
assign data_s2[4] = use_xnor_s2r ? (data_s2[3] ~^ data_s2r[4]) : (data_s2[3] ^ data_s2r[4]);
assign data_s2[5] = use_xnor_s2r ? (data_s2[4] ~^ data_s2r[5]) : (data_s2[4] ^ data_s2r[5]);
assign data_s2[6] = use_xnor_s2r ? (data_s2[5] ~^ data_s2r[6]) : (data_s2[5] ^ data_s2r[6]);
assign data_s2[7] = use_xnor_s2r ? (data_s2[6] ~^ data_s2r[7]) : (data_s2[6] ^ data_s2r[7]);
assign data_s2[8] = ~use_xnor_s2r;
assign needs_rebalance_s3 = (disparity == 0) || (ones_count_s3r == 4);
assign negative_rebalance_s3 = disparity[4] ^ (ones_count_s3r > 4);
assign invert_output_s3 = (~data_s3r[8] && needs_rebalance_s3) || (negative_rebalance_s3 && ~needs_rebalance_s3);
assign add_two_s3 = data_s3r[8] ^ negative_rebalance_s3;
assign diff_s3 = add_two_s3 ? ({1'b0, diff_s3r} - 5'd2) : {1'b0, diff_s3r};
assign TMDS_DATA = output_data;

always @ (posedge PIXEL_CLK) begin
    if (RESET == 1) begin
        disparity <= 0;
        data_s2r <= 0;
        use_xnor_s2r <= 0;
        ones_count_s2r <= 0;
        active_s2r <= 0;
        vsync_s2r <= 0;
        hsync_s2r <= 0;
        data_s3r <= 0;
        ones_count_s3r <= 0;
        diff_s3r <= 0;
        active_s3r <= 0;
        vsync_s3r <= 0;
        hsync_s3r <= 0;
    end else begin
        data_s2r <= DATA;
        use_xnor_s2r <= use_xnor_s1;
        ones_count_s2r <= ones_count_s1;
        active_s2r <= ACTIVE;
        vsync_s2r <= VSYNC;
        hsync_s2r <= HSYNC;
        data_s3r <= data_s2;
        ones_count_s3r <= ones_count_s2r;
        diff_s3r <= 4'd8 - ones_count_s2r;
        active_s3r <= active_s2r;
        vsync_s3r <= vsync_s2r;
        hsync_s3r <= hsync_s2r;
        if (active_s3r) begin
            disparity <= invert_output_s3 ? (disparity - diff_s3) : (disparity + diff_s3);
            output_data <= {invert_output_s3, data_s3r[8], invert_output_s3 ? (~data_s3r[7:0]) : data_s3r[7:0]};
        end else begin
            case ({vsync_s3r, hsync_s3r})
                2'b00: output_data <= `SIGNAL_C00;
                2'b01: output_data <= `SIGNAL_C01;
                2'b10: output_data <= `SIGNAL_C10;
                2'b11: output_data <= `SIGNAL_C11;
            endcase
        end
    end
end

endmodule

