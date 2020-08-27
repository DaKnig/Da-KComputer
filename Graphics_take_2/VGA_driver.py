#!/usr/bin/env python3
"""
provides bindings to pins for VGA_signal_gen.py for the PMOD VGA module
"""

from nmigen.back import verilog
from nmigen.asserts import Assert
from nmigen.lib.cdc import ResetSynchronizer
from nmigen.build.dsl import *
from nmigen import *

from arty_z7 import ArtyZ720Platform

class PLL(Elaboratable):
    def __init__(self, clk125):
        self.clk_125 = clk125
        self.clk_40 = Signal()
        # self.clk_clk200 = Signal()
        self.pll_locked = Signal()
    def elaborate(self, platform):
        m=Module()

        pll_fb = Signal()
        # pll_125 = Signal()
        pll_40 = Signal()
        # pll_clk200 = Signal()
        m.submodules += [
            Instance("PLLE2_BASE",
                     p_STARTUP_WAIT="FALSE", o_LOCKED=self.pll_locked,

                     # VCO @ 1GHz
                     p_REF_JITTER1=0.01, p_CLKIN1_PERIOD=8.0,
                     p_CLKFBOUT_MULT=8, p_DIVCLK_DIVIDE=1,
                     i_CLKIN1=self.clk_125, i_CLKFBIN=pll_fb, o_CLKFBOUT=pll_fb,

                     # 125MHz
                     # p_CLKOUT0_DIVIDE=8, p_CLKOUT0_PHASE=0.0, o_CLKOUT0=pll_125,

                     # 40MHz
                     p_CLKOUT1_DIVIDE=25, p_CLKOUT1_PHASE=0.0, o_CLKOUT1=pll_40,

                     # 200MHz
                     # p_CLKOUT2_DIVIDE=5, p_CLKOUT2_PHASE=0.0, o_CLKOUT2=pll_clk200
            ),
            # Instance("BUFG", i_I=pll_125, o_O=self.clk_125),
            Instance("BUFG", i_I=pll_40, o_O=self.clk_40),
            # Instance("BUFG", i_I=pll_clk200, o_O=self.clk_clk200),
        ]
        return m


from VGA_signal_gen import *

class VGA_driver(Elaboratable):
    def elaborate(self, platform):
        m=Module()
        m.submodules += Instance("PS7", a_keep="TRUE") # some vivado shit
        m.submodules.vgen = vgen = DomainRenamer("cd40")(VGA_signal_gen())

        m.submodules.clkgen = clkgen = PLL(platform.request("clk125"))

        cd40 = ClockDomain("cd40")
        m.domains += cd40
        m.d.comb += cd40.clk.eq(clkgen.clk_40)
        m.submodules += ResetSynchronizer(~clkgen.pll_locked,domain="cd40")

        platform.add_resources([
            Resource("vga", 0,
                Subsignal("r", Pins("1 2 3 4", dir="o", conn=("pmod", 0))),
                Subsignal("b", Pins("7 8 9 10",dir="o", conn=("pmod", 0))),
                Subsignal("g", Pins("1 2 3 4", dir="o", conn=("pmod", 1))),
                Subsignal("hs",Pins("7",       dir="o", conn=("pmod", 1))),
                Subsignal("vs",Pins("8",       dir="o", conn=("pmod", 1))),
                Attrs(IOSTANDARD="LVCMOS33"))
        ])

        vga = platform.request("vga")
        m.d.comb += [
            vga.r.eq(vgen.color.red  [-4:]),
            vga.b.eq(vgen.color.blue [-4:]),
            vga.g.eq(vgen.color.green[-4:]),
            vga.hs.eq(vgen.hsync),
            vga.vs.eq(vgen.vsync),
            ]
            
        display_switch = platform.request("switch",0) # SW0
        with m.If(display_switch):
            m.d.comb += vga.eq(0)
        return m

if __name__ == "__main__" :
    ArtyZ720Platform().build(VGA_driver(), do_program=True)
