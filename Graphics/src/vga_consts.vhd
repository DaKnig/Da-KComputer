library ieee;
use ieee.std_logic_1164.all;

package vga_consts is

  -- 25.175 Mhz clock for vga screen
  constant clk_T : time := 39.7219 ns;

  -- VGA columns/rows
  constant h_frame : integer := 800;
  constant v_frame : integer := 525;

  constant visible_x : integer := 640;
  constant visible_y : integer := 480;

  constant hsync_start : integer := 656;
  constant hsync_end   : integer := 752; -- one after the end

  constant vsync_start : integer := 490;
  constant vsync_end   : integer := 492; -- one after the end

end vga_consts;
