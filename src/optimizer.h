#ifndef OPTIMIZER_H
#define OPTIMIZER_H

#include "simulation.h"
#include <vector>
#include <map>

/**
 * Clase para optimizar la configuración de servidores
 * Busca la asignación de 12 servidores que minimice el tiempo de espera
 */

struct ConfigResult {
    std::vector<int> config;           // Configuración [c1, c2, c3, c4, c5]
    double avgWaitTime;                 // Tiempo de espera promedio
    double stdDevWaitTime;              // Desviación estándar
    double avgUtilization;              // Utilización promedio
    int totalCustomers;
    
    bool operator<(const ConfigResult& other) const {
        return avgWaitTime < other.avgWaitTime;
    }
};

class ConfigOptimizer {
private:
    int totalServers;
    int numReplicas;
    std::vector<ConfigResult> results;
    
public:
    ConfigOptimizer(int totalServers = 12, int numReplicas = 30)
        : totalServers(totalServers), numReplicas(numReplicas) {}
    
    /**
     * Ejecuta búsqueda exhaustiva sobre todas las combinaciones válidas
     * y retorna la mejor configuración
     */
    ConfigResult findOptimalConfiguration();
    
    /**
     * Ejecuta múltiples réplicas de una configuración específica
     */
    ConfigResult evaluateConfiguration(const std::vector<int>& config);
    
    /**
     * Retorna los N mejores resultados
     */
    std::vector<ConfigResult> getTopResults(int n) const;
    
    /**
     * Imprime reporte de optimización
     */
    void printOptimizationReport() const;
    
    /**
     * Retorna todas las configuraciones evaluadas
     */
    const std::vector<ConfigResult>& getAllResults() const {
        return results;
    }
};

/**
 * Clase para análisis de sensibilidad
 * Evalúa cómo cambian las métricas con variaciones en parámetros
 */
class SensitivityAnalysis {
private:
    std::vector<int> baseConfig;
    
public:
    SensitivityAnalysis(const std::vector<int>& config) : baseConfig(config) {}
    
    /**
     * Analiza impacto de variar la tasa de llegadas
     */
    void analyzeArrivalRate(double minLambda, double maxLambda, int steps);
    
    /**
     * Analiza impacto de variar el número de servidores en una estación
     */
    void analyzeServerCount(int stationId, int minServers, int maxServers);
    
    /**
     * Imprime resultados de sensibilidad
     */
    void printResults() const;
};

/**
 * Clase para análisis de warm-up
 * Determina cuándo la simulación alcanza estado estacionario
 */
class WarmupAnalysis {
private:
    std::vector<int> config;
    
public:
    WarmupAnalysis(const std::vector<int>& config) : config(config) {}
    
    /**
     * Calcula métricas para diferentes períodos de warm-up
     * y encuentra el momento óptimo para comenzar mediciones
     */
    int findOptimalWarmupPeriod();
    
    /**
     * Imprime análisis de convergencia
     */
    void printConvergenceAnalysis() const;
};

#endif // OPTIMIZER_H
