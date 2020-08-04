library ieee;
use ieee.STD_LOGIC_1164.all;

entity HDMI_tb is

end entity HDMI_tb;

architecture test of HDMI_tb is

  signal clk125         : std_logic := '0';
  signal hdmi_out_p     : std_logic_vector(3 downto 0);
  signal hdmi_out_n     : std_logic_vector(3 downto 0);

  signal leds           : std_logic_vector(3 downto 0);


  component hdmi_output_test is
    port (
      clk125 : in std_logic := '0';
      hdmi_out_p : out std_logic_vector(3 downto 0);
      hdmi_out_n : out std_logic_vector(3 downto 0);

      leds : out std_logic_vector(3 downto 0));
  end component hdmi_output_test;
    

begin  -- architecture test

  hdmi_i : hdmi_output_test port map(
      clk125     => clk125,
      hdmi_out_p => hdmi_out_p,
      hdmi_out_n => hdmi_out_n,

      leds       => leds
      );
  clk125 <= not clk125 after 8 ns;

end architecture test;
