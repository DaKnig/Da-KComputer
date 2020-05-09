TBS  := TMDS_encoder_tb HDMI_encoder_tb VGA_signal_generator_tb \
	top_level_video_test_tb

OBJS := vga_consts.o useful_functions.o TMDS_encoder.o HDMI_encoder.o\
	VGA_signal_generator.o top_level_video_test.o\
	$(TBS:=.o)

.SUFFIXES:
.PHONY: clean graph_show

all: graph

graph: TMDS_encoder_tb
	ghdl -r $< --vcd=$<.vcd --stop-time=500ns

$(TBS) : $(OBJS)
	ghdl -e --std=08 $@

%.o: src/%.vhd
	ghdl -a --std=08 $<

clean:
	ghdl --clean
	rm *.o *.vcd -rf

graph_show: graph
	gtkwave *.vcd & 2>/dev/null 3>/dev/null
