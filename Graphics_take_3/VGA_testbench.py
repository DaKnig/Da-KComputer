#!/usr/bin/env python3
"""
VGA testbench. shows the frames on a pygame surface on screen.
works only for a specified VGA_mode as specified in VGA_signal_gen.py
"""
from nmigen import *
from nmigen.back.pysim import Simulator, Passive

from Color import Color

import pygame
import numpy as np
import sys



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
    global s

    pygame.init()
    d = pygame.display.set_mode(
        (vga_mode.h_visible_area, vga_mode.v_visible_area))
    s = pygame.surfarray.pixels2d(d)

    global counter
    # give it a few cycles to start up
    counter = 0
    for _ in range(20):
        yield
        counter += 1

    # wait for vsync to be inactive
    while True:
        hs = yield hsync # use this for less accurate, faster detection
        if hs==1:
  #      vs = yield vsync
   #     if vs==1:
            break
        yield
        counter += 1
    # wait for active vsync
    print("vsync 1 detected at",counter)
    #print("hsync 1 detected at",counter)

    while True:
        hs = yield hsync # same as above comment
        if hs==0:
    #    vs = yield vsync
    #    if vs==0:
            break
        yield
        counter += 1
    # wair for picture
    print(f"vsync at counter={counter}")
    #print(f"hsync at counter={counter}")

    clocks_till_frame = vga_mode.h_whole_line * \
        (vga_mode.v_sync_pulse + vga_mode.v_back_porch)
    for _ in range(clocks_till_frame):
        yield
        counter += 1

    print(f"starting drawing frame at {counter}")
    # pdb.set_trace() # use this on older python3 interpreters
    # breakpoint()
    correction = (8-len(color.blue))
    for v in range(vga_mode.v_visible_area):
        for h in range(vga_mode.h_visible_area):
            x = yield color.blue
            x += (yield color.green) << 8
            x += (yield color.red) << 16
            s[h][v] = x << correction
            yield
            counter += 1
        for h in range(vga_mode.h_visible_area, vga_mode.h_whole_line):
            yield
            counter += 1
    print(f"finished drawing frame at {counter}")

    pygame.display.update()

from VGA_timing_gen import VGA_timing_gen
from VGA_signal_gen import VGA_mode
from top_level import Controller

def main():
    import sys

    frames_to_sym=2
    if "--frames" in sys.argv:
        frames_to_sym = sys.argv[sys.argv.index("--frames")+1]
        frames_to_sym = float (frames_to_sym)

    m = Module()

    m.submodules.vgagen = vgagen = Controller(VGA_mode)#VGA_signal_gen()
    m.submodules.timegen = timegen = VGA_timing_gen(
        vga_mode = VGA_mode,
        delay= vgagen.delay)

    m.d.comb += [ # port map
        vgagen.hcount.eq(timegen.hcount),
        vgagen.vcount.eq(timegen.vcount),
        #vgagen.blank.eq(timegen.blank)
    ]

    sim = Simulator(m)
    sim.add_clock(25e-9, domain="sync")

    def wrap(process):
        def wrapper():
            yield from process
        return wrapper

    def status_print():
        yield Passive()
        global counter
        while True:
            for _ in range(10_000):
                yield
            print("counter is", counter//1000,"k",
                  "that is %7.5f"%(counter/VGA_mode.h_whole_line),
                  "scanlines")

    sim.add_sync_process(wrap(test_vga(VGA_mode, timegen.hsync, timegen.vsync, vgagen.color)), domain = "sync")
    sim.add_sync_process(status_print, domain="sync")

    with sim.write_vcd("test.vcd", "test.gtkw",
                       traces= timegen.ports() + vgagen.ports() ):
        sim.run_until(2.5*frames_to_sym/60)


import pdb
#pdb.set_trace()
if __name__=="__main__":
#    pdb.set_trace()
    #try:
        main()
#    except Exception as e:
        print("\n counter =",counter)
        breakpoint()
        print("the screen",["is","isn't"][s.any()],"completely black")
 #       print("exception was:",e)
#        raise e

#    pdb.set_trace()
