# PMFG Algorithm Makefile
# Author: Eduardo-zampirolli
# Project: Complex Networks in Economy
# Working Directory: /home/edu/Documents/Complex-Networks-in-Economy
# OGDF Directory: /home/edu/ogdf

# Compiler and flags
CXX = g++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -g
TARGET = teste3
SRCDIR = .
BUILDDIR = build

# OGDF paths - Fixed for your specific installation
OGDF_ROOT = /home/edu/ogdf
OGDF_INCLUDE = $(OGDF_ROOT)/include
OGDF_BUILD = $(OGDF_ROOT)/build
OGDF_CFLAGS = -I$(OGDF_INCLUDE)
OGDF_LIBS = -L$(OGDF_BUILD) -logdf -lpthread -lm

# Source files
SOURCES = teste3.c
OBJECTS = $(BUILDDIR)/teste3.o

# Default target
all: check-ogdf $(TARGET)

# Create build directory
$(BUILDDIR):
	mkdir -p $(BUILDDIR)

# Check OGDF installation
check-ogdf:
	@echo "=== Checking OGDF Installation ==="
	@echo "OGDF Root: $(OGDF_ROOT)"
	@echo "OGDF Include: $(OGDF_INCLUDE)"
	@echo "OGDF Build: $(OGDF_BUILD)"
	@test -d $(OGDF_ROOT) || (echo "❌ OGDF directory not found at $(OGDF_ROOT)" && exit 1)
	@test -d $(OGDF_INCLUDE) || (echo "❌ OGDF include directory not found" && exit 1)
	@test -f $(OGDF_INCLUDE)/ogdf/decomposition/DynamicPlanarSPQRTree.h || (echo "❌ DynamicPlanarSPQRTree.h not found" && echo "Available SPQR files:" && find $(OGDF_INCLUDE) -name "*SPQR*" 2>/dev/null || echo "None found" && exit 1)
	@test -f $(OGDF_BUILD)/libogdf.so || test -f $(OGDF_BUILD)/libogdf.a || (echo "❌ OGDF library not found in $(OGDF_BUILD)" && echo "Available libraries:" && find $(OGDF_ROOT) -name "libogdf*" 2>/dev/null || echo "None found" && echo "" && echo "Run 'make build-ogdf' to build OGDF" && exit 1)
	@echo "✅ OGDF installation OK"

# Compile object files
$(BUILDDIR)/%.o: $(SRCDIR)/%.c | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $(OGDF_CFLAGS) -c $< -o $@

# Link executable
$(TARGET): $(OBJECTS)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $@ $(OGDF_LIBS)
	@echo "✅ Compilation successful!"
	@echo "Executable: $(TARGET)"

# Build OGDF properly
build-ogdf:
	@echo "=== Building OGDF ==="
	cd $(OGDF_ROOT) && \
	rm -rf build CMakeCache.txt && \
	mkdir -p build && \
	cd build && \
	cmake .. -DCMAKE_BUILD_TYPE=Release && \
	make -j$(shell nproc)
	@echo ""
	@echo "✅ OGDF build completed!"
	@echo "Checking for library files..."
	@find $(OGDF_ROOT) -name "libogdf*" -type f || echo "No library files found"

# Quick OGDF status
ogdf-status:
	@echo "=== OGDF Status ==="
	@echo "Directory exists: $(shell test -d $(OGDF_ROOT) && echo YES || echo NO)"
	@echo "Include exists: $(shell test -d $(OGDF_INCLUDE) && echo YES || echo NO)"
	@echo "Build dir exists: $(shell test -d $(OGDF_BUILD) && echo YES || echo NO)"
	@echo "Library files found:"
	@find $(OGDF_ROOT) -name "libogdf*" -type f 2>/dev/null || echo "  None found"
	@echo "SPQR header exists: $(shell test -f $(OGDF_INCLUDE)/ogdf/decomposition/DynamicPlanarSPQRTree.h && echo YES || echo NO)"

# Clean build files
clean:
	rm -rf $(BUILDDIR) $(TARGET)

# Run the program
run: $(TARGET)
	./$(TARGET)

# Debug build
debug: CXXFLAGS += -DDEBUG -g3 -O0
debug: clean $(TARGET)

# Test compilation without running
test-compile: clean
	@echo "Testing compilation only..."
	$(MAKE) $(TARGET)
	@echo "✅ Compilation test successful!"

# Show current working directory and paths
info:
	@echo "=== Environment Information ==="
	@echo "Current directory: $(shell pwd)"
	@echo "User: $(shell whoami)"
	@echo "Compiler: $(CXX)"
	@echo "Flags: $(CXXFLAGS)"
	@echo "OGDF Root: $(OGDF_ROOT)"
	@echo "OGDF Include: $(OGDF_INCLUDE)"
	@echo "OGDF Build: $(OGDF_BUILD)"
	@echo "OGDF CFLAGS: $(OGDF_CFLAGS)"
	@echo "OGDF LIBS: $(OGDF_LIBS)"
	@echo "Source files: $(SOURCES)"
	@echo "Target: $(TARGET)"

# Help
help:
	@echo "=== PMFG Algorithm Makefile ==="
	@echo "Eduardo Zampirolli - Complex Networks in Economy"
	@echo ""
	@echo "Available targets:"
	@echo "  all           - Build the PMFG algorithm (default)"
	@echo "  build-ogdf    - Build OGDF from source"
	@echo "  ogdf-status   - Check OGDF installation status"
	@echo "  test-compile  - Test compilation without running"
	@echo "  clean         - Remove build files and executable"
	@echo "  run           - Build and run the program"
	@echo "  debug         - Build with debug symbols"
	@echo "  info          - Show environment information"
	@echo "  help          - Show this help message"

.PHONY: all clean run debug build-ogdf ogdf-status test-compile info help

