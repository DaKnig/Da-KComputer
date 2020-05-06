library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity HDMI_encoder is
  
  port (
    red            : in  unsigned (7 downto 0);  -- red component
    blue           : in  unsigned (7 downto 0);  -- blue component
    green          : in  unsigned (7 downto 0);  -- green component
    bit_clk        : in  std_logic;       -- the bit clock, 250 MHz for VGA
    sync_counter   : in  integer range 0 to 9; -- the bit to send out
    hsync, vsync   : in  std_logic;
    active         : in  std_logic; -- '1' for data, '0' for control
    hotplug_detect : in  std_logic;
    serial_red     : out std_logic;  -- red to be sent in serial. at bit_clk.
    serial_blue    : out std_logic;
    serial_green   : out std_logic);

end entity HDMI_encoder;

architecture behave of HDMI_encoder is

  component TMDS_encoder is
  
  port (
    data_in     : in  unsigned(7 downto 0);  -- serial data in
                                             -- clocked at the pixel clock
    data_out    : out unsigned(9 downto 0);  -- serial data out
                                             -- clocked at 10x pixel clock
    rst         : in  std_logic;          -- reset the state of the encoder,
                                          -- used for synch or something
    bit_clk     : in std_logic;           -- 10x pixel clock

    sync_counter: in integer range 0 to 9; -- data changes after 9
    hsync,vsync : in std_logic;
    active      : in std_logic);
  end component TMDS_encoder;

  signal red_TMDS, blue_TMDS, green_TMDS : unsigned(9 downto 0);
                                        -- parallel TMDS data
  signal rst_TMDS     : std_logic;
  signal tmds_clk_en  : std_logic := '0';

  signal TMDS_2b10b_control : unsigned(9 downto 0);
  signal TMDS_control : std_logic_vector(1 downto 0);
begin  -- architecture behave
  
  process (bit_clk) is
  begin  -- process
    if rising_edge(bit_clk) then
      serial_red   <= red_TMDS(sync_counter);
      serial_blue  <= blue_TMDS(sync_counter);
      serial_green <= green_TMDS(sync_counter);
    end if;
  end process;





  red_TMDS_unit : TMDS_encoder
    port map (
      data_in      => red,
      data_out     => red_TMDS,
      rst          => rst_TMDS,
      bit_clk      => bit_clk,
      sync_counter => sync_counter,
      hsync        => hsync,
      vsync        => vsync,
      active       => active);

  blue_TMDS_unit: TMDS_encoder
    port map (
      data_in      => blue,
      data_out     => blue_TMDS,
      rst          => rst_TMDS,
      bit_clk      => bit_clk,
      sync_counter => sync_counter,
      hsync        => hsync,
      vsync        => vsync,
      active       => active);

  green_TMDS_unit: TMDS_encoder
    port map (
      data_in      => green,
      data_out     => green_TMDS,
      rst          => rst_TMDS,
      bit_clk      => bit_clk,
      sync_counter => sync_counter,
      hsync        => hsync,
      vsync        => vsync,
      active       => active);

end architecture behave;
