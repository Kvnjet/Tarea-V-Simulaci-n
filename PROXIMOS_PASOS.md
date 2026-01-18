# PRÓXIMOS PASOS - Guía de Continuación

## 🎯 Objetivo General
Completar la simulación de colas con optimización y análisis múltiples réplicas.

## 📋 Tareas Pendientes (En Orden de Prioridad)

### 1️⃣ INSTALAR COMPILADOR C++ (Requisito previo)

**Si aún no tienes g++ instalado:**

Ver archivo: [INSTALACION.md](INSTALACION.md)

Opciones rápidas:
- **Windows**: Descargar MinGW-w64 desde mingw-w64.org
- **Linux**: `sudo apt install build-essential`
- **Mac**: `brew install gcc` (con Homebrew)

Verificar:
```bash
g++ --version
```

---

### 2️⃣ COMPILAR EL PROYECTO

Una vez tengas compilador:

```bash
cd "C:\Users\kvnes\OneDrive\Documentos\GitHub\Tarea-V-Simulaci-n"
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation.exe
bin\simulation.exe
```

Deberías ver una salida como:
```
================================
Simulación de Sistema de Colas
Restaurante de Comida Rápida
================================

Configuración de servidores:
  - Cajas: 3
  - Refrescos: 2
  ...

Clientes procesados: 1425
Tiempo de espera promedio: 6.24 minutos
...
```

---

### 3️⃣ IMPLEMENTAR MÚLTIPLES RÉPLICAS

**Archivo a modificar**: `src/main.cpp`

**Cambiar de:**
```cpp
int main() {
    std::vector<int> config = {3, 2, 2, 1, 4};
    QueueSimulation sim(config, 42);
    sim.initialize();
    sim.run();
    sim.printResults();
    return 0;
}
```

**Cambiar a:**
```cpp
#include <numeric>
#include <cmath>

int main() {
    std::vector<int> config = {3, 2, 2, 1, 4};
    int numReplicas = 30;
    
    std::vector<double> waitTimes;
    std::vector<int> customerCounts;
    
    for (int r = 0; r < numReplicas; r++) {
        QueueSimulation sim(config, r);  // Semilla = r
        sim.initialize();
        sim.run();
        
        Statistics stats = sim.getStatistics();
        waitTimes.push_back(stats.avgWaitTime);
        customerCounts.push_back(stats.totalCustomers);
    }
    
    // Calcular media y desviación
    double meanWait = std::accumulate(waitTimes.begin(), 
                                      waitTimes.end(), 0.0) / numReplicas;
    
    double variance = 0.0;
    for (double w : waitTimes) {
        variance += (w - meanWait) * (w - meanWait);
    }
    double stdDev = std::sqrt(variance / numReplicas);
    
    std::cout << "\n=== PROMEDIO DE " << numReplicas << " RÉPLICAS ===" << std::endl;
    std::cout << "Tiempo de espera: " << meanWait << " ± " << stdDev << " min" << std::endl;
    
    return 0;
}
```

---

### 4️⃣ IMPLEMENTAR BÚSQUEDA DE CONFIGURACIÓN ÓPTIMA

**Crear archivo**: `src/optimizer_impl.cpp`

```cpp
#include "simulation.h"
#include <iostream>
#include <vector>
#include <limits>
#include <iomanip>

struct ConfigResult {
    std::vector<int> config;
    double avgWaitTime;
};

ConfigResult evaluateConfig(const std::vector<int>& config, int replicas) {
    double totalWait = 0.0;
    
    for (int r = 0; r < replicas; r++) {
        QueueSimulation sim(config, r);
        sim.initialize();
        sim.run();
        totalWait += sim.getStatistics().avgWaitTime;
    }
    
    return {config, totalWait / replicas};
}

int main() {
    double minWaitTime = std::numeric_limits<double>::infinity();
    std::vector<int> bestConfig;
    
    std::cout << "Buscando configuración óptima..." << std::endl;
    std::cout << "Esto puede tomar varios minutos..." << std::endl << std::endl;
    
    int iterations = 0;
    
    // Búsqueda exhaustiva
    for (int c1 = 1; c1 <= 12; c1++) {
        for (int c2 = 1; c1 + c2 <= 12; c2++) {
            for (int c3 = 1; c1 + c2 + c3 <= 12; c3++) {
                for (int c4 = 1; c1 + c2 + c3 + c4 <= 12; c4++) {
                    int c5 = 12 - c1 - c2 - c3 - c4;
                    if (c5 < 1) continue;
                    
                    std::vector<int> config = {c1, c2, c3, c4, c5};
                    ConfigResult result = evaluateConfig(config, 5);  // 5 réplicas rápidas
                    
                    iterations++;
                    if (iterations % 50 == 0) {
                        std::cout << "Evaluadas " << iterations << " configuraciones..." << std::endl;
                    }
                    
                    if (result.avgWaitTime < minWaitTime) {
                        minWaitTime = result.avgWaitTime;
                        bestConfig = config;
                        
                        std::cout << "✓ Nueva mejor: [" << c1 << "," << c2 << "," 
                                  << c3 << "," << c4 << "," << c5 << "] = " 
                                  << std::fixed << std::setprecision(2)
                                  << minWaitTime << " min" << std::endl;
                    }
                }
            }
        }
    }
    
    std::cout << "\n=== CONFIGURACIÓN ÓPTIMA ===" << std::endl;
    std::cout << "Cajas: " << bestConfig[0] << std::endl;
    std::cout << "Refrescos: " << bestConfig[1] << std::endl;
    std::cout << "Freidora: " << bestConfig[2] << std::endl;
    std::cout << "Postres: " << bestConfig[3] << std::endl;
    std::cout << "Pollo: " << bestConfig[4] << std::endl;
    std::cout << "Tiempo de espera: " << minWaitTime << " minutos" << std::endl;
    
    return 0;
}
```

Compilar:
```bash
g++ -std=c++17 -O3 src/optimizer_impl.cpp src/simulation.cpp -o bin/optimizer.exe
bin\optimizer.exe
```

---

### 5️⃣ IMPLEMENTAR ANÁLISIS DE WARM-UP

**Crear función en**: `src/simulation.cpp`

```cpp
void analyzeWarmupPeriod(const std::vector<int>& config) {
    std::cout << "\n=== Análisis de Warm-up ===" << std::endl;
    std::cout << std::setw(15) << "Minutos"
              << std::setw(15) << "Espera (min)"
              << std::setw(15) << "Clientes" << std::endl;
    std::cout << std::string(45, '-') << std::endl;
    
    // Modificar QueueSimulation para permitir warm-up
    // (Requiere cambios en la clase)
    
    for (int warmup = 0; warmup <= 120; warmup += 20) {
        // Ejecutar simulación con warm-up
        // Registrar estadísticas
    }
}
```

---

### 6️⃣ VALIDAR ESTABILIDAD

**Añadir a main.cpp:**

```cpp
bool validateStability(const Statistics& stats) {
    bool stable = true;
    
    std::cout << "\nValidación de Estabilidad:" << std::endl;
    std::cout << std::string(40, '-') << std::endl;
    
    for (size_t i = 0; i < stats.stationUtilization.size(); i++) {
        double util = stats.stationUtilization[i];
        std::cout << "Estación " << i << ": " 
                  << std::fixed << std::setprecision(3) << (util * 100)
                  << "% ";
        
        if (util > 0.8) {
            std::cout << "⚠ SOBRECARGADA";
            stable = false;
        } else {
            std::cout << "✓ OK";
        }
        std::cout << std::endl;
    }
    
    return stable;
}
```

---

### 7️⃣ EXPORTAR RESULTADOS A CSV

**Añadir función:**

```cpp
void exportResultsToCSV(const std::string& filename,
                        const std::vector<int>& config,
                        const Statistics& stats) {
    std::ofstream file(filename, std::ios::app);
    
    file << config[0] << ","
         << config[1] << ","
         << config[2] << ","
         << config[3] << ","
         << config[4] << ","
         << stats.totalCustomers << ","
         << std::fixed << std::setprecision(2) << stats.avgWaitTime << ","
         << stats.waitTimeStdDev << "\n";
    
    file.close();
}
```

---

## 📊 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

1. ✅ Esqueleto base (YA COMPLETADO)
2. ⏭️ Instalar compilador
3. ⏭️ Compilar y ejecutar versión simple
4. ⏭️ Múltiples réplicas (prioridad alta)
5. ⏭️ Búsqueda de configuración
6. ⏭️ Validación de estabilidad
7. ⏭️ Análisis de warm-up
8. ⏭️ Exportación de datos
9. ⏭️ Documentar resultados

---

## 🧪 PRUEBAS SUGERIDAS

### Prueba 1: Configuración Actual
```bash
bin\simulation.exe
# Verificar que funciona y da resultados razonables
```

### Prueba 2: Múltiples Réplicas
```bash
# Ejecutar main.cpp modificado
# Verificar convergencia de resultados
```

### Prueba 3: Comparar Configuraciones
```cpp
configs = [
    {3, 2, 2, 1, 4},   // Actual
    {4, 2, 2, 1, 3},   // +Cajas
    {3, 3, 2, 1, 3},   // +Refrescos
]
// Comparar resultados
```

---

## 📚 REFERENCIA DE ARCHIVOS

| Archivo | Contenido | Última Modificación |
|---------|-----------|-------------------|
| README.md | Instrucciones generales | ✓ |
| INSTALACION.md | Instalar compilador | ✓ |
| ARQUITECTURA.md | Diseño del sistema | ✓ |
| REFERENCIA.md | APIs y clases | ✓ |
| EJEMPLOS_USO.cpp | Ejemplos de código | ✓ |
| DIAGRAMA.txt | Visualización | ✓ |
| PROYECTO_COMPLETO.md | Resumen | ✓ |
| src/simulation.h | Headers | ✓ |
| src/simulation.cpp | Implementación | ✓ |
| src/config.h | Configuración | ✓ |
| src/main.cpp | Punto de entrada | ⏳ Será modificado |

---

## ⚡ TIPS DE OPTIMIZACIÓN

### Compilación Rápida
```bash
g++ -std=c++17 -O3 -march=native src/main.cpp src/simulation.cpp -o bin/sim
```

### Depuración
```bash
g++ -std=c++17 -g -O0 src/main.cpp src/simulation.cpp -o bin/sim_debug
gdb bin/sim_debug
```

### Paralelización (Futuro)
```cpp
#pragma omp parallel for
for (int r = 0; r < numReplicas; r++) {
    // Ejecutar réplicas en paralelo
}
```

---

## 🎓 CRITERIOS DE ÉXITO

✓ Compilación sin errores  
✓ Resultados estadísticamente válidos  
✓ Utilización < 0.8 en todas las estaciones  
✓ Tiempo de espera > 0  
✓ Configuración óptima encontrada  
✓ Documentación completa  

---

## 📞 TROUBLESHOOTING

**Error: "g++ no se reconoce"**
→ Ver INSTALACION.md

**Error: "#include <random> not found"**
→ Usar `-std=c++17` al compilar

**Resultados erráticos**
→ Aumentar NUM_REPLICAS a 30+

**Ejecución muy lenta**
→ Usar `-O3` en compilación

---

**Estado**: Listo para continuar  
**Próximo**: Instalar compilador C++  
**Tiempo estimado**: 2-3 horas para completar

¡Buena suerte! 🚀
