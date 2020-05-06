OBJS :=  useful_functions.o TMDS_encoder.o TMDS_encoder_tb.o HDMI_encoder.o \
	HDMI_encoder_tb.o

TBS  := TMDS_encoder_tb HDMI_encoder_tb

all: graph

graph: TMDS_encoder_tb
	ghdl -r $< --vcd=clk_div.vcd --stop-time=500ns

$(TBS) : $(OBJS)
	ghdl -e --std=08 $@
%.o: src/%.vhd
	ghdl -a --std=08 $<
clean:
	ghdl --clean
	rm *.o *.vcd -rf

graph_show: graph
	gtkwave *.vcd & 2>/dev/null 3>/dev/null
