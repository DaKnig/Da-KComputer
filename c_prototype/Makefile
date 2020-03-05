SRCDIR := src
BINDIR := bin
OBJS := main.o putpixel.o
CFLAGS := -Og -ggdb -Wall -Wextra -Wshadow -Wcast-qual \
          -Wstrict-aliasing=1 -Wswitch-enum -Wstrict-prototypes \
	  -Wundef -Wpointer-arith -Wformat-security -Winit-self \
	  -Wwrite-strings -Wredundant-decls -Wno-unused -Werror \
#	  -fsanitize=address
LIBS := $(shell sdl2-config --cflags --libs) -lm

CC ?= gcc

all: $(BINDIR)/main #unit-tests

memtest: $(BINDIR)/main
	valgrind --tool=memcheck --leak-check=full --show-leak-kinds=all -v $<

$(BINDIR)/main: $(OBJS) Makefile
	$(CC) $(LIBS) $(CFLAGS) -o $@ $(OBJS) $(LIBS)

%.o: $(SRCDIR)/%.c
	$(CC) $(LIBS) $(CFLAGS) -c -o $@ $<

.PHONY: clean memtest run

clean:
	rm -f *.o
	rm -f main
	rm -f bin/*
run:$(BINDIR)/main
	$(BINDIR)/main
