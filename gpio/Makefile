CC ?= cc
PKG_CONFIG ?= pkg-config

CFLAGS ?= -Wall -Wextra -Wpedantic
LDLIBS += $(shell $(PKG_CONFIG) --libs libgpiod)

BUILD := build
TARGET := $(BUILD)/led
SRCS := main.c
OBJS := $(addprefix $(BUILD)/,$(SRCS:.c=.o))

.PHONY: all clean

all: $(TARGET)

$(BUILD):
	mkdir -p $(BUILD)

$(TARGET): $(OBJS) | $(BUILD)
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(shell $(PKG_CONFIG) --cflags libgpiod) -c $< -o $@

clean:
	$(RM) -r $(BUILD)
