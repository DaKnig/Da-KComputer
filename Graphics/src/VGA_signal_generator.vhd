library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.vga_consts.all;

entity VGA_signal_generator is
  port (
    bit_clk, rst     : in  std_logic;             -- bit clock and synch rst
    red, blue, green : out unsigned(7 downto 0);  -- clocked at pixel clock
    sync_counter     : out integer range 0 to 9;
    hsync, vsync     : out std_logic;

    active           : out boolean); -- '1' for video data, '0' for ctrl
end entity VGA_signal_generator;

architecture behave of VGA_signal_generator is

  signal h_cnt : integer range 0 to h_frame-1 := 0;
  signal v_cnt : integer range 0 to v_frame-1 := 0;

  signal effect1, effect2 : unsigned(9 downto 0);

  signal sync_counter_inner : integer range 0 to 9;

begin  -- architecture behave

  active <= h_cnt < visible_x and v_cnt < visible_y;
  sync_counter <= sync_counter_inner;

  hsync <= '1' when h_cnt < hsync_end and h_cnt >= hsync_start else '0';
  vsync <= '1' when v_cnt < vsync_end and v_cnt >= vsync_start else '0';

  effect1 <= to_unsigned (h_cnt, 10) when active else (others => '0');
  effect2 <= to_unsigned (v_cnt, 10) when active else (others => '0');

  red <=   effect1(9 downto 2) and effect2(7 downto 0);
  blue <=  (effect1(9 downto 2) xor effect1(7 downto 0)) or effect2(8 downto 1);
  green <= x"00";

  process (bit_clk) is
  begin  -- process
    if rst = '1' then
      h_cnt <= h_frame-1;
      v_cnt <= v_frame-1;
      sync_counter_inner <= 9; -- because next clock it's going to change
    elsif sync_counter_inner < 9 then
      sync_counter_inner <= sync_counter_inner+1;
    else -- sync_counter = 9
      sync_counter_inner <= 0;

      h_cnt <= 0 when h_cnt = h_frame-1 else h_cnt+1;
      if h_cnt = h_frame-1 then
        v_cnt <= 0 when (h_cnt = h_frame-1 and v_cnt = v_frame-1)
                 else v_cnt+1;
      end if;
    end if;
  end process;

end architecture behave;
