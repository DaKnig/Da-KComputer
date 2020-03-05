OBJS := TMDS_encoder.o

all: TMDS_encoder

graph: peak_detector_tb
	ghdl -r peak_detector_tb --vcd=clk_div.vcd --stop-time=100ms
	gtkwave *.vcd & 2>/dev/null 3>/dev/null
TMDS_encoder: $(OBJS)
	ghdl -e $@
%.o: %.vhd
	ghdl -a $<
clean:
	ghdl --clean
	rm *.vcd -rf
