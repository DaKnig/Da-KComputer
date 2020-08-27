#!/usr/bin/env python3
"""
this is a simple VGA signal generator, including VGA timing generator and all
"""

from nmigen.back import verilog

from nmigen import *

all = ["VGA_signal_gen"]

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

class VGA_signal_gen(Elaboratable):
    def __init__(self, vga_mode=VGA_mode, delay=1):
        """
        outputs:
          [hv]sync - 0 when sync, 1 otherwise
          blank - 0 when video active, 1 otherwise
          red,green,blue - values in range(16,240)
          [hv]count - pixel number currently produced
        parameters:
          vga_mode- a dict as described above
          delay- delay between [hv]count and VGA signal- [hv]sync, blank
          and Color.
        """
        # parameters
        self.vga_mode = VGA_mode
        # outputs
        self.hsync  = Signal(reset = 1)
        self.vsync  = Signal(reset = 1)
        self.blank  = Signal(reset = 0)
        self.red    = Signal(unsigned(8))
        self.green  = Signal(unsigned(8))
        self.blue   = Signal(unsigned(8))
        self.hcount = Signal(
            range(self.vga_mode.h_whole_line),  reset = 0)
        self.vcount = Signal(
            range(self.vga_mode.v_whole_frame), reset = 0)

    def ports(self):
        return [# outputs
                self.hsync, self.vsync, self.blank, self.red, self.green,
                self.blue, self.hcount, self.vcount]


    def elaborate(self, platform):
        m = Module()

        comb, sync = m.d.comb, m.d.sync

        hcount = Signal(self.hcount.shape())
        vcount = Signal(self.vcount.shape())
        comb += [
            self.hcount.eq(hcount),
            self.vcount.eq(vcount)]


        v = self.vga_mode

        # counter logic
        with m.If(hcount != v.h_whole_line-1):
            sync += hcount.eq(hcount+1)
        with m.Else():
            sync += hcount.eq(0)
            with m.If(vcount != v.v_whole_frame-1):
                sync += vcount.eq(vcount+1)
            with m.Else():
                sync += vcount.eq(0)

        # control logic
        with m.If((hcount >= v.h_sync_start) & (hcount < v.h_sync_end)):
            sync += self.hsync.eq(0)
        with m.Else():
            sync += self.hsync.eq(1)

        with m.If((vcount >= v.v_sync_start) & (vcount < v.v_sync_end)):
            sync += self.vsync.eq(0)
        with m.Else():
            sync += self.vsync.eq(1)

        with m.If((vcount >= v.v_visible_area) |
                  (hcount >= v.h_visible_area)):
            sync += [
                self.blue.eq(0),
                self.green.eq(0),
                self.red.eq(0)
            ]

            sync += self.blank.eq(1)
        with m.Else():
            sync += [
                self.blue.eq(hcount),
                self.green.eq(hcount+vcount),
                self.red.eq(vcount)
            ]

            sync += self.blank.eq(0)

        return m





if __name__ == "__main__":
    import sys
    if "--test" in sys.argv or "-t" in sys.argv:

        from nmigen.back.pysim import Simulator, Delay, Settle

        m = Module()

        m.submodules.vgagen = vgagen = VGA_signal_gen()

        sim = Simulator(m)
        sim.add_clock(25e-9, domain="sync")
        
        def process():
            yield Passive()

        # sim.add_sync_process(process, domain = "sync")
        with sim.write_vcd("test.vcd", "test.gtkw",
                           traces=vgagen.ports()):
            sim.run_until(2/60, run_passive=True)

    elif "--verilog" in sys.argv :
        top = VGA_signal_gen()
        with open("VGA_signal_gen.v", "w") as f:
            f.write(verilog.convert(top, name = "VGA_signal_gen",
                ports= top.ports(),
                strip_internal_attrs = "--strip" in sys.argv
            ))
