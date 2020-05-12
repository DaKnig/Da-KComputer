library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity HDMI_encoder is

  port (
    red, blue, green : in  unsigned (7 downto 0);  -- parallel colors
    bit_clk          : in  std_logic;   -- the bit clock, 250 MHz for VGA
    pix_clk          : in  std_logic;   -- pixel clock, 25MHz
    hsync, vsync     : in  std_logic;
    active           : in  boolean;     -- true for data, false for control
    hotplug_detect   : in  std_logic;
    serial_red       : out std_logic;  -- red to be sent in serial. at bit_clk.
    serial_blue      : out std_logic;
    serial_green     : out std_logic;
    serial_pix_clk   : out std_logic);  -- synch'd with the serial data

end entity HDMI_encoder;

architecture behave of HDMI_encoder is

  component TMDS_encoder is

    port (
      data_in     : in  unsigned(7 downto 0);  -- serial data in
                                               -- clocked at the pixel clock
      data_out    : out unsigned(9 downto 0);  -- serial data out
      rst         : in  std_logic;          -- reset the state of the encoder
                                            -- used for synch or something
      pix_clk     : in std_logic;           -- pixel clock. 25MHz.
      hsync,vsync : in std_logic;
      active      : in boolean);
  end component TMDS_encoder;

  signal red_TMDS, blue_TMDS, green_TMDS : unsigned(9 downto 0);
                                        -- parallel TMDS data
  signal rst_TMDS     : std_logic;

  signal shifting_red, shifting_blue, shifting_green : unsigned(9 downto 0);
  signal serial_counter : integer range 9 downto 0 := 0;
begin  -- architecture behave

  serial_blue  <= shifting_blue(0);
  serial_green <= shifting_green(0);
  serial_red   <= shifting_red(0);
  
  process (bit_clk) is
  begin  -- process
    if rising_edge(bit_clk) then
      if serial_counter = 9 then
        serial_pix_clk <= '0';
      elsif serial_counter = 4 then
        serial_pix_clk <= '1';
      end if;

      if serial_counter = 9 then
        serial_counter <= 0;
        shifting_blue  <= blue_TMDS;
        shifting_green <= green_TMDS;
        shifting_red   <= red_TMDS;
      else
        serial_counter <= serial_counter + 1;
        shifting_blue  <= '0' & shifting_red(9 downto 1);
        shifting_green <= '0' & shifting_red(9 downto 1);
        shifting_red   <= '0' & shifting_red(9 downto 1);
      end if;
    end if;
  end process;

  rst_TMDS <= not hotplug_detect; -- do nothing when hotplug is 0



  blue_TMDS_unit : TMDS_encoder
    port map (
      data_in      => red,
      data_out     => red_TMDS,
      rst          => rst_TMDS,
      pix_clk      => pix_clk,
      hsync        => hsync,
      vsync        => vsync,
      active       => active);

  green_TMDS_unit: TMDS_encoder
    port map (
      data_in      => blue,
      data_out     => blue_TMDS,
      rst          => rst_TMDS,
      pix_clk      => pix_clk,
      hsync        => '0',
      vsync        => '0',
      active       => active);

  red_TMDS_unit: TMDS_encoder
    port map (
      data_in      => green,
      data_out     => green_TMDS,
      rst          => rst_TMDS,
      pix_clk      => pix_clk,
      hsync        => '0',
      vsync        => '0',
      active       => active);

end architecture behave;
