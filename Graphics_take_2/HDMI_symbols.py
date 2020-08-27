#!/usr/bin/env python3

# rewrite of `minimal_HDMI_symbols.vhd` in nmigen

# https://nmigen.info/nmigen/latest/lang.html <- lang reference
# nmigen on freenode - help

#notes:
#    `all you need to do is, in your nmigen script, from nmigen_boards.arty_z7 include ArtyZ7Platform`
#    `then instantiate it with platform = ArtyZ7Platform(top_module)
#     and build it with platform.build()
from nmigen.back import verilog
from nmigen import *

def TMDS_encode(data: int, inverted: bool = False):
    # does not perform the last flipping step.
    if data > 239:
        data=239
    if data < 16:
        data=16

    ones = 0
    for i in bin(data)[2:]:
        ones += int(i)

    use_xnor = (ones > 4) or (ones == 4 and data&1 == 0)

    result = [data&1] + [0]*8
    data = [(data>>i)&1 for i in range(8)]
    for i in range(1,8):
        if use_xnor:
            result[i] = 1^data[i]^result[i-1]
        else:
            result[i] = data[i] ^ result[i-1]
    result[8] = int(not use_xnor)
    if not inverted :
        result = [0]+result[::-1]
    else:
        result = [1] + [result[8]] + [[1,0][i] for i in result[0:8]][::-1]
    result = ''.join([str(i) for i in result[::-1]])[::-1]
    return int(result,base=2)

def TMDS3(pixel,m):
    """
    this would assume `pixel` is a Signal(24), encoding a bgr color.
    returns the encoded pixel as a flat Signal(30), encoding each 8bit channel.

    need m for intermediate signals to avoid bugs with array
    """
    TMDS_LUT_a = [0]*256
    for i in range(256): # generate LUT for TMDS signals
        TMDS_LUT_a[i] = C(TMDS_encode(i), unsigned(10))

    TMDS_LUT = Array(TMDS_LUT_a)
#    TMDS_LUT = Array(map(lambda x: C(TMDS_encode(i),unsigned(10)) , range(256)))

    c0 = Signal(10)
    c1 = Signal(10)
    c2 = Signal(10)

    m.d.comb += [
        c0.eq(TMDS_LUT[pixel[:8]]),
        c1.eq(TMDS_LUT[pixel[8:16]]),
        c2.eq(TMDS_LUT[pixel[16:]]),
    ]

    encoded_pixel = Cat(c0,c1,c2)

    # encoded_pixel = Cat([TMDS_LUT[pixel[:8]],
    #                      TMDS_LUT[pixel[8:16]],
    #                      TMDS_LUT[pixel[16:]]])

    return encoded_pixel

class minimal_hdmi_symbols(Elaboratable):
    def __init__(self, hsync_invert:bool=False, vsync_invert:bool=False):
        """
        vga -> hdmi converter.
        inputs and generics:
        [hv]sync_invert are for inverting the sync signals compared to the VGA side as some modes require that.
            if True, sync=1 would be considered as active sync.
        red,blue,green are raw VGA colors. this module only works with 8 bits per channel.
        blank : 1 when screen is blank, 0 when video data is active
        outputs:
        c0,c1,c2- gbr respectively, HDMI encoded.
        """
        # inputs
        self.hsync = Signal()
        self.vsync = Signal()
        self.blank = Signal()
        self.red   = Signal(unsigned(8))
        self.green = Signal(unsigned(8))
        self.blue  = Signal(unsigned(8))
        self.hsync_invert = hsync_invert
        self.vsync_invert = vsync_invert
        # outputs
        self.c0    = Signal(unsigned(10))
        self.c1    = Signal(unsigned(10))
        self.c2    = Signal(unsigned(10))
    def elaborate(self,platform):
        # internal signals
        m = Module()

        processed_hsync = Signal()
        processed_vsync = Signal()
        
        m.d.comb += [ # invert when need be
            processed_hsync.eq(self.hsync if not self.hsync_invert else ~self.hsync),
            processed_vsync.eq(self.vsync if not self.vsync_invert else ~self.vsync)
        ]

        symbol_queue = Array([Signal(5,reset_less=True) for _ in range(11)])
        symbols = Signal(30,reset_less=True)
        last_blank = Signal(reset=1) # last was not blank or sync
        last_vsync = Signal(reset=1)
        last_hsync = Signal(reset=1)

        data_island_armed = Signal(reset=0)
        data_island_index = Signal(unsigned(6),reset=0b11111)

        color_queue = Array([Signal(24, reset_less=True) for _ in range(len(symbol_queue))])
          # the idea is I apply TMDS between last 2 layers - so between layer 1 and 0

        current_symbol = Signal(unsigned(5),reset_less=True)
        current_color  = Signal(30,reset_less=True)


        clocks_since_last_vsync = Signal(unsigned(32)) # debug
        clocks_since_last_hsync = Signal(unsigned(32))
        clocks_since_last_blank = Signal(unsigned(32))

        # code
        m.d.comb += [
            self.c0.eq(symbols[20:30]),
            self.c1.eq(symbols[10:20]),
            self.c2.eq(symbols[ 0:10]),

            current_symbol.eq(symbol_queue[0]),
            current_color.eq(color_queue[0])
        ]


        hdmi_control_symbols_d = {
        #--------------------------------------------------------------
        #- TMDS encoded colours. 1 to 7 are reserved.
        #--------------------------------------------------------------
            0b00000 : 0b0111110000_0111110000_0111110000,  #- RGB
            0b00001 : 0b0111110000_0111110000_1011110000,  #- RGB
            0b00010 : 0b0111110000_1011110000_0111110000,  #- RGB
            0b00011 : 0b0111110000_1011110000_1011110000,  #- RGB
            0b00100 : 0b1011110000_0111110000_0111110000,  #- RGB
            0b00101 : 0b1011110000_0111110000_1011110000,  #- RGB
            0b00110 : 0b1011110000_1011110000_0111110000,  #- RGB
            0b00111 : 0b1011110000_1011110000_1011110000,  #- RGB
        #--------------------------------------------------------------
        #- control symbols from 5.4.2 # part of the DVI-D standard
        #--------------------------------------------------------------
            0b01000 : 0b1101010100_1101010100_1101010100,  #- CTL periods
            0b01001 : 0b0010101011_1101010100_1101010100,  #- Hsync
            0b01010 : 0b0101010100_1101010100_1101010100,  #- vSync
            0b01011 : 0b1010101011_1101010100_1101010100,  #- vSync+hSync
        #--------------------------------------------------------------
        #- Symbols to signal the start of a HDMI feature
        #--------------------------------------------------------------
            0b01100 : 0b0101010100_0010101011_0010101011,  #- DataIslandPeamble, with VSYNC # 5.2.1.1
            0b01101 : 0b0101100011_0100110011_0100110011,  #- DataIslandGuardBand, with VSYNC # 5.2.3.3
            0b01110 : 0b1101010100_0010101011_1101010100,  #- VideoPramble 5.2.1.1
            0b01111 : 0b1011001100_0100110011_1011001100,  #- VideoGuardBand 5.2.2.1

        #--------------------------------------------------------------
        #- From TERC4 codes in 5.4.3, and data data layout from 5.2.3.1
        #-
        #- First nibble  is used for the nFirstWordOfPacket (MSB) Header Bit, VSYNC, HSYNC (LSB).
        #- The packet is sent where VSYNC = '1' and HSYNC = '0', so we are left with 4 options
        #- Second nibble is used for the odd bits the four data sub-packets
        #- Third nibble  is used for the even bits the four data sub-packets
        #-
        #- These can be used to contruct a data island with any header
        #- and any data in subpacket 0, but all other subpackets
        #- must be 0s.
        #--------------------------------------------------------------
            0b10000 : 0b1011100100_1010011100_1010011100,  #- 0010 0000 0000, TERC4 coded
            0b10001 : 0b1011100100_1010011100_1001100011,  #- 0010 0000 0001, TERC4 coded
            0b10010 : 0b1011100100_1001100011_1010011100,  #- 0010 0000 0000, TERC4 coded
            0b10011 : 0b1011100100_1001100011_1001100011,  #- 0010 0001 0001, TERC4 coded
            0b10100 : 0b0110001110_1010011100_1010011100,  #- 0110 0000 0000, TERC4 coded
            0b10101 : 0b0110001110_1010011100_1001100011,  #- 0110 0000 0001, TERC4 coded
            0b10110 : 0b0110001110_1001100011_1010011100,  #- 0110 0001 0000, TERC4 coded
            0b10111 : 0b0110001110_1001100011_1001100011,  #- 0110 0001 0001, TERC4 coded
            0b11000 : 0b0110011100_1010011100_1010011100,  #- 1010 0000 0000, TERC4 coded
            0b11001 : 0b0110011100_1010011100_1001100011,  #- 1010 0000 0001, TERC4 coded
            0b11010 : 0b0110011100_1001100011_1010011100,  #- 1010 0001 0000, TERC4 coded
            0b11011 : 0b0110011100_1001100011_1001100011,  #- 1010 0001 0001, TERC4 coded
            0b11100 : 0b0101100011_1010011100_1010011100,  #- 1110 0000 0000, TERC4 coded
            0b11101 : 0b0101100011_1010011100_1001100011,  #- 1110 0000 0001, TERC4 coded
            0b11110 : 0b0101100011_1001100011_1010011100,  #- 1110 0001 0000, TERC4 coded
            0b11111 : 0b0101100011_1001100011_1001100011,  #- 1110 0001 0001, TERC4 coded
        }
        hdmi_control_symbols = Memory(width=30, depth=32,
                                      init=[hdmi_control_symbols_d[i] for i in range(32)])

        m.submodules.rdport_hdmi_ctrl_syms = rdport = hdmi_control_symbols.read_port()
        m.d.comb += rdport.addr.eq(current_symbol)


        m.d.sync += symbols.eq(rdport.data)

        # m.d.sync += Cat(color_queue).eq(Cat(color_queue[1:],self.red,self.green,self.blue))
        color_queue_next = Cat(color_queue[1:],self.red,self.green,self.blue)
        m.d.sync += Cat(*color_queue).eq(color_queue_next)
        assert (len (color_queue_next) == len(Cat(*color_queue)))

 #       with m.If(current_symbol < 8): ### THIS FUCKS UP THE THING. REMOVE TO TEST OR W/E
#            m.d.sync += symbols.eq(TMDS3(current_color,m))

        with m.If(self.blank == 0):
            # Are we being asked to send video data? If so we need to send a peramble
            r,g,b = self.red[1], self.green[1], self.blue[1]
            with m.If(last_blank):

                m.d.sync += [
                    symbol_queue[10].eq(Cat(r,g,b, C(0,2))), # bgr
                    symbol_queue[9]. eq(0b01111), # Video Guard Band
                    symbol_queue[8]. eq(0b01111),
                    symbol_queue[7]. eq(0b01110), # Video Preamble
                    symbol_queue[6]. eq(0b01110),
                    symbol_queue[5]. eq(0b01110),
                    symbol_queue[4]. eq(0b01110),
                    symbol_queue[3]. eq(0b01110),
                    symbol_queue[2]. eq(0b01110),
                    symbol_queue[1]. eq(0b01110),
                    symbol_queue[0]. eq(0b01110)
                ]
            with m.Else():
                m.d.sync += [
                    Cat(*symbol_queue).eq(Cat(symbol_queue[1:],
                                              Cat(r,g,b, C(0,2)))) #bgr
                ]
        with m.Else():
                    # Either end the data packet or just send
                    # the syncs using CTL frames
            data_island_control_symbols_l = [                # the switch case thing
                0b01100, 0b01100, 0b01100, 0b01100, 0b01100, 0b01100, 0b01100, 0b01100, # Data island preamble
                0b01101, 0b01101, # Data island Guard Band
                #-----------------------
                # For a NULL Data Island
                #-----------------------
                0b10000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, # Data Island ( 0- 7)
                0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, # Data Island ( 8-15)
                0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, # Data Island (16-23)
                0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, 0b11000, # Data Island (24-31)
                # Trailing guard band
                0b01101, 0b01101,  # Data island Guard Band
                # There has to be four CTL symbols before the next block of video our data,
                # But that won't be a problem for us, we will have the rest of the vertical
                # Blanking interval
            ]
            data_island_control_symbols_l += [0b010 <<2 | (self.vsync_invert <<1) | (not self.hsync_invert)] * \
                (64-len(data_island_control_symbols_l))###
                # we know that all 64 symbols fit within the hblank, so V&H = 1_0
            assert(len(data_island_control_symbols_l)==64) # just to see if its true

            data_island_control_symbols = Memory(width=5, depth=64,
                                                 init=data_island_control_symbols_l)

            m.submodules.rdport_data_island = rdport = data_island_control_symbols.read_port()
            m.d.comb += rdport.addr.eq(data_island_index)

            m.d.sync += Cat(*symbol_queue).eq(Cat(*symbol_queue[1:]))
            with m.If(data_island_index == 0b111111): # if packet is finished, send hsync, vsync.
                m.d.sync += symbol_queue[-1].eq(Cat(processed_hsync, processed_vsync, C(0b010,3)))
            with m.Else(): # when in the packet, send the data according to the packet stuff.
#                self.dat_r.eq(rdport.data)
                m.d.sync += symbol_queue[-1].eq(rdport.data)
            #end case;


        # end if;
        with m.If(data_island_index != 0b111111):
            m.d.sync += data_island_index.eq(data_island_index+1)

        # If we see the rising edge of vsync we need to send
        # a data island the next time we see the hsync signal
        # drop.
        with m.If((last_vsync == 0) & self.vsync ):
            m.d.sync += data_island_armed.eq(1)

        with m.If(data_island_armed & last_hsync & (self.hsync==0) ): # if armed and hsync starts
            m.d.sync += [
                data_island_index.eq(0),
                data_island_armed.eq(0)
            ]

        m.d.sync += [
            last_blank.eq(self.blank),
            last_hsync.eq(self.hsync),
            last_vsync.eq(self.vsync)
        ]
        m.d.sync += [ # [vh]sync is active low
            # this is one clock late
            clocks_since_last_vsync.eq(Mux((self.vsync==C(1)) & (last_vsync==C(0,1)), 0, 1+clocks_since_last_vsync)),
            clocks_since_last_hsync.eq(Mux((self.hsync==C(1)) & (last_hsync==C(0,1)), 0, 1+clocks_since_last_hsync)),
            clocks_since_last_blank.eq(Mux((self.blank==C(1)) & (last_blank==C(0,1)), 0, 1+clocks_since_last_blank)),            
        ]

        return m






if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "--test":

        pass

    top = minimal_hdmi_symbols(hsync_invert=True, vsync_invert=True)
    with open("minimal_hdmi_symbols.v", "w") as f:
        f.write(verilog.convert(top, name = "minimal_hdmi_symbols", ports=[
            #inputs
            top.hsync, top.vsync, top.blank, top.red, top.green, top.blue,
            # outputs
            top.c0, top.c1, top.c2]
        ))
