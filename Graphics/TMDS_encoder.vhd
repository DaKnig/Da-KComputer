library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity TMDS_encoder is
  
  port (
    data_in     : in  unsigned(7 downto 0);  -- serial data in, clocked at the pixel clock
    data_out    : out std_logic;  -- serial data out, clocked at 10x pixel clock
    rst         : in  std_logic;  -- reset the state of the encoder, used for
                                  -- synch or something
    bit_clock   : in  std_logic;  -- 10x pixel clock
    pixel_clock : out std_logic);

end entity TMDS_encoder;

architecture behave of TMDS_encoder is

  signal data_reduced_transitions: unsigned(7 downto 0);
  signal bit_counter : integer range 0 to 9;
begin  -- architecture behave

  -- purpose: generate data_reduced_transition
  -- type   : sequential
  -- inputs : bit_clock, rst, data_in
  -- outputs: data_reduced_transitions
  process (bit_clock, rst) is
  begin  -- process
    if rst = '0' then                   -- asynchronous reset (active low)
      bit_counter <= 0;
    elsif bit_clock'event and bit_clock = '1' then  -- rising clock edge
      data_reduced_transitions <=
        shift_left(data_in,1) xor data_in;
    end if;
  end process;
--  data_reduced_transitions

end architecture behave;
