library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity 	TMDS_encoder_tb is
  
end entity 	TMDS_encoder_tb;

architecture behave of TMDS_encoder_tb is
  constant T_CLK : time := 4 ns;

  component TMDS_encoder is
  
    port (
      data_in     : in  unsigned(7 downto 0);  -- serial data in
                                               -- clocked at the pixel clock
      data_out    : out unsigned(9 downto 0);  -- serial data out
                                               -- clocked at 10x pixel clock
      rst         : in  std_logic;  -- reset the state of the encoder, used for
                                  -- synch or something
      bit_clock   : in  std_logic;  -- 10x pixel clock
      pixel_clock : out std_logic);
    
  end component TMDS_encoder;

  signal data_in     : unsigned(7 downto 0);
  signal data_out    : unsigned(9 downto 0);  
  signal rst         : std_logic;
  signal bit_clock   : std_logic := '1';
  signal pixel_clock : std_logic;

  signal counter     : integer;
  
begin  -- architecture behave

  TMDS_encoder_instance: TMDS_encoder
    port map (
      data_in            => data_in,
      data_out           => data_out,
      rst                => rst,
      bit_clock          => bit_clock,
      pixel_clock        => pixel_clock);

  
  rst <= '1', '0' after 10 ns;

  bit_clock <= not bit_clock after T_CLK/2;

  process (pixel_clock, rst) is
  begin  -- process
    if rst = '1' then                   -- asynchronous reset (active low)
      counter <= 0;
    elsif rising_edge(pixel_clock) then  -- rising clock edge
      counter <= counter + 1;
    end if;
  end process;

  data_in <= x"99" when counter = 0 else -- 4 high bits, lowest bit 1, xor
             x"33" when counter = 1 else -- same
             x"66" when counter = 2 else -- 4 high bits, lowest bit 0, xnor
             x"20" when counter = 3 else -- 1 high bit, xor
             x"00";

end architecture behave;
