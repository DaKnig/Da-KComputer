"""
Top_Triangle:
    input params:
        y_top, x_top, z_top, color_top
        delta_left_x, delta_right_x

        delta_z_x, delta_color_x
        delta_z_y, delta_color_y (the differential of the left side)

        y_bottom
    in:
        i_x, i_y
    out:
        o_color, o_z
    output generic param:
        delay - x,y in to color out

Bottom_Triangle:
    input params:
        y_top, x_top, z_top, color_top, width_top
        delta_left_x, delta_right_x

        delta_z_x, delta_color_x
        delta_z_y, delta_color_y (the differential of the left side)

        y_bottom
    in:
        i_x, i_y
    out:
        o_color, o_z
    output generic param:
        delay - x,y in to color out

Controller:
    in:
        offset_x, offset_y, offset_z - from kb controller - for tirangle 1
        vga_x, vga_y - from vga timing gen
    out:
        color
        delay - x,y in to clock out
"""
from nmigen import *
from nmigen.hdl.ast import *

from Color import Color

class Top_Triangle(Elaboratable):
    def __init__(self, vga_mode,
                 y_top, x_top, z_top, color_top, y_bottom,
                 delta_left_x, delta_right_x,

                 delta_z_x, delta_color_x,
                 delta_z_y, delta_color_y):
        # input params
        self.vga_mode      = vga_mode
        self.y_top         = y_top
        self.x_top         = x_top
        self.z_top         = z_top
        self.color_top     = color_top
        self.delta_left_x  = delta_left_x
        self.delta_right_x = delta_right_x

        self.delta_z_x     = delta_z_x
        self.delta_color_x = delta_color_x
        self.delta_z_y     = delta_z_y
        self.delta_color_y = delta_color_y

        self.y_bottom      = y_bottom

        # inputs
        self.i_x     = Signal(11)
        self.i_y     = Signal(10)
        # outputs
        self.o_color = Color(8) # output is 4 bits anyways
        self.o_z     = Signal(16)
        self.o_delay = 0 ####@@@@

    def ports(self):
        return [
            self.i_x, self.i_y,
            self.o_color, self.o_z]
    def elaborate(self, platform):
        m = Module()
        comb, sync = m.d.comb, m.d.sync

        left_x  = Signal(signed(12))
        right_x = Signal(signed(12))

        left_z  = Signal(16)
        left_color = Color(8)

        next_x, next_y = Signal(signed(12)), Signal(signed(12))
        next_z, next_color = Signal(16), Color(8)
        # prepare the next pixel. when x,y match it, output it.

        x, y = self.i_x, self.i_y

        line_finished = Signal()

        with m.If(x == self.vga_mode.h_visible_area):
            sync += line_finished.eq(1)
        with m.Elif(x == 0):
            sync += line_finished.eq(0)

        with m.If ((x == next_x) & (y == next_y)):
            comb += [
                self.o_color.eq(next_color),
                self.o_z.eq(next_z),
            ]


        with m.If( (y==self.y_bottom) | (y==self.vga_mode.v_visible_area) ):
            # prepare for the next frame
            sync += [
                next_x.eq (self.x_top),
                next_y.eq (self.y_top),
                next_z.eq (self.z_top),
                next_color.eq(self.color_top),

                left_x.eq (self.x_top),
                right_x.eq(self.x_top),
                left_z.eq (self.z_top),
                left_color.eq(self.color_top)]
        with m.Elif(((x >= right_x) & (line_finished == 0)) | \
                    (x >= self.vga_mode.h_visible_area)):
            # prepare for the next line
            sync += [
                left_x.eq (left_x  + self.delta_left_x),
                next_x.eq (left_x  + self.delta_left_x),
                right_x.eq(right_x + self.delta_right_x),

                next_y.eq (y + 1),
                left_z.eq (left_z + self.delta_z_y),
                next_z.eq (left_z + self.delta_z_y),

                next_color.red  .eq(left_color.red   + \
                                    self.delta_color_y.red  ),
                next_color.green.eq(left_color.green + \
                                    self.delta_color_y.green),
                next_color.blue .eq(left_color.blue  + \
                                    self.delta_color_y.blue ),

                left_color.red  .eq(left_color.red   + \
                                    self.delta_color_y.red  ),
                left_color.green.eq(left_color.green + \
                                    self.delta_color_y.green),
                left_color.blue .eq(left_color.blue  + \
                                    self.delta_color_y.blue ),

                line_finished.eq(1),
            ]
        with m.Elif((x >= left_x) & (x < right_x) & (line_finished == 0)):
            # if active, prepare next pixel
            sync += [
                next_x.eq(next_x + 1),
                next_z.eq (left_z + self.delta_z_x),

                next_color.red  .eq(next_color.red   + \
                                    self.delta_color_x.red  ),
                next_color.green.eq(next_color.green + \
                                    self.delta_color_x.green),
                next_color.blue .eq(next_color.blue  + \
                                    self.delta_color_x.blue ),
            ]
        with m.Else():
            # if you dont do anything... might as well do something useful
            with m.If(next_x < 0): # avoid drawing outside the screen
                sync += [
                    next_x.eq(next_x + 1),
                    next_z.eq(next_z + self.delta_z_x),
                    next_color.red  .eq(next_color.red   + \
                                        self.delta_color_x.red  ),
                    next_color.green.eq(next_color.green + \
                                        self.delta_color_x.green),
                    next_color.blue .eq(next_color.blue  + \
                                        self.delta_color_x.blue ),
                ]

            with m.If(left_x < 0):
                sync += [
                    left_x.eq(left_x + 1),
                    left_z.eq(left_z + self.delta_z_x),
                    left_color.red  .eq(left_color.red   + \
                                        self.delta_color_x.red  ),
                    left_color.green.eq(left_color.green + \
                                        self.delta_color_x.green),
                    left_color.blue .eq(left_color.blue  + \
                                        self.delta_color_x.blue ),
                ]
            ### can add the "do this 32/1024 times" clause to speed it up
        return m

class Controller(Elaboratable):
    """
    in:
        vga_x, vga_y - from vga timing gen
    out:
        color
        delay - x,y in to clock out
    must finish: @@@@@
        offset_x, offset_y, offset_z
        - from kb controller - for tirangle 1 - internal
    """
    def __init__(self, vga_mode):
        self.vga_mode = vga_mode
        self.offset_x = 0
        self.offset_y = 0
        self.offset_z = 0

        self.hcount = Signal(
            range(self.vga_mode.h_whole_line))
        self.vcount = Signal(
            range(self.vga_mode.v_whole_frame))

        self.color = Color(8)
        self.delay = 1
    def ports(self):
        return [# outputs
                self.color.red, self.color.green, self.color.blue,
                # inputs
                self.hcount, self.vcount]

    def elaborate(self, platform):
        m = Module()
        sync, comb = m.d.sync, m.d.comb

        x_top, y_top, z_top = [], [], []
        delta_left_x, delta_right_x, delta_z_x = [], [], []
        delta_z_y, y_bottom = [], []

        color_top, delta_color_x, delta_color_y = [], [], []

        fields = [
            x_top, y_top, z_top, delta_left_x, delta_right_x, delta_z_x,
            delta_z_y, y_bottom]
        colors = [
            color_top, delta_color_x, delta_color_y]

        with open("triangle_init_data.csv") as f:
            for line in f:
                if line[0] == '#' or line.strip() == "": continue

                values = [s.strip() for s in line.split(',')]

                for field in fields:
                    field.append(int(values[0]))
                    del values[0]

                for cl in colors:
                    cl.append(Color(signed(9)))
                    comb += [
                        cl[-1].red  .eq(int(values[0])),
                        cl[-1].green.eq(int(values[1])),
                        cl[-1].blue .eq(int(values[2])), ]
                    del values[0]
                    del values[0]
                    del values[0]

        # outputs
        o_color = []
        o_z     = []
        for i in range(len(fields[0])):
            m.submodules["TopTriangle_%d"%i] = (
                Top_Triangle(
                    self.vga_mode,
                    y_top         = y_top[i],
                    x_top         = x_top[i],
                    z_top         = z_top[i],
                    color_top     = color_top[i],
                    y_bottom      = y_bottom[i],
                    delta_left_x  = delta_left_x[i],
                    delta_right_x = delta_right_x[i],
                    delta_z_x     = delta_z_x[i],
                    delta_color_x = delta_color_x[i],
                    delta_z_y     = delta_z_y[i],
                    delta_color_y = delta_color_y[i]))
            o_z.append(Signal(16))
            o_color.append(Color(8))
            comb += [
                m.submodules["TopTriangle_%d"%i].i_x.eq(self.hcount),
                m.submodules["TopTriangle_%d"%i].i_y.eq(self.vcount),

                o_z    [-1].eq(m.submodules["TopTriangle_%d"%i].o_z),
                o_color[-1].eq(m.submodules["TopTriangle_%d"%i].o_color),
            ]
        #@@@ add multi triangle shit
        comb += self.color.eq(o_color[0])
        comb += self.color.eq(250)
        return m
