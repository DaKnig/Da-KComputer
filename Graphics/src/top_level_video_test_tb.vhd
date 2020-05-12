library ieee;
use ieee.std_logic_1164.all;

entity top_level_video_test_tb is

end entity top_level_video_test_tb;

architecture test of top_level_video_test_tb is

  constant T_CLK : time := 8 ns;

  component top_level_video_test is
    port (
      driving_clk          : in  std_logic;  -- 125MHz, for generating bit_clk
      video_out_p          : out std_logic_vector(2 downto 0);
      video_out_n          : out std_logic_vector(2 downto 0);
      bit_clk_n, bit_clk_p : out std_logic);

  end component top_level_video_test;

  signal driving_clk : std_logic := '0';
  signal video_out_p : std_logic_vector(2 downto 0);
  signal bit_clk_p   : std_logic;

begin  -- architecture test

  driving_clk <= not driving_clk after T_CLK/2;

  video_thing : component top_level_video_test
    port map (
      driving_clk => driving_clk,
      video_out_p => video_out_p,
      bit_clk_p   => bit_clk_p);

end architecture test;
