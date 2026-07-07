# Makefile for DCA Chapter 1 Verification Code
# Author: Wang Bingqin
# Date: 2026-07-06

CC = gcc
CFLAGS = -Wall -Wextra -O2 -std=c99
TARGET = verify_arithmetic
SOURCE = verify_arithmetic.c

.PHONY: all clean run test

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CC) $(CFLAGS) -o $(TARGET) $(SOURCE)

run: $(TARGET)
	./$(TARGET)

test: $(TARGET)
	@echo "Running C verification tests..."
	./$(TARGET)
	@echo ""
	@echo "Running Python verification tests..."
	python3 verify_arithmetic.py

clean:
	rm -f $(TARGET) *.o

# Install check (optional)
install-check:
	@echo "Checking dependencies..."
	@which gcc > /dev/null || echo "gcc not found. Please install gcc."
	@which python3 > /dev/null || echo "python3 not found. Please install python3."

help:
	@echo "Available targets:"
	@echo "  all       - Build the C verification program (default)"
	@echo "  run       - Build and run the C verification program"
	@echo "  test      - Run both C and Python verification tests"
	@echo "  clean     - Remove built files"
	@echo "  help      - Show this help message"