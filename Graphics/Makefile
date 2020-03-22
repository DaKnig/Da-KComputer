OBJS :=  useful_functions.o TMDS_encoder.o TMDS_encoder_tb.o

all: TMDS_encoder_tb

graph: TMDS_encoder_tb
	ghdl -r $< --vcd=clk_div.vcd --stop-time=1ms
	gtkwave *.vcd & 2>/dev/null 3>/dev/null
TMDS_encoder_tb: $(OBJS)
	ghdl -e --std=08 $@
%.o: %.vhd
	ghdl -a --std=08 $<
clean:
	ghdl --clean
	rm *.vcd -rf
