# Referencia Rápida - Sistema de Simulación de Colas

## Estructura de Carpetas

```
Tarea-V-Simulación/
├── Instrucciones/
│   └── queue_simulation_guide.md
├── src/
│   ├── main.cpp
│   ├── simulation.h
│   ├── simulation.cpp
│   ├── config.h
│   └── optimizer.h
├── build/          (creado al compilar)
├── bin/            (creado al compilar)
├── Makefile
├── compile.bat
├── README.md
├── INSTALACION.md
├── ARQUITECTURA.md
├── EJEMPLOS_USO.cpp
└── REFERENCIA.md   (este archivo)
```

## Compilación Rápida

### Windows (con g++ instalado)
```bash
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation.exe
bin\simulation.exe
```

### Linux/Mac
```bash
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation
./bin/simulation
```

### Con Make
```bash
make      # Compilar
make run  # Compilar y ejecutar
make clean # Limpiar
```

## Clases Principales

### `RandomGenerators`
Genera números aleatorios con diferentes distribuciones:
```cpp
RandomGenerators rng(seed);

rng.exponentialInterarrival(lambda);    // λ = 3
rng.exponentialService(mu);              // μ = 0.4
rng.normalDiscreteService(mean, stddev); // mean=3, stddev=0.5
rng.binomialService(n, p);               // n=5, p=0.6
rng.geometricService(p);                 // p=0.1
rng.numOrders();                         // Binomial(5, 0.4)
rng.shouldVisit(probability);            // p=0.9, 0.7, 0.25, 0.3
```

### `Station`
Representa una estación con cola y múltiples servidores:
```cpp
Station station(id, numServers);

station.addCustomer(customer);           // Agregar a cola
station.hasAvailableServer();             // ¿Hay servidor?
station.getQueueLength();                 // Largo de cola
station.getUtilization(simTime);          // ρ = uso/capacidad
station.startService(serverIdx, time, currentTime);
station.releaseServer(serverIdx);
```

### `QueueSimulation`
Motor principal de simulación:
```cpp
std::vector<int> config = {3, 2, 2, 1, 4};
QueueSimulation sim(config, seed);

sim.initialize();                // Preparar simulación
sim.run();                        // Ejecutar
sim.getStatistics();              // Obtener resultados
sim.printResults();               // Mostrar resultados
```

### `Statistics`
Resultados de la simulación:
```cpp
Statistics stats = sim.getStatistics();

stats.avgWaitTime;               // Tiempo espera promedio
stats.waitTimeStdDev;             // Desviación estándar
stats.avgSystemTime;              // Tiempo en sistema
stats.totalCustomers;             // Clientes procesados
stats.stationUtilization;         // Utilización por estación
```

## Configuración

Editar `src/config.h`:

```cpp
// Parámetros de servicio
const double MU_CASHIER = 0.4;
const double MU_DRINKS = 1.333;
const double MEAN_FRYER = 3.0;

// Probabilidades
const double PROB_DRINKS = 0.9;
const double PROB_FRYER = 0.7;
const double PROB_DESSERTS = 0.25;
const double PROB_CHICKEN = 0.3;

// Simulación
const double SIMULATION_TIME = 480.0;  // 8 horas
const int NUM_REPLICAS = 30;
```

## Estructuras de Datos

### `Event`
```cpp
struct Event {
    double time;           // Tiempo del evento
    int eventType;         // ARRIVAL o SERVICE_END
    int customerId;        // ID del cliente
    int stationId;         // ID de la estación
};
```

### `Customer`
```cpp
struct Customer {
    int id;
    double arrivalTime;
    double departureTime;
    double totalWaitTime;
    std::vector<int> stations;        // Ruta
    int numOrders;                     // Órdenes
    int currentStationIndex;
};
```

## Enumeraciones

```cpp
enum EventType { ARRIVAL, SERVICE_END };
enum Station { CASHIER = 0, DRINKS = 1, FRYER = 2, 
               DESSERTS = 3, CHICKEN = 4 };
```

## Parámetros por Defecto

| Parámetro | Valor |
|-----------|-------|
| Llegadas (λ) | 3/min |
| Cajas (μ) | 0.4/min |
| Refrescos (μ) | 1.333/min |
| Freidora | N(3, 0.5) |
| Postres | B(5, 0.6) |
| Pollo | Geom(0.1) |
| Duración | 480 min |
| Servidores | [3,2,2,1,4] |

## Constantes Importantes

```cpp
const int NUM_STATIONS = 5;
const double SIMULATION_TIME = 480.0;
const int NUM_WARMUP_MINUTES = 60;
const double MAX_UTILIZATION = 0.8;
const int TOTAL_SERVERS = 12;
```

## Flujo Típico de Uso

```cpp
#include "simulation.h"

int main() {
    // 1. Configurar
    std::vector<int> config = {3, 2, 2, 1, 4};
    
    // 2. Crear
    QueueSimulation sim(config, 42);
    
    // 3. Inicializar
    sim.initialize();
    
    // 4. Ejecutar
    sim.run();
    
    // 5. Analizar
    Statistics stats = sim.getStatistics();
    
    // 6. Mostrar
    sim.printResults();
    
    return 0;
}
```

## Validación Básica

```cpp
// Verificar que configuración es válida
int total = 0;
for (int s : config) total += s;
assert(total == 12);  // Debe ser exactamente 12

// Verificar estabilidad
for (double util : stats.stationUtilization) {
    assert(util < 0.8);  // Debe ser menor a 80%
}
```

## Búsqueda de Configuración Óptima

```cpp
std::vector<int> bestConfig;
double minWait = INFINITY;

for (int c1 = 1; c1 <= 12; c1++) {
    for (int c2 = 1; c1 + c2 <= 12; c2++) {
        // ... iterar todas las combinaciones
        
        if (avgWait < minWait) {
            minWait = avgWait;
            bestConfig = {c1, c2, c3, c4, c5};
        }
    }
}
```

## Múltiples Réplicas

```cpp
std::vector<double> results;

for (int r = 0; r < 30; r++) {
    QueueSimulation sim(config, r);  // Semilla = r
    sim.initialize();
    sim.run();
    
    results.push_back(sim.getStatistics().avgWaitTime);
}

// Calcular media y desviación
double mean = accumulate(results.begin(), results.end(), 0.0) / 30;
double variance = 0;
for (double val : results) {
    variance += (val - mean) * (val - mean);
}
double stddev = sqrt(variance / 30);
```

## Macros Útiles

```cpp
#define DEBUG(x) std::cout << #x << " = " << x << std::endl
#define ASSERT_CONFIG(cfg) assert(cfg[0] + cfg[1] + cfg[2] + cfg[3] + cfg[4] == 12)
```

## Troubleshooting

| Problema | Solución |
|----------|----------|
| No compila | Usar C++17: `-std=c++17` |
| Resultados erráticos | Aumentar NUM_REPLICAS |
| Utilización > 0.8 | Agregar servidores |
| Espera muy baja | Demasiados servidores |
| No termina | Verificar SIMULATION_TIME |

## Optimizaciones de Performance

```cpp
// Compilar con optimización
g++ -std=c++17 -O3 -march=native ...

// Usar referencias en bucles
for (const auto& customer : completedCustomers) { ... }

// Preallocar memoria
customers.reserve(expectedCount);
```

## Salida Esperada

```
Simulación inicializada con configuración:
  Cajas: 3 servidor(es)
  Refrescos: 2 servidor(es)
  Freidora: 2 servidor(es)
  Postres: 1 servidor(es)
  Pollo: 4 servidor(es)

Iniciando simulación...
Simulación finalizada en tiempo: 480 minutos

============================================================
RESULTADOS DE LA SIMULACIÓN
============================================================

Clientes procesados: 1425
Tiempo de espera promedio: 6.24 minutos
Desviación estándar: 3.51 minutos
Tiempo en sistema promedio: 15.82 minutos

Utilización por estación:
-----------
       Cajas:  72.3%
   Refrescos:  65.4%
    Freidora:  68.9%
     Postres:  45.2%
       Pollo:  75.6%
============================================================
```

## Enlaces Útiles

- Guía completa: [queue_simulation_guide.md](Instrucciones/queue_simulation_guide.md)
- Arquitectura: [ARQUITECTURA.md](ARQUITECTURA.md)
- Ejemplos: [EJEMPLOS_USO.cpp](EJEMPLOS_USO.cpp)
- Instalación: [INSTALACION.md](INSTALACION.md)

---

**Última actualización**: Enero 2026  
**Versión**: 1.0
