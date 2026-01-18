# Arquitectura del Sistema de Colas

## Diagrama de Clases

```
┌──────────────────────────────┐
│      QueueSimulation         │
│                              │
│  - eventQueue                │
│  - stations[5]               │
│  - customers[]               │
│  - currentTime               │
│  - rng: RandomGenerators     │
│                              │
│  + initialize()              │
│  + run()                     │
│  + processEvent()            │
│  + startService()            │
│  + getStatistics()           │
└──────────────────────────────┘
          │
          ├─────────────────┬──────────────┬──────────────┐
          │                 │              │              │
    ┌─────▼──────┐  ┌──────▼──┐  ┌───────▼───┐  ┌──────▼──────┐
    │ Station[0] │  │Station[]│  │RandomGen  │  │ Events     │
    │  (Cajas)   │  │         │  │           │  │            │
    └────────────┘  └─────────┘  └───────────┘  └────────────┘
```

## Flujo de Datos

```
                          ┌─────────────────┐
                          │ START (t=0)     │
                          └────────┬────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ GenerarPrimeraLlegada(λ)   │
                    │ Agregar a eventQueue       │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │ WHILE t < 480 minutos      │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼─────────────────────┐
              │                    │                     │
         ┌────▼──────┐       ┌────▼──────┐      ┌──────▼────┐
         │ ARRIVAL   │       │SERVICE_END│      │ UPDATE t  │
         │ Event     │       │ Event     │      │           │
         └────┬──────┘       └────┬──────┘      └───────────┘
              │                   │
         ┌────▼──────────────────┐│
         │ CrearCliente          ││
         │ GenerarRuta           ││
         │ AgregarACajas         ││
         │ SiServerDisponible    ││
         │   Iniciar Servicio    ││
         │ AgendarSiguienteLleg  ││
         │                       ││
         │                       │└──────────────┐
         │                       │               │
         │                   ┌───▼────────────┐  │
         │                   │LiberarServidor │  │
         │                   │AvanzarEstación │  │
         │                   │SiMásEstaciones │  │
         │                   │ Ir a siguiente │  │
         │                   │ElseTerminar    │  │
         │                   │                │  │
         └───────────────────┴────────────────┘  │
                   │                             │
                   └─────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────┐
                    │ GENERAR REPORTES       │
                    │ - Tiempo Espera Prom   │
                    │ - Desv. Estándar       │
                    │ - Utilización          │
                    └────────────────────────┘
```

## Máquina de Estados del Cliente

```
                    ┌─────────────┐
                    │   LLEGA     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  CAJAS      │ (Siempre)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ ¿REFRESCOS? │ (90%)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ ¿FREIDORA?  │ (70%)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ ¿POSTRES?   │ (25%)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ ¿POLLO?     │ (30%)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   SALE      │
                    └─────────────┘
```

## Distribuciones Aleatorias Utilizadas

| Estación | Distribución | Parámetros | Propósito |
|----------|--------------|-----------|----------|
| Llegadas | Exponencial | λ=3 | Tiempos entre llegadas |
| Cajas | Exponencial | μ=0.4 | Tiempo servicio |
| Refrescos | Exponencial | μ=1.333 | Tiempo servicio |
| Freidora | Normal Discreta | μ=3, σ=0.5 | Tiempo servicio |
| Postres | Binomial | n=5, p=0.6 | Tiempo servicio |
| Pollo | Geométrica | p=0.1 | Tiempo servicio |
| Órdenes | Binomial | n=5, p=0.4 | Cantidad órdenes/cliente |

## Estructura de Datos Principal

### Event Queue (Priority Queue)
```
min-heap
├─ (t=0.5, ARRIVAL, -1, -1)
├─ (t=1.2, SERVICE_END, 0, 0)
├─ (t=2.1, ARRIVAL, -1, -1)
└─ (t=3.5, SERVICE_END, 1, 0)
```

### Stations Array
```
stations[0] → CASHIER
   ├─ queue: [Customer 0, Customer 2]
   ├─ serverBusy: [true, false, false]
   └─ serviceEndTimes: [3.5, 0, 0]

stations[1] → DRINKS
   ├─ queue: [Customer 1]
   ├─ serverBusy: [true, false]
   └─ serviceEndTimes: [2.8, 0]
```

## Algoritmo DES (Discrete Event Simulation)

```
1. Inicializar()
   ├─ Crear estaciones con sus servidores
   ├─ Cola de eventos vacía
   ├─ t = 0
   └─ Programar primera llegada

2. Mientras (t < T_simulación)
   ├─ Extraer evento con tiempo mínimo
   ├─ Actualizar t al tiempo del evento
   ├─ Procesar evento:
   │  ├─ Si ARRIVAL:
   │  │  ├─ Crear cliente
   │  │  ├─ Generar ruta
   │  │  ├─ Agregar a Cajas
   │  │  ├─ Si servidor disponible → startService()
   │  │  └─ Programar siguiente llegada
   │  │
   │  └─ Si SERVICE_END:
   │     ├─ Liberar servidor
   │     ├─ Si más estaciones en ruta → Ir siguiente
   │     ├─ Else → Registrar salida
   │     └─ Si hay cola → startService(siguiente cliente)

3. Calcular Estadísticas()
   ├─ Promedio de tiempos de espera
   ├─ Desviación estándar
   ├─ Utilización por estación
   └─ Imprimir resultados
```

## Ejemplo de Ejecución

### Simulación en tiempo simulado:

```
t=0.00: ARRIVAL (Cliente 0) → Cola Cajas
t=0.00: SERVICE_END (Cliente 0, Cajas) → Ir a Refrescos (90%)
t=0.50: ARRIVAL (Cliente 1) → Cola Cajas
t=1.20: SERVICE_END (Cliente 0, Refrescos) → Ir a Freidora (70%)
t=1.50: ARRIVAL (Cliente 2) → Cola Cajas
t=1.50: SERVICE_END (Cliente 1, Cajas) → Ir a Refrescos
t=2.10: SERVICE_END (Cliente 2, Cajas) → Ir a Postres (25%)
...
t=480.00: FIN SIMULACIÓN
```

## Cálculo de Métricas

### Tiempo de Espera Promedio
```
W̄ = (1/n) × Σ(t_salida - t_llegada) para todos los clientes
```

### Desviación Estándar
```
σ = √[(1/n) × Σ(W_i - W̄)²]
```

### Utilización de Estación
```
ρ_i = (Σ tiempos_servicio) / (num_servidores × tiempo_simulación)
```

## Escalabilidad

El código está diseñado para ser fácil de escalar:

### Agregar una nueva estación:
1. Agregar enum en Station
2. Aumentar NUM_STATIONS
3. Agregar parámetros en config.h
4. Agregar caso en generateRoute()
5. Agregar caso en startService()

### Agregar réplicas:
```cpp
for (int r = 0; r < NUM_REPLICAS; r++) {
    QueueSimulation sim(config, r);  // Semilla diferente
    sim.initialize();
    sim.run();
    results[r] = sim.getStatistics();
}
```

## Optimización de Servidores

Búsqueda exhaustiva sobre todas las combinaciones:

```cpp
for (int c1 = 1; c1 <= 12; c1++) {
    for (int c2 = 1; c1+c2 <= 12; c2++) {
        for (int c3 = 1; c1+c2+c3 <= 12; c3++) {
            for (int c4 = 1; c1+c2+c3+c4 <= 12; c4++) {
                int c5 = 12 - c1 - c2 - c3 - c4;
                if (c5 < 1) continue;
                
                config = {c1, c2, c3, c4, c5};
                avgWait = runMultipleSimulations(config);
                
                if (avgWait < minWait) {
                    minWait = avgWait;
                    bestConfig = config;
                }
            }
        }
    }
}
```

---

**Nota**: Esta arquitectura sigue el patrón de Discrete Event Simulation estándar en investigación de operaciones.
