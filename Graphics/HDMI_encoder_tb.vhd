library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity HDMI_encoder_tb is
end entity;

architecture HDMI_encoder_tb of HDMI_encoder_tb is

  component HDMI_encoder is
  
  port (
    red            : in  unsigned (7 downto 0);  -- red component
    blue           : in  unsigned (7 downto 0);  -- blue component
    green          : in  unsigned (7 downto 0);  -- green component
    bit_clk        : in  std_logic;       -- the bit clock, 250 MHz for VGA
    sync_counter   : in  integer range 0 to 9;
    hsync, vsync   : in  std_logic;
    active         : in  std_logic; -- '1' for data, '0' for control
    hotplug_detect : in  std_logic;
    serial_red     : out std_logic;  -- red to be sent in serial. at bit_clk.
    serial_blue    : out std_logic;
    serial_green   : out std_logic);
  end component;

  signal bit_clk                               : std_logic := '0';
  signal serial_red, serial_blue, serial_green : std_logic;

  signal sync_counter   : integer range 0 to 9 := 0;
  signal hsync, vsync   : std_logic;
  signal active         : std_logic := '1';
  signal hotplug_detect : std_logic := '1';

  type pixel is array (2 downto 0) of unsigned (7 downto 0);
  type video_memory is array (integer range <>) of pixel;

  signal vram : video_memory (0 to 1000):= ((x"33",x"33",x"33"),(x"55",x"56",x"57"),(x"ff",x"00",x"00") , others=>(x"00",x"00",x"00"));

  signal current_pixel : pixel;
  signal counter : integer := 0;

  signal red   : unsigned(7 downto 0);
  signal blue  : unsigned(7 downto 0);
  signal green : unsigned(7 downto 0);
begin  -- architecture HDMI_encoder_tb

  current_pixel <= vram(counter/10);
  
  red   <= current_pixel(2);
  blue  <= current_pixel(1);
  green <= current_pixel(0);

  bit_clk <= not bit_clk after 1 ns;
  process (bit_clk) is
  begin  -- process
    if rising_edge(bit_clk) then
      hsync <= '0';
      vsync <= '0';
      counter <= counter + 1;
      sync_counter <= (counter + 1) mod 10;
    end if;
  end process;



  
  encoder: HDMI_encoder
    port map (
      red            => red   ,
      blue           => blue  ,
      green          => green ,
      bit_clk        => bit_clk,
      sync_counter   => sync_counter,
      hsync          => hsync,
      vsync          => vsync,
      active         => active,
      hotplug_detect => hotplug_detect,
      serial_red     => serial_red,
      serial_blue    => serial_blue,
      serial_green   => serial_green);
end architecture HDMI_encoder_tb;
