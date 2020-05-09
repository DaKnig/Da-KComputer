library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.vga_consts.all;

entity VGA_signal_generator_tb is

end entity VGA_signal_generator_tb;

architecture behave of VGA_signal_generator_tb is

  component VGA_signal_generator is
    port (
      bit_clk, rst     : in  std_logic;           -- bit clock and synch rst
      red, blue, green : out unsigned(7 downto 0); -- clocked at pixel clock
      sync_counter     : out integer range 0 to 9;
      hsync, vsync     : out std_logic;

      active           : out boolean); -- '1' for video data, '0' for ctrl
  end component VGA_signal_generator;

  signal bit_clk, rst     : std_logic := '1';     -- bit clock and synch rst
  signal red, blue, green : unsigned(7 downto 0); -- clocked at pixel clock
  signal sync_counter     : integer range 0 to 9;
  signal hsync, vsync     : std_logic;
  signal active           : boolean; -- '1' for video data, '0' for ctrl

begin  -- architecture behave

  gen: component VGA_signal_generator
    port map (bit_clk,rst,red,blue,green,sync_counter,hsync,vsync,active);

  bit_clk <= not bit_clk after 1 ns; -- does that really matter
  rst <= '0';

  -- a->b is like ~a|b
  process (bit_clk) is
  begin
    assert active or (red = 0 and red = blue and red = green)
      report "color during inactive time";

    assert not active or (hsync = '0' and vsync = '0')
      report "active while syncing";
  end process;
end architecture behave;
