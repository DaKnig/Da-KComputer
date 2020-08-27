#!/usr/bin/env python3
"""note - this is a rewrite"""

"""
idea - basically queue all the inputs , use state machine for knowing what
 to do next.
"""

from nmigen.back import verilog
from nmigen.asserts import Assert
from nmigen import *

class VGA_to_HDMI(Elaboratable): # different name- minimal_hdmi_symbols
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
    def __init__(self, hsync_invert:bool=False, vsync_invert:bool=False):
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

    def elaborate(self, platform):
        m = Module()
        comb, sync = m.d.comb, m.d.sync

        #helper signals

        processed_hsync = Signal() # 0 at blank, 1 otherwise
        processed_vsync = Signal()

        if self.hsync_invert:
            comb += processed_hsync.eq(~self.hsync)
        else:
            comb += processed_hsync.eq(self,hsync)

        if self.vsync_invert:
            comb += processed_vsync.eq(~self.vsync)
        else:
            comb += processed_vsync.eq(self,vsync)


        c0,c1,c2 = self.c0,self.c1,self.c2

        #queue logic

        color_queue = Array((Color(8) for _ in range(10)))
        ctrl_queue  = Array([
            Record([("vsync", 1), ("hsync", 1), ("blank", 1)])
            for _ in range(10)])

        for color, next_color in zip(color_queue, color_queue[1:]):
            sync += color.eq(*next_color.as_list()) ####
        sync += color_queue[-1].eq(self.red,self.green,self.blue)
        for ctrl, next_ctrl in zip(ctrl_queue, ctrl_queue[1:]):
            sync += ctrl.eq(next_ctrl)
        sync += ctrl_queue[-1].eq(Cat(self.vsync,self.hsync,self.blank))


        # logic for the normal operation- no transitions, no data island
        TMDS_8b10b = Array([ # lookup for colors during active time
            Const(TMDS_encode(x), unsigned(10)) for x in range(256) ])
        TMDS_2b10b = Array((Const(x,10) # lookup for control during blank
                            for x in [0b1101010100,
                                      0b0010101011,
                                      0b0101010100,
                                      0b1010101011])) # Hsync is bottom bit

        with m.If(ctrl_queue[0].blank == 0):
            sync += [
                c0.eq(TMDS_8b10b[color_queue[0].red]), ### check
                c1.eq(TMDS_8b10b[color_queue[0].green]),
                c2.eq(TMDS_8b10b[color_queue[0].blue])
            ]
        with m.Else():
            sync += [
                c0.eq(TMDS_2b10b[Cat(
                    ctrl_queue[0].hsync,
                    ctrl_queue[0].vsync)]),
                c1.eq(0b1101010100),
                c2.eq(0b1101010100)
            ]

        # logic for video preamble
        preamble_counter = Signal(range(10), reset=0)
          # the location of the first valid color in the queue.
        with m.If((self.blank==0) & (ctrl_queue[-1].blank==1)):
            sync += [ # video preamble
                c0.eq(0b1101010100),
                c1.eq(0b0010101011),
                c2.eq(0b1101010100),
                preamble_counter.eq(9)
                # next clock, position 9 in color_queue would be valid
            ]
        with m.If(preamble_counter > 2): # Video Guardband (5.2.2.1)
            sync += [
                c0.eq(0b1101010100),
                c1.eq(0b0010101011),
                c2.eq(0b1101010100),
                preamble_counter.eq(preamble_counter-1)
            ]
        with m.Elif(preamble_counter > 0): # Video Preamble (5.2.1.1)
            sync += [
                c0.eq(0b1011001100),
                c1.eq(0b0100110011),
                c2.eq(0b1011001100),
                preamble_counter.eq(preamble_counter-1)
            ]

        # logic for Nul data island
        data_island_armed = Signal(1,reset=0)
        with m.If((ctrl_queue[0].vsync == 1) &
                  (ctrl_queue[1].vsync == 0) ):
            sync += data_island_armed.eq(1)

        preamble_len = 8
        guardband_len = 2
        data_island_len = 32
        total_data_island_len = data_island_len+preamble_len+2*preamble_len

        data_island_index = Signal(range(total_data_island_len + 1),
                                   reset=total_data_island_len)
        with m.If(data_island_armed &
                  (ctrl_queue[0].hsync == 0) &
                  (ctrl_queue[1].hsync == 1) ): # if armed and hsync stops
            sync += [
                data_island_index.eq(0),
                data_island_armed.eq(0)
            ]

        TERC4 = Array([
            C(0b1010011100,10), # 5.4.3
            C(0b1001100011,10),
            C(0b1011100100,10),
            C(0b1011100010,10),
            C(0b0101110001,10),
            C(0b0100011110,10),
            C(0b0110001110,10),
            C(0b0100111100,10),
            C(0b1011001100,10),
            C(0b0100111001,10),
            C(0b0110011100,10),
            C(0b1011000110,10),
            C(0b1010001110,10),
            C(0b1001110001,10),
            C(0b0101100011,10),
            C(0b1011000011,10)
            ])
        data_island_preamble   = C(0b0101010100_0010101011_0010101011,30)
        # vsync active and hsync inactive
        data_island_guard_band = C(0b0101100011_0100110011_0100110011,30)
        # vsync active and hsync inactive

        # by default, when sending data island,
        with m.If(data_island_index < total_data_island_len):
            sync += [
                data_island_index.eq(data_island_index+1),
                c1.eq(TERC4[0b0000]),# send nothing
                c2.eq(TERC4[0b0000])
            ]

        with m.If(data_island_index < preamble_len):
            sync += Cat(c2,c1,c0).eq(data_island_preamble)
        with m.Elif(data_island_index < preamble_len + guardband_len):
            sync += Cat(c2,c1,c0).eq(data_island_guard_band)
        with m.Elif(data_island_index == preamble_len + guardband_len):
            sync += c0.eq(
                TERC4[Cat(ctrl_queue[0].hsync,ctrl_queue[0].vsync,C(0,2))])
            # first bit of the frame is 0
        with m.Elif(data_island_index <
                    preamble_len + guardband_len + data_island_len):
            sync += c0.eq(
                TERC4[Cat(ctrl_queue[0].hsync,ctrl_queue[0].vsync,C(2,2))])
                # other frame bits are 1
        with m.Elif(data_island_index < total_data_island_len):
            sync += Cat(c2,c1,c0).eq(data_island_guard_band)


        # asserts
        with m.If(self.blank==1): # when no data should be sent,
            sync += Assert(Cat(self.red, self.green, self.blue) == 0)
            # ... no data should be sent
        with m.If(ctrl_queue[0].blank==1): # same for exiting the queue
            sync += Assert(color_queue[0].as_concat() == 0)
        sync += Assert((data_island_index >= total_data_island_len) |
                           (preamble_counter == 0))
        return m

class Color(Record):
    def __init__(self, width=8):
        super().__init__([
            ("red", width),
            ("green", width),
            ("blue", width)])
    def as_concat(self):
        return Cat(self.red, self.green, self.blue)
    def as_list(self):
        return [self.red, self.green, self.blue]
    def eq(self, *color):
        if len(color)==1:
            return super().eq(color[0])
        elif len(color) == 3:
            r, g, b = color

        assert len(r)==len(g)==len(b)==len(self.red)
        return [
            self.red.eq(r),
            self.green.eq(g),
            self.blue.eq(b)]

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

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2 and sys.argv[1] == "--test":

        pass

    top = VGA_to_HDMI(hsync_invert=True, vsync_invert=True)
    with open("VGA_to_HDMI.v", "w") as f:
        f.write(verilog.convert(top, name = "VGA_to_HDMI", ports=[
            #inputs
            top.hsync, top.vsync, top.blank, top.red, top.green, top.blue,
            # outputs
            top.c0, top.c1, top.c2]
        ))
