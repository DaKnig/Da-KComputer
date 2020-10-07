#!/usr/bin/env python3
"""
this is a simple VGA signal generator, including VGA timing generator and all
"""

from nmigen.back import verilog
from nmigen import *

__all__ = ["VGA_signal_gen", "VGA_mode"]

class VGA_mode:
    def __init__(self):
        # horiz
        self.h_visible_area = 800
        self.h_front_porch =  40
        self.h_sync_pulse =   128
        self.h_back_porch =   88
        self.h_whole_line =   1056
        # vertical
        self.v_visible_area = 600
        self.v_front_porch =  1
        self.v_sync_pulse =   4
        self.v_back_porch =   23
        self.v_whole_frame =  628

        # helpers
        self.h_sync_start = self.h_visible_area + self.h_front_porch

        self.h_sync_end   = self.h_sync_start + self.h_sync_pulse

        self.v_sync_start = self.v_visible_area + self.v_front_porch
        self.v_sync_end   = self.v_sync_start + self.v_sync_pulse

VGA_mode = VGA_mode()

from Color import Color

class VGA_signal_gen(Elaboratable):
    def __init__(self, vga_mode=VGA_mode):
        """
        inputs:
          blank - 0 when video active, 1 otherwise
          [hv]count - pixel number currently produced
        outputs:
          color - color to display
        parameters:
          vga_mode- a dict as described above
          delay- delay between [hv]count and VGA signal- [hv]sync, blank
          and Color.
        """
        # parameters
        self.vga_mode = vga_mode
        self.delay  = 1 ## outputs one clock after x,y
        #inputs
        self.blank  = Signal()
        self.hcount = Signal(
            range(self.vga_mode.h_whole_line))
        self.vcount = Signal(
            range(self.vga_mode.v_whole_frame))
        #outputs
        self.color  = Color(4)

    def ports(self):
        return [# outputs
                self.color.red, self.color.green, self.color.blue,
                # inputs
                self.blank, self.hcount, self.vcount]


    def elaborate(self, platform):
        m = Module()

        comb, sync = m.d.comb, m.d.sync

        red, green, blue = self.color.as_list()

        v = self.vga_mode

        with m.If((self.vcount >= v.v_visible_area) |
                  (self.hcount >= v.h_visible_area)):
            sync += [
                blue.eq(0),
                green.eq(0),
                red.eq(0)
            ]

        with m.Else():
            sync += [
                blue.eq(self.hcount),
                green.eq(self.hcount + self.vcount),
                red.eq(self.vcount)
            ]

        return m

from VGA_timing_gen import *

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv or "-t" in sys.argv:
        from VGA_timing_gen import *

        frames_to_sym=2
        if "--frames" in sys.argv:
            frames_to_sym = sys.argv[sys.argv.index("--frames")+1]
            frames_to_sym = float (frames_to_sym)
        from nmigen.back.pysim import Simulator, Delay, Settle

        m = Module()

        m.submodules.vgagen = vgagen = VGA_signal_gen()
        m.submodules.timegen = timegen = VGA_timing_gen(
            vga_mode = VGA_mode,
            delay= vgagen.delay)

        m.d.comb += [ # port map
            vgagen.hcount.eq(timegen.hcount),
            vgagen.vcount.eq(timegen.vcount),
            vgagen.blank.eq(timegen.blank)
            ]

        sim = Simulator(m)
        sim.add_clock(25e-9, domain="sync")

        def process():
            yield Passive()

        # sim.add_sync_process(process, domain = "sync")
        with sim.write_vcd("test.vcd", "test.gtkw",
                           traces= timegen.ports() + vgagen.ports() ):
            sim.run_until(frames_to_sym/60, run_passive=True)

    elif "--verilog" in sys.argv :
        top = VGA_signal_gen()
        with open("VGA_signal_gen.v", "w") as f:
            f.write(verilog.convert(top, name = "VGA_signal_gen",
                ports= top.ports(),
                strip_internal_attrs = "--strip" in sys.argv
            ))
