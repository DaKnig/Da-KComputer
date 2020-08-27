"""this class generates the required vga timing counters and sync signals"""

from nmigen import *

__all__ = ["VGA_timing_gen"]

class VGA_timing_gen(Elaboratable):
    def __init__(self, vga_mode, delay=1):
        """
        outputs:
          [hv]sync - 0 when sync, 1 otherwise
          blank - 0 when video active, 1 otherwise
          [hv]count - pixel number currently produced
        parameters:
          vga_mode- a dict as described above
          delay- delay between [hv]count and VGA signal- [hv]sync, blank
          and Color.
        """
        # parameters
        self.vga_mode = vga_mode
        # outputs
        self.hsync  = Signal()
        self.vsync  = Signal()
        self.blank  = Signal(reset = 0)
        self.hcount = Signal(
            range(self.vga_mode.h_whole_line),  reset = 0)
        self.vcount = Signal(
            range(self.vga_mode.v_whole_frame), reset = 0)
        self.delay  = delay
        if delay < 1:
            raise ValueError("delay must be at least one clock")

    def ports(self):
        return [# outputs
                self.hsync, self.vsync, self.blank, self.hcount,
                self.vcount]


    def elaborate(self, platform):
        m = Module()

        comb, sync = m.d.comb, m.d.sync

        hcount = Signal(self.hcount.shape())
        vcount = Signal(self.vcount.shape())
        comb += [
            self.hcount.eq(hcount),
            self.vcount.eq(vcount)]

        sync_queue = Array(
            [Record([("hsync",1),("vsync",1)]) for i in range(self.delay)])
        for i in range(self.delay-1):
            m.d.sync += sync_queue[i].eq(sync_queue[i+1])

        m.d.comb += [
            self.hsync.eq(sync_queue[0].hsync),
            self.vsync.eq(sync_queue[0].vsync)]




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
            sync += sync_queue[-1].hsync.eq(0)
        with m.Else():
            sync += sync_queue[-1].hsync.eq(1)

        with m.If((vcount >= v.v_sync_start) & (vcount < v.v_sync_end)):
            sync += sync_queue[-1].vsync.eq(0)
        with m.Else():
            sync += sync_queue[-1].vsync.eq(1)

        with m.If((vcount >= v.v_visible_area) |
                  (hcount >= v.h_visible_area)):
            sync += self.blank.eq(1)
        with m.Else():
            sync += self.blank.eq(0)

        return m
