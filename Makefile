# Makefile para Simulación de Sistema de Colas

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
LDFLAGS = 

# Directorios
SRC_DIR = src
BUILD_DIR = build
BIN_DIR = bin

# Archivos fuente
SOURCES = $(SRC_DIR)/main.cpp $(SRC_DIR)/simulation.cpp
HEADERS = $(SRC_DIR)/simulation.h
OBJECTS = $(BUILD_DIR)/main.o $(BUILD_DIR)/simulation.o
TARGET = $(BIN_DIR)/simulation

# Compilación
all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -o $@ $^ $(LDFLAGS)
	@echo "✓ Compilación exitosa: $(TARGET)"

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp $(HEADERS)
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@
	@echo "✓ Compilado: $@"

# Ejecutar
run: $(TARGET)
	./$(TARGET)

# Limpiar
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
	@echo "✓ Directorios limpios"

# Compilar con depuración
debug: CXXFLAGS = -std=c++17 -Wall -Wextra -g -O0
debug: clean all

# Phony targets
.PHONY: all run clean debug
