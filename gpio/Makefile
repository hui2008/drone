CC ?= cc
PKG_CONFIG ?= pkg-config

CFLAGS ?= -Wall -Wextra -Wpedantic
LDLIBS += $(shell $(PKG_CONFIG) --libs libgpiod)

TARGET := led
SRCS := main.c
OBJS := $(SRCS:.c=.o)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

%.o: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell $(PKG_CONFIG) --cflags libgpiod) -c $< -o $@

clean:
	$(RM) $(TARGET) $(OBJS)
