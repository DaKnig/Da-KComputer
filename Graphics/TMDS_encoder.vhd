library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.useful_functions.all;

entity TMDS_encoder is
  
  port (
    data_in     : in  unsigned(7 downto 0);  -- serial data in
                                             -- clocked at the pixel clock
    data_out    : out unsigned(9 downto 0);  -- serial data out
                                             -- clocked at 10x pixel clock
    rst         : in  std_logic;  -- reset the state of the encoder, used for
                                  -- synch or something
    bit_clock   : in  std_logic;  -- 10x pixel clock
    pixel_clock : out std_logic);

end entity TMDS_encoder;

architecture behave of TMDS_encoder is

  signal data_st_1         : unsigned(7 downto 0);
  signal pixel_clock_inner : std_logic;
  signal bit_clock_counter : integer range 0 to 4;

  signal xord_data         : unsigned(8 downto 0);  -- either xor'd or xnor'd
                                                    -- data indicated by bit8
  signal xor_bit_counter   : integer range 0 to 7;  -- used in a later process

  signal xord_data_st_2    : unsigned(8 downto 0);
  signal acc_bias          : integer range 3 downto -4;  -- accumulated dc bias
  signal use_xnor_st_1     : boolean;

  signal new_bias          : integer range 4 downto -4; -- bias of xord_data_st_2
begin  -- architecture behave

  -- purpose: generate pixel clock
  -- type   : sequential
  -- inputs : bit_clock
  -- outputs: pixel_clock
  process (bit_clock, rst) is
  begin  -- process
    if rising_edge(bit_clock) then

      if rst = '1' then
        bit_clock_counter <= 0;
        pixel_clock_inner <= '0';
      elsif bit_clock_counter = 4 then
        bit_clock_counter <= 0;
        pixel_clock_inner <= not pixel_clock_inner;
      else
        bit_clock_counter <= bit_clock_counter + 1;
      end if;

    end if;
  end process;
  pixel_clock <= pixel_clock_inner;

---------------------------------------------------------------------------------------
  -- purpose: buffer input and count ones
  -- type   : sequential
  -- inputs : pixel_clock_inner, rst, data_in
  -- outputs: data_st_1
  process (pixel_clock_inner) is
  begin  -- process
    if rising_edge(pixel_clock_inner) then  -- rising clock edge

      if rst = '0' then                   -- asynchronous reset (active low)
        data_st_1 <= (others => '0');
      else
        data_st_1 <= data_in;
        use_xnor_st_1 <= ones_count(data_in) > 4 or (ones_count(data_in) = 4 and data_in(0) = '0');        
      end if;

    end if;
  end process;
---------------------------------------------------------------------------------------
  -- purpose: make xord_data
  make_xord_data: block is
  begin  -- block make_xord_data
    xord_data(0) <= data_st_1(0);
    make_mid_xord_data: for n in 1 to 7 generate
      xord_data(n) <= data_st_1(n) xnor xord_data(n-1) when use_xnor_st_1
                      else data_st_1(n) xor xord_data(n-1);
      --maybe later upgrade to : `data_in(n) xor xord_data(n-1) xor when use_xnor`
    end generate make_mid_xord_data;
    xord_data(8) <= '0' when use_xnor_st_1 else '1';
  end block make_xord_data;

  -- purpose: save xord_data
  -- type   : combinational
  -- inputs : pixel_clock_inner, xord_data
  -- outputs: xord_data_st_2
  process (pixel_clock_inner) is
  begin  -- process
    if rising_edge(pixel_clock_inner) then
      xord_data_st_2 <= xord_data;
    end if;
  end process;

---------------------------------------------------------------------------------------

  new_bias <= to_integer(ones_count(xord_data_st_2(7 downto 0))) - 4;
  
  -- purpose: messing with the bias stuff, generating the final symbol
  -- type   : combinational
  -- inputs : pixel_clock_inner, xord_data_st_2
  -- outputs: data_out
  process (pixel_clock_inner) is
  begin  -- process
    if rising_edge(pixel_clock_inner) then
      if rst = '1' then
        data_out <= (others => '0');
        acc_bias <= 0;
      elsif (acc_bias < 0) = (new_bias < 0) then
        data_out <= '1' & xord_data_st_2(8) & (not xord_data_st_2(7 downto 0));
        acc_bias <= acc_bias - new_bias;
      else
        data_out <= '0' & xord_data_st_2(8 downto 0);
        acc_bias <= acc_bias + new_bias;
      end if;
    end if;
  end process;
  
end architecture behave;
