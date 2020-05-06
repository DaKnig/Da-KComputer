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
      bit_clk     : in std_logic;
      sync_counter: in integer range 0 to 9; -- data changes after 9
      hsync,vsync : in std_logic;
      active      : in std_logic);  -- clock enable - logic happens when its on
  end component TMDS_encoder;

  signal data_in     : unsigned(7 downto 0);
  signal data_out    : unsigned(9 downto 0);  
  signal rst         : std_logic;
  signal bit_clk     : std_logic := '1';

  signal counter     : integer range 0 to 9;
  signal data_counter: integer := 0;
  signal hsync,vsync : std_logic;
  signal active      : std_logic;

  type ROM is array (integer range <>) of unsigned(7 downto 0);
  signal inputs : ROM(0 to 100) := (
    x"99",x"33",x"66",x"20",x"ff", others=>x"00");
begin  -- architecture behave

  TMDS_encoder_instance: TMDS_encoder
    port map (
      data_in            => data_in,
      data_out           => data_out,
      rst                => rst,
      hsync              => hsync,
      vsync              => vsync,
      active             => active,
      sync_counter       => counter,
      bit_clk            => bit_clk);

  
  rst <= '1', '0' after 10 ns;

  bit_clk <= not bit_clk after T_CLK/2;


  process (bit_clk, rst) is
  begin  -- process
    if rst = '1' then                   -- asynchronous reset (active low)
      counter <= 0;
    elsif rising_edge(bit_clk) then  -- rising clock edge
      counter <= counter + 1 when counter<9 else 0;
      data_counter <= data_counter + 1 when counter = 9 else data_counter;
    end if;
  end process;

  data_in <= inputs(data_counter);

end architecture behave;
