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
    variable no1s : integer range 0 to data'length := 0;
  begin  -- function ones_count

    for d in data'range loop
      if data(d) = '1' then
        no1s := no1s + 1;
      end if;
    end loop;  -- d

    return to_unsigned(no1s, 3);

  end function ones_count;

end useful_functions;
