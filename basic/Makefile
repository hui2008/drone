CC ?= cc
CFLAGS ?= -g -Wall -Wextra -pedantic

TARGET := hello-world
SRC := main.c

.PHONY: all run clean

all: $(TARGET)

$(TARGET): $(SRC)
	mkdir -p build
	$(CC) $(CFLAGS) $(SRC) -o build/$(TARGET)

run: $(TARGET)
	./build/$(TARGET)

clean:
	rm -f build/$(TARGET)
