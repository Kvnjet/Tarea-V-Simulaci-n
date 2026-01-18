#include "simulation.h"
#include <iostream>
#include <vector>

int main() {
    std::cout << "================================" << std::endl;
    std::cout << "Simulación de Sistema de Colas" << std::endl;
    std::cout << "Restaurante de Comida Rápida" << std::endl;
    std::cout << "================================" << std::endl << std::endl;
    
    // Configuración de servidores: [Cajas, Refrescos, Freidora, Postres, Pollo]
    // Total = 12 servidores
    std::vector<int> serverConfig = {3, 2, 2, 1, 4};
    
    // Validar que la suma sea 12
    int total = 0;
    for (int s : serverConfig) total += s;
    
    if (total != 12) {
        std::cerr << "Error: La suma de servidores debe ser 12, se obtuvo " << total << std::endl;
        return 1;
    }
    
    std::cout << "Configuración de servidores:" << std::endl;
    std::cout << "  - Cajas: " << serverConfig[0] << std::endl;
    std::cout << "  - Refrescos: " << serverConfig[1] << std::endl;
    std::cout << "  - Freidora: " << serverConfig[2] << std::endl;
    std::cout << "  - Postres: " << serverConfig[3] << std::endl;
    std::cout << "  - Pollo: " << serverConfig[4] << std::endl;
    std::cout << "  TOTAL: " << total << std::endl << std::endl;
    
    // Crear y ejecutar simulación
    QueueSimulation sim(serverConfig, 42);  // Seed = 42 para reproducibilidad
    
    sim.initialize();
    sim.run();
    sim.printResults();
    
    return 0;
}
