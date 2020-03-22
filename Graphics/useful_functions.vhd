library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package useful_functions is
  function ones_count (
    data : unsigned)               -- data input
    return unsigned;
end package;


package body useful_functions is

  -- purpose: count the number of ones in an unsigned number
  function ones_count (
    data : unsigned)
    return unsigned is
    variable no1s : integer range 0 to 5 := 0;
  begin  -- function ones_count

    if data'length < 5 then
--      report to_string(std_logic_vector(data));
      no1s := 0;
      for d in data'range loop
        if data(d) = '1' then
          no1s := no1s + 1;
        end if;
      end loop;  -- d

      return to_unsigned(no1s, 3);

    else

      return ones_count(data(data'length/2 downto 0)) +
             ones_count(
               data(data'length-1 downto data'length-data'length/2));

    end if;

  end function ones_count;

end useful_functions;
