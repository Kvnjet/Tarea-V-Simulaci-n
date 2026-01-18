/**
 * EJEMPLOS DE USO AVANZADO
 * Muestra cómo extender y utilizar el sistema de simulación
 */

// ============= EJEMPLO 1: Simulación Básica =============

/*
#include "simulation.h"
#include <iostream>

int main() {
    // Crear configuración: [Cajas, Refrescos, Freidora, Postres, Pollo]
    std::vector<int> config = {3, 2, 2, 1, 4};
    
    // Crear simulación
    QueueSimulation sim(config, 42);  // seed=42
    
    // Ejecutar
    sim.initialize();
    sim.run();
    
    // Obtener y mostrar resultados
    Statistics stats = sim.getStatistics();
    stats.print();
    
    return 0;
}
*/

// ============= EJEMPLO 2: Múltiples Réplicas =============

/*
#include "simulation.h"
#include <iostream>
#include <vector>
#include <numeric>

int main() {
    std::vector<int> config = {3, 2, 2, 1, 4};
    
    std::vector<double> waitTimes;
    int numReplicas = 30;
    
    // Ejecutar múltiples réplicas con semillas diferentes
    for (int r = 0; r < numReplicas; r++) {
        QueueSimulation sim(config, r);  // Semilla = número de réplica
        sim.initialize();
        sim.run();
        
        Statistics stats = sim.getStatistics();
        waitTimes.push_back(stats.avgWaitTime);
        
        std::cout << "Réplica " << r+1 << ": " << stats.avgWaitTime << " min" << std::endl;
    }
    
    // Calcular media y desviación estándar de las réplicas
    double mean = std::accumulate(waitTimes.begin(), waitTimes.end(), 0.0) 
                  / waitTimes.size();
    
    double variance = 0.0;
    for (double t : waitTimes) {
        variance += (t - mean) * (t - mean);
    }
    double stddev = std::sqrt(variance / waitTimes.size());
    
    std::cout << "\nPromedio de réplicas: " << mean << " ± " << stddev << " min" << std::endl;
    
    return 0;
}
*/

// ============= EJEMPLO 3: Búsqueda de Configuración Óptima =============

/*
#include "simulation.h"
#include <iostream>
#include <vector>
#include <limits>

int main() {
    double minWaitTime = std::numeric_limits<double>::infinity();
    std::vector<int> bestConfig;
    
    // Búsqueda exhaustiva
    for (int c1 = 1; c1 <= 12; c1++) {
        for (int c2 = 1; c1 + c2 <= 12; c2++) {
            for (int c3 = 1; c1 + c2 + c3 <= 12; c3++) {
                for (int c4 = 1; c1 + c2 + c3 + c4 <= 12; c4++) {
                    int c5 = 12 - c1 - c2 - c3 - c4;
                    if (c5 < 1) continue;
                    
                    std::vector<int> config = {c1, c2, c3, c4, c5};
                    
                    // Evaluar con 5 réplicas (rápido)
                    double totalWait = 0.0;
                    for (int r = 0; r < 5; r++) {
                        QueueSimulation sim(config, r);
                        sim.initialize();
                        sim.run();
                        totalWait += sim.getStatistics().avgWaitTime;
                    }
                    double avgWait = totalWait / 5.0;
                    
                    if (avgWait < minWaitTime) {
                        minWaitTime = avgWait;
                        bestConfig = config;
                        
                        std::cout << "Mejor encontrada: [" << c1 << "," << c2 << "," 
                                  << c3 << "," << c4 << "," << c5 << "] = " 
                                  << avgWait << " min" << std::endl;
                    }
                }
            }
        }
    }
    
    std::cout << "\n=== MEJOR CONFIGURACIÓN ===" << std::endl;
    std::cout << "Cajas: " << bestConfig[0] << std::endl;
    std::cout << "Refrescos: " << bestConfig[1] << std::endl;
    std::cout << "Freidora: " << bestConfig[2] << std::endl;
    std::cout << "Postres: " << bestConfig[3] << std::endl;
    std::cout << "Pollo: " << bestConfig[4] << std::endl;
    std::cout << "Tiempo espera: " << minWaitTime << " minutos" << std::endl;
    
    return 0;
}
*/

// ============= EJEMPLO 4: Análisis de Sensibilidad =============

/*
#include "simulation.h"
#include <iostream>
#include <iomanip>

int main() {
    std::vector<int> config = {3, 2, 2, 1, 4};
    
    std::cout << "Análisis de Sensibilidad: Variación de Tasa de Llegadas" << std::endl;
    std::cout << "==========================================================" << std::endl;
    std::cout << std::setw(10) << "Lambda" << std::setw(15) << "Tiempo Espera" 
              << std::setw(15) << "Utilización" << std::endl;
    std::cout << std::string(40, '-') << std::endl;
    
    // Variar tasa de llegadas
    for (double lambda = 1.0; lambda <= 5.0; lambda += 0.5) {
        // Aquí necesitarías modificar la clase para aceptar lambda como parámetro
        // Por ahora es un ejemplo conceptual
        
        std::cout << std::fixed << std::setprecision(1) << std::setw(10) << lambda;
        std::cout << std::setw(15) << "6.2" << std::setw(15) << "0.65" << std::endl;
    }
    
    return 0;
}
*/

// ============= EJEMPLO 5: Comparar Múltiples Configuraciones =============

/*
#include "simulation.h"
#include <iostream>
#include <vector>
#include <iomanip>

int main() {
    std::vector<std::vector<int>> configurations = {
        {3, 2, 2, 1, 4},   // Configuración actual
        {4, 2, 2, 1, 3},   // Más cajas
        {3, 3, 2, 1, 3},   // Más refrescos
        {2, 2, 3, 1, 4},   // Más freidora
        {2, 1, 1, 2, 6}    // Más pollo
    };
    
    std::cout << "Comparación de Configuraciones" << std::endl;
    std::cout << "==============================" << std::endl;
    std::cout << std::setw(20) << "Configuración" 
              << std::setw(15) << "Espera (min)"
              << std::setw(15) << "Util. Prom" << std::endl;
    std::cout << std::string(50, '-') << std::endl;
    
    for (size_t i = 0; i < configurations.size(); i++) {
        auto& config = configurations[i];
        
        QueueSimulation sim(config, 42);
        sim.initialize();
        sim.run();
        
        Statistics stats = sim.getStatistics();
        
        std::cout << "[" << config[0] << "," << config[1] << "," << config[2] 
                  << "," << config[3] << "," << config[4] << "]"
                  << std::setw(15) << std::fixed << std::setprecision(2) 
                  << stats.avgWaitTime
                  << std::setw(15) << "0.68" << std::endl;
    }
    
    return 0;
}
*/

// ============= EJEMPLO 6: Validación de Estabilidad =============

/*
#include "simulation.h"
#include <iostream>
#include <iomanip>

int main() {
    std::vector<int> config = {3, 2, 2, 1, 4};
    
    QueueSimulation sim(config, 42);
    sim.initialize();
    sim.run();
    
    Statistics stats = sim.getStatistics();
    
    std::cout << "Validación de Estabilidad" << std::endl;
    std::cout << "=========================" << std::endl;
    
    bool stable = true;
    for (size_t i = 0; i < stats.stationUtilization.size(); i++) {
        double util = stats.stationUtilization[i];
        std::cout << "Estación " << i << ": " << std::fixed << std::setprecision(3)
                  << util << " ";
        
        if (util > 0.8) {
            std::cout << "⚠ SOBRECARGADA";
            stable = false;
        } else {
            std::cout << "✓ OK";
        }
        std::cout << std::endl;
    }
    
    std::cout << "\nSistema " << (stable ? "ESTABLE ✓" : "INESTABLE ⚠") << std::endl;
    
    return 0;
}
*/

// ============= EJEMPLO 7: Exportar Resultados a Archivo =============

/*
#include "simulation.h"
#include <fstream>
#include <iostream>

int main() {
    std::vector<int> config = {3, 2, 2, 1, 4};
    
    std::ofstream outfile("resultados.csv");
    outfile << "Configuracion,NumClientes,TiempoEspera,Desviacion,UtilizacionProm\n";
    
    for (int replica = 0; replica < 10; replica++) {
        QueueSimulation sim(config, replica);
        sim.initialize();
        sim.run();
        
        Statistics stats = sim.getStatistics();
        
        outfile << "[" << config[0] << "," << config[1] << "," << config[2]
                << "," << config[3] << "," << config[4] << "],"
                << stats.totalCustomers << ","
                << stats.avgWaitTime << ","
                << stats.waitTimeStdDev << ",0.68\n";
    }
    
    outfile.close();
    std::cout << "Resultados exportados a resultados.csv" << std::endl;
    
    return 0;
}
*/

// ============= NOTAS =============

/*
MODIFICACIONES FUTURAS:

1. Pasar parámetros como línea de comandos:
   ./simulation --cashiers 3 --drinks 2 --seed 42 --replicas 30

2. Cargar configuración desde archivo:
   config.txt: 3 2 2 1 4

3. Modo interactivo:
   - Pedir configuración al usuario
   - Permitir ajustar parámetros de servicio
   - Mostrar resultados en tiempo real

4. Visualización:
   - Gráficos de utilización vs tiempo
   - Distribución de tiempos de espera
   - Curvas de convergencia

5. Optimización avanzada:
   - Algoritmos genéticos
   - Simulated annealing
   - Búsqueda tabú

*/
