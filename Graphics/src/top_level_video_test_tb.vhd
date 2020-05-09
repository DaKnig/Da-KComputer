library ieee;
use ieee.std_logic_1164.all;

entity top_level_video_test_tb is

end entity top_level_video_test_tb;

architecture test of top_level_video_test_tb is

  component top_level_video_test is

    port (
      bit_clk                               : in std_logic;
      serial_red, serial_blue, serial_green : out std_logic);

  end component top_level_video_test;

  signal bit_clk : std_logic := '0';
  signal serial_red, serial_blue, serial_green : std_logic;

begin  -- architecture test

  bit_clk <= not bit_clk after 1 ns;

  video_thing: component top_level_video_test
    port map (
      bit_clk      => bit_clk,
      serial_red   => serial_red,
      serial_blue  => serial_blue,
      serial_green => serial_green);

end architecture test;
