library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.useful_functions.all;

entity TMDS_encoder is

  port (
    data_in     : in  unsigned(7 downto 0);  -- parallel data in
                                             -- clocked at the pixel clock
    data_out    : out unsigned(9 downto 0);

    rst         : in  std_logic;  -- reset the state of the encoder, used for
                                  -- synch or something
    pix_clk     : in std_logic;   -- pixel clock, 25MHz
    hsync,vsync : in std_logic;
    active      : in boolean);

end entity TMDS_encoder;

architecture behave of TMDS_encoder is

  signal data_st_1         : unsigned(7 downto 0);

  signal xord_data         : unsigned(8 downto 0); -- either xor'd or xnor'd
                                                   -- data indicated by bit8
  signal xor_bit_counter   : integer range 0 to 7; -- used in a later process

  signal xord_data_st_2    : unsigned(8 downto 0);
  signal acc_bias          : integer range 3 downto -4;-- accumulated dc bias
  signal use_xnor_st_1     : boolean;

  signal new_bias          : integer range 4 downto -4; -- bias of xord_data_st_2

  signal debug_ones_count  : unsigned(3 downto 0);

  type TMDS_ctrl_sr_t is array (1 downto 0) of unsigned(1 downto 0);
  signal TMDS_ctrl_sr : TMDS_ctrl_sr_t;

  type bool_sr_t is array (1 downto 0) of boolean;
  signal active_sr : bool_sr_t;

begin  -- architecture behave

  -- purpose: shifting all the relevant inputs across the shift registers
  -- type   : combinational
  -- inputs : bit_clk
  -- outputs:
  shift_reg_update: process (pix_clk) is
  begin  -- process shift_reg_update
    if rising_edge(pix_clk) then
      TMDS_ctrl_sr <= TMDS_ctrl_sr(0 downto 0) & (vsync&hsync);
      active_sr <= active_sr(0 downto 0) & (active);
    end if;
  end process shift_reg_update;

---------------------------------------------------------------------------------------
  -- purpose: buffer input and count ones
  -- type   : sequential
  -- inputs : bit_clk, data_in
  -- outputs: data_st_1, use_xnor_st_1
  process (pix_clk) is
  begin  -- process
    if rising_edge(pix_clk) then
      data_st_1 <= data_in;
      debug_ones_count <= ones_count(data_in);
      use_xnor_st_1 <= ones_count(data_in) > 4
                       or (ones_count(data_in) = 4 and data_in(0) = '0');
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
  -- inputs : bit_clk, xord_data
  -- outputs: xord_data_st_2
  process (pix_clk) is
    variable xord_data_v : unsigned(8 downto 0) := 9x"000";
  begin  -- process
    if rising_edge(pix_clk) then
      xord_data_v(0) := data_st_1(0);
      for i in 1 to 7 loop
        if use_xnor_st_1 then
          xord_data_v(i) := data_st_1(i) xnor xord_data_v(i-1);
        else
          xord_data_v(i) := data_st_1(i) xor  xord_data_v(i-1);
        end if;
      end loop;  -- i
      xord_data_v(8) := '0' when use_xnor_st_1 else '1';
      xord_data_st_2 <= xord_data_v;

      assert xord_data = xord_data_v;
    end if;
  end process;

---------------------------------------------------------------------------------------

  new_bias <= to_integer(ones_count(xord_data_st_2(7 downto 0))) - 4;

  -- purpose: messing with the bias stuff, generating the final symbol
  -- type   : combinational
  -- inputs : bit_clk, xord_data_st_2
  -- outputs: data_out
  process (pix_clk) is
  begin  -- process
    if rising_edge(pix_clk) then
      if rst = '1' then
        data_out <= (others => '0');
        acc_bias <= 0;
      elsif not active_sr(1) then
        case TMDS_ctrl_sr(1) is
          when "00" => data_out <= "1101010100";
          when "01" => data_out <= "0010101011";
          when "10" => data_out <= "0101010100";
          when "11" => data_out <= "1010101011";
          when others => null;
        end case;
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
