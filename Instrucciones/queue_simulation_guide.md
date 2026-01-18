# Guía de Implementación: Simulación de Sistema de Colas en Restaurante de Comida Rápida

## 1. Resumen del Problema

Debes simular un sistema de colas (red de Jackson abierta) para un restaurante de comida rápida con 5 estaciones de servicio y 12 trabajadores totales. El objetivo es **minimizar el tiempo de espera promedio** asignando trabajadores óptimamente a cada estación.

### Estaciones del Sistema:
1. **Cajas** (obligatoria, 100% de clientes)
2. **Refrescos** (90% probabilidad)
3. **Freidora** (70% probabilidad)
4. **Postres** (25% probabilidad)
5. **Pollo** (30% probabilidad)

---

## 2. Parámetros Clave del Sistema

### 2.1 Llegadas de Clientes
- **Distribución**: Proceso Poisson
- **Tasa λ**: 3 clientes/minuto (ajustable)

### 2.2 Tiempos de Servicio por Estación

| Estación | Distribución | Parámetros |
|----------|--------------|------------|
| Cajas | Exponencial | μ⁻¹ = 2.5 min (μ = 0.4/min) |
| Refrescos | Exponencial | μ⁻¹ = 0.75 min (μ = 1.333/min) |
| Freidora | Normal Discreta | μ⁻¹ = 3 min (μ ≈ 0.333/min) |
| Postres | Binomial | n=5, p=0.6 (μ⁻¹ ≈ 1.5 min) |
| Pollo | Geométrica | p = 0.1 |

### 2.3 Cantidad de Órdenes por Cliente
- **Distribución**: Binomial(n=5, p=2/5)
- Cada cliente tiene entre 0-5 órdenes

### 2.4 Probabilidades de Enrutamiento
- **Cajas**: 1.0 (todos pasan)
- **Refrescos**: 0.9
- **Freidora**: 0.7
- **Postres**: 0.25
- **Pollo**: 0.3

---

## 3. Arquitectura de la Solución en C++

### 3.1 Estructura de Clases Principal

```cpp
// Evento en la simulación
struct Event {
    double time;           // Tiempo del evento
    int eventType;         // Tipo: ARRIVAL, SERVICE_END, etc.
    int customerId;
    int stationId;
    
    bool operator>(const Event& other) const {
        return time > other.time;
    }
};

// Cliente en el sistema
struct Customer {
    int id;
    double arrivalTime;
    double totalWaitTime;
    std::vector<int> stations;  // Estaciones a visitar
    int numOrders;              // Cantidad de órdenes
    int currentStationIndex;
};

// Estación de servicio
class Station {
    int id;
    int numServers;
    std::queue<Customer*> queue;
    std::vector<bool> serverBusy;
    std::vector<double> serviceEndTimes;
    
public:
    void addCustomer(Customer* c);
    Customer* getNextCustomer();
    bool hasAvailableServer();
    int getQueueLength();
    double getUtilization();
};

// Motor de simulación
class QueueSimulation {
    std::priority_queue<Event, std::vector<Event>, 
                       std::greater<Event>> eventQueue;
    std::vector<Station> stations;
    std::vector<Customer> customers;
    std::mt19937 rng;
    
    double currentTime;
    double simulationDuration;  // 8 horas = 480 minutos
    
public:
    void initialize(std::vector<int> serverConfig);
    void run();
    void generateArrival();
    void processEvent(Event& e);
    Statistics getStatistics();
};
```

### 3.2 Generadores de Números Aleatorios

```cpp
class RandomGenerators {
    std::mt19937 rng;
    
public:
    // Llegadas Poisson (tiempos entre llegadas exponenciales)
    double exponentialInterarrival(double lambda) {
        std::exponential_distribution<> dist(lambda);
        return dist(rng);
    }
    
    // Servicio en Cajas y Refrescos
    double exponentialService(double mu) {
        std::exponential_distribution<> dist(mu);
        return dist(rng);
    }
    
    // Servicio en Freidora (Normal Discreta)
    int normalDiscreteService(double mean, double stddev) {
        std::normal_distribution<> dist(mean, stddev);
        int value = std::round(dist(rng));
        return std::max(1, value);  // Mínimo 1 minuto
    }
    
    // Servicio en Postres (Binomial)
    int binomialService(int n, double p) {
        std::binomial_distribution<> dist(n, p);
        return dist(rng);
    }
    
    // Servicio en Pollo (Geométrica)
    int geometricService(double p) {
        std::geometric_distribution<> dist(p);
        return dist(rng) + 1;  // Geométrica empieza en 1
    }
    
    // Cantidad de órdenes por cliente
    int numOrders() {
        std::binomial_distribution<> dist(5, 0.4);
        return dist(rng);
    }
    
    // Decisión de visitar estación
    bool shouldVisit(double probability) {
        std::uniform_real_distribution<> dist(0.0, 1.0);
        return dist(rng) < probability;
    }
};
```

---

## 4. Algoritmo de Simulación (Discrete Event Simulation)

### 4.1 Flujo Principal

```
1. Inicializar:
   - Cola de eventos vacía
   - Configuración de servidores por estación
   - Tiempo actual = 0
   - Programar primera llegada

2. Mientras tiempo < 480 minutos:
   a. Extraer evento con menor tiempo de la cola
   b. Avanzar tiempo actual al tiempo del evento
   c. Procesar evento según tipo:
      - ARRIVAL: Generar cliente, enrutar a Cajas
      - SERVICE_END: Liberar servidor, enrutar cliente
   d. Programar siguiente evento si corresponde

3. Calcular estadísticas finales
```

### 4.2 Procesamiento de Llegada

```cpp
void processArrival(Event& e) {
    // Crear nuevo cliente
    Customer c;
    c.id = nextCustomerId++;
    c.arrivalTime = currentTime;
    c.numOrders = rng.numOrders();
    
    // Determinar ruta del cliente
    c.stations.push_back(CASHIER);  // Siempre va a Cajas
    
    if (rng.shouldVisit(0.9)) 
        c.stations.push_back(DRINKS);
    if (rng.shouldVisit(0.7)) 
        c.stations.push_back(FRYER);
    if (rng.shouldVisit(0.25)) 
        c.stations.push_back(DESSERTS);
    if (rng.shouldVisit(0.3)) 
        c.stations.push_back(CHICKEN);
    
    // Agregar a estación de Cajas
    stations[CASHIER].addCustomer(&c);
    
    // Si hay servidor disponible, iniciar servicio
    if (stations[CASHIER].hasAvailableServer()) {
        startService(CASHIER, &c);
    }
    
    // Programar siguiente llegada
    double nextArrival = currentTime + rng.exponentialInterarrival(3.0);
    eventQueue.push({nextArrival, ARRIVAL, -1, -1});
}
```

### 4.3 Procesamiento de Fin de Servicio

```cpp
void processServiceEnd(Event& e) {
    int stationId = e.stationId;
    Customer* c = &customers[e.customerId];
    
    // Liberar servidor
    stations[stationId].releaseServer();
    
    // Avanzar a siguiente estación en la ruta
    c->currentStationIndex++;
    
    if (c->currentStationIndex < c->stations.size()) {
        // Hay más estaciones por visitar
        int nextStation = c->stations[c->currentStationIndex];
        stations[nextStation].addCustomer(c);
        
        if (stations[nextStation].hasAvailableServer()) {
            startService(nextStation, c);
        }
    } else {
        // Cliente termina, registrar tiempo total
        c->totalWaitTime = currentTime - c->arrivalTime;
        completedCustomers.push_back(*c);
    }
    
    // Atender siguiente cliente en cola si hay
    if (!stations[stationId].isEmpty()) {
        Customer* next = stations[stationId].getNextCustomer();
        startService(stationId, next);
    }
}
```

---

## 5. Optimización de Configuración de Servidores

### 5.1 Objetivo
Encontrar la configuración óptima de 12 servidores que **minimice el tiempo de espera promedio**.

### 5.2 Enfoque de Búsqueda

```cpp
struct ServerConfig {
    int cashiers;
    int drinks;
    int fryer;
    int desserts;
    int chicken;
    
    int total() const {
        return cashiers + drinks + fryer + desserts + chicken;
    }
};

// Búsqueda exhaustiva o heurística
ServerConfig findOptimalConfig() {
    double minWaitTime = INFINITY;
    ServerConfig bestConfig;
    
    // Iterar sobre todas las combinaciones válidas
    for (int c1 = 1; c1 <= 12; c1++) {
        for (int c2 = 1; c1+c2 <= 12; c2++) {
            for (int c3 = 1; c1+c2+c3 <= 12; c3++) {
                for (int c4 = 1; c1+c2+c3+c4 <= 12; c4++) {
                    int c5 = 12 - c1 - c2 - c3 - c4;
                    if (c5 < 1) continue;
                    
                    ServerConfig config = {c1, c2, c3, c4, c5};
                    
                    // Simular múltiples réplicas
                    double avgWait = runMultipleSimulations(config, 30);
                    
                    if (avgWait < minWaitTime) {
                        minWaitTime = avgWait;
                        bestConfig = config;
                    }
                }
            }
        }
    }
    
    return bestConfig;
}
```

### 5.3 Configuración Sugerida Inicial

Basado en el documento, una configuración razonable sería:
- **Cajas**: 3 (alta tasa de llegada)
- **Refrescos**: 2 (alta probabilidad, servicio rápido)
- **Freidora**: 2 (probabilidad media, servicio medio)
- **Postres**: 1 (baja probabilidad)
- **Pollo**: 4 (tiempo largo, probabilidad media)

---

## 6. Métricas y Estadísticas

### 6.1 Métricas a Calcular

```cpp
struct Statistics {
    double avgWaitTime;           // W̄
    double waitTimeVariance;      // Var(W)
    double avgSystemTime;
    std::vector<double> stationUtilization;  // ρi para cada estación
    int totalCustomers;
    
    void print() {
        std::cout << "=== Resultados de Simulación ===" << std::endl;
        std::cout << "Clientes atendidos: " << totalCustomers << std::endl;
        std::cout << "Tiempo de espera promedio: " << avgWaitTime 
                  << " minutos" << std::endl;
        std::cout << "Varianza del tiempo: " << waitTimeVariance << std::endl;
        std::cout << "\nUtilización por estación:" << std::endl;
        // ... imprimir cada estación
    }
};
```

### 6.2 Validación de Estabilidad

- **Criterio**: ρᵢ < 0.8 para todas las estaciones
- Si ρᵢ ≥ 0.8, la estación está sobrecargada

---

## 7. Implementación Paso a Paso

### Paso 1: Estructura Básica
1. Definir clases: Event, Customer, Station, QueueSimulation
2. Implementar generadores aleatorios con `<random>`
3. Implementar cola de eventos con `std::priority_queue`

### Paso 2: Lógica de Simulación
1. Implementar `processArrival()`
2. Implementar `processServiceEnd()`
3. Implementar `startService()` para cada tipo de estación
4. Implementar loop principal de simulación

### Paso 3: Estadísticas
1. Recolectar tiempos de espera de cada cliente
2. Calcular media y varianza
3. Calcular utilización de servidores

### Paso 4: Optimización
1. Implementar búsqueda de configuración óptima
2. Ejecutar múltiples réplicas (30+) por configuración
3. Usar semillas diferentes para cada réplica

### Paso 5: Evaluación
1. Verificar cumplimiento de especificaciones (40 pts)
2. Comparar tiempo de espera con mínimo teórico (50 pts)
3. Validar comparabilidad de resultados (10 pts)

---

## 8. Consideraciones Importantes

### 8.1 Múltiples Réplicas
- Ejecutar al menos 30 réplicas independientes
- Usar semillas diferentes: `rng.seed(replicaNumber)`
- Promediar resultados para estimar E[W]

### 8.2 Warm-up Period
- Considerar descartar primeros 60 minutos (estado transitorio)
- Medir estadísticas solo en estado estacionario

### 8.3 Longitud de Simulación
- T = 480 minutos (8 horas)
- Suficiente para alcanzar estado estacionario

### 8.4 Validación
- Comparar con fórmula teórica de Jackson Networks
- Verificar que utilizaciones sean < 0.8

---

## 9. Ejemplo de Salida Esperada

```
=== Configuración de Servidores ===
Cajas: 3 servidores
Refrescos: 2 servidores
Freidora: 2 servidores
Postres: 1 servidor
Pollo: 4 servidores

=== Resultados (30 réplicas) ===
Clientes procesados: 1425 ± 45
Tiempo de espera promedio: 6.2 ± 0.8 minutos
Varianza: 12.5 minutos²

=== Utilización de Estaciones ===
Cajas: 72.3%
Refrescos: 65.4%
Freidora: 68.9%
Postres: 45.2%
Pollo: 75.6%

Puntuación estimada: 95/100
```

---

## 10. Recursos de C++ Necesarios

### Librerías
```cpp
#include <iostream>
#include <queue>
#include <vector>
#include <random>
#include <algorithm>
#include <cmath>
```

### Compilación
```bash
g++ -std=c++17 -O2 simulation.cpp -o simulation
./simulation
```

---

## 11. Checklist Final

- [ ] Implementar generadores aleatorios correctos
- [ ] Sistema de eventos discretos funcionando
- [ ] Enrutamiento probabilístico implementado
- [ ] Múltiples réplicas ejecutándose
- [ ] Estadísticas calculadas correctamente
- [ ] Búsqueda de configuración óptima
- [ ] Validación de utilizaciones < 0.8
- [ ] Documentación y resultados presentados
- [ ] Código bien comentado y organizado

¡Buena suerte con tu implementación!