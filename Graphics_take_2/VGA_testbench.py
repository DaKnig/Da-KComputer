#!/usr/bin/env python3
"""
VGA testbench. shows the frames on a pygame surface on screen.
works only for a specified VGA_mode as specified in VGA_signal_gen.py
"""
from nmigen import *
from nmigen.back.pysim import Simulator

from Color import Color

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

def test_vga(vga_mode, hsync, vsync, color):
    """
    hsync, vsync- 1-bit Signals
    color - Color
    """

    import pygame
    import numpy as np
    import sys


    pygame.init()
    d = pygame.display.set_mode(
        (vga_mode.h_visible_area, vga_mode.v_visible_area))
    s = pygame.surfarray.pixels2d(d)


    # give it a few cycles to start up
    counter = 0
    for _ in range(20):
        yield
        counter += 1

    # wait for vsync to be inactive
    while True:
        vsync = yield vsync
        if vsync==1:
            break
        yield
        counter += 1
    # wait for active vsync
    while True:
        vsync = yield vsync
        if vsync==0:
            print(f"vsync at counter={counter}")
            break
        yield
        counter += 1
    # wair for picture
    clocks_till_frame = vga_mode.h_whole_line * \
        (vga_mode.v_sync_pulse + vga_mode.v_back_porch)
    for _ in range():
        yield
        counter += 1

    print(f"starting drawing frame at {counter}")

    for v in range(vga_mode.v_visible_area):
        for h in range(vga_mode.h_visible_area):
            x = yield color.blue
            x += (yield color.green) << 8
            x += (yield color.red) << 16
            s[h][v] = x
            yield
            counter += 1
        for h in range(vga_mode.h_visible_area, vga_mode.h_whole_line):
            yield
            counter += 1
    print(f"finished drawing frame at {counter}")

    pygame.display.update()

from VGA_timing_gen import *
from VGA_signal_gen import *

def main():
    import sys

    frames_to_sym=2
    if "--frames" in sys.argv:
        frames_to_sym = sys.argv[sys.argv.index("--frames")+1]
        frames_to_sym = float (frames_to_sym)

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
    
    def wrap(process):
        def wrapper():
            yield from process
        return wrapper

    sim.add_sync_process(wrap(test_vga(VGA_mode, timegen.hsync, timegen.vsync, vgagen.color)), domain = "sync")

    with sim.write_vcd("test.vcd", "test.gtkw",
                       traces= timegen.ports() + vgagen.ports() ):
        sim.run_until(2*frames_to_sym/60)


if __name__=="__main__":
    main()
