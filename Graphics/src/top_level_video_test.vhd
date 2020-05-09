library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity top_level_video_test is

  port (
    bit_clk                               : in  std_logic;
    serial_red, serial_blue, serial_green : out std_logic);

end entity top_level_video_test;

architecture test of top_level_video_test is

  component HDMI_encoder is

    port (
      red            : in  unsigned (7 downto 0);  -- red component
      blue           : in  unsigned (7 downto 0);  -- blue component
      green          : in  unsigned (7 downto 0);  -- green component
      bit_clk        : in  std_logic;   -- the bit clock, 250 MHz for VGA
      sync_counter   : in  integer range 0 to 9;   -- the bit to send out
      hsync, vsync   : in  std_logic;
      active         : in  boolean;     -- true for data, false for control
      hotplug_detect : in  std_logic;
      serial_red     : out std_logic;   --red to be sent in serial at bit_clk
      serial_blue    : out std_logic;
      serial_green   : out std_logic);

  end component HDMI_encoder;

  component VGA_signal_generator is
    port (
      bit_clk, rst     : in  std_logic;
      red, blue, green : out unsigned(7 downto 0);  -- clocked at pixel clock
      sync_counter     : out integer range 0 to 9;
      hsync, vsync     : out std_logic;

      active : out boolean);            -- '1' for video data, '0' for ctrl
  end component VGA_signal_generator;

  signal rst              : std_logic;
  signal red, blue, green : unsigned (7 downto 0);
  signal sync_counter     : integer range 0 to 9;
  signal hsync, vsync     : std_logic;
  signal active           : boolean;
  signal hotplug_detect   : std_logic;

begin  -- architecture test

  rst            <= '0';
  hotplug_detect <= '1';                -- for now. ("monitor is connected")

  data_generator : component VGA_signal_generator
    port map (
      bit_clk      => bit_clk,
      rst          => rst,
      red          => red,
      blue         => blue,
      green        => green,
      sync_counter => sync_counter,
      hsync        => hsync,
      vsync        => vsync,
      active       => active);

  encoder : component HDMI_encoder
    port map (
      red            => red,
      blue           => blue,
      green          => green,
      bit_clk        => bit_clk,
      sync_counter   => sync_counter,
      hsync          => hsync,
      vsync          => vsync,
      active         => active,
      hotplug_detect => hotplug_detect,
      serial_red     => serial_red,
      serial_blue    => serial_blue,
      serial_green   => serial_green);

end architecture test;
