OBJS :=  useful_functions.o TMDS_encoder.o TMDS_encoder_tb.o

all: graph

graph: TMDS_encoder_tb
	ghdl -r $< --vcd=clk_div.vcd --stop-time=1ms

TMDS_encoder_tb: $(OBJS)
	ghdl -e --std=08 $@
%.o: %.vhd
	ghdl -a --std=08 $<
clean:
	ghdl --clean
	rm *.o *.vcd -rf
TMDS_encoder.o: TMDS_encoder.vhd useful_functions.o 
	ghdl -a --std=08 $<

graph_show: graph
	gtkwave *.vcd & 2>/dev/null 3>/dev/null
