# Simulación de Sistema de Colas - Restaurante de Comida Rápida

## Estructura del Proyecto

```
Tarea-V-Simulación/
├── Instrucciones/
│   └── queue_simulation_guide.md    # Especificaciones completas
├── src/
│   ├── main.cpp                      # Punto de entrada
│   ├── simulation.h                  # Headers y declaraciones
│   └── simulation.cpp                # Implementación
├── Makefile                          # Para compilación en Linux/Mac
├── compile.bat                       # Script de compilación para Windows
└── README.md                         # Este archivo
```

## Descripción de Componentes

### 1. **simulation.h**
Contiene todas las declaraciones:
- **Enumeraciones**: `EventType`, `Station`
- **Estructuras**:
  - `Event`: Representa eventos en la simulación
  - `Customer`: Información de cada cliente
  - `Statistics`: Estadísticas de salida
- **Clases**:
  - `RandomGenerators`: Generadores de números aleatorios con diferentes distribuciones
  - `Station`: Representa una estación de servicio con colas
  - `QueueSimulation`: Motor principal de simulación con eventos discretos

### 2. **simulation.cpp**
Implementación de todas las clases:
- Distribuciones aleatorias (Exponencial, Normal, Binomial, Geométrica)
- Lógica de estaciones (colas, servidores)
- Motor de simulación con manejo de eventos
- Cálculo de estadísticas

### 3. **main.cpp**
Programa principal que:
- Define la configuración de servidores (3, 2, 2, 1, 4 para cada estación)
- Crea la simulación
- Ejecuta la simulación
- Muestra resultados

## Compilación

### En Windows (con MinGW/g++ instalado)

```bash
compile.bat
```

O manualmente:
```bash
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation.exe
```

### En Linux/Mac

```bash
make
```

O manualmente:
```bash
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation
```

## Ejecución

### Windows
```bash
bin\simulation.exe
```

### Linux/Mac
```bash
./bin/simulation
```

## Características Implementadas

✅ **Generadores Aleatorios**:
- Tiempos entre llegadas (Exponencial/Poisson)
- Tiempos de servicio específicos por estación
- Decisiones probabilísticas de enrutamiento

✅ **Sistema de Colas**:
- Múltiples servidores por estación
- Colas FIFO
- Generación de rutas aleatorias

✅ **Motor de Simulación**:
- Discrete Event Simulation (DES)
- Cola de eventos con prioridad
- Gestión de llegadas y fins de servicio

✅ **Estadísticas**:
- Tiempo de espera promedio
- Desviación estándar
- Utilización de estaciones
- Clientes procesados

## Configuración de Servidores

La configuración actual en `main.cpp`:
```cpp
std::vector<int> serverConfig = {3, 2, 2, 1, 4};
```

Representa:
- Cajas: 3 servidores
- Refrescos: 2 servidores
- Freidora: 2 servidores
- Postres: 1 servidor
- Pollo: 4 servidores
- **Total: 12 servidores**

## Próximos Pasos para Mejora

1. **Múltiples Réplicas**: Implementar función para ejecutar 30+ réplicas
2. **Búsqueda de Configuración Óptima**: Iterar sobre todas las combinaciones
3. **Análisis de Warm-up**: Descartar primeros 60 minutos de transitorio
4. **Validación de Estabilidad**: Verificar ρᵢ < 0.8
5. **Salida Detallada**: Exportar resultados a archivos

## Parámetros de Simulación

| Parámetro | Valor |
|-----------|-------|
| Tiempo de simulación | 480 minutos (8 horas) |
| Tasa de llegadas (λ) | 3 clientes/minuto |
| Órdenes por cliente | Binomial(5, 0.4) |
| Total servidores | 12 |

## Validación

La simulación es válida si:
- ✓ Todos los clientes completan su ruta
- ✓ Utilización < 0.8 en todas las estaciones
- ✓ Resultados son reproducibles (con misma semilla)
- ✓ Tiempo de espera > 0 (existe alguna congestión)

## Compilación con Depuración

### Linux/Mac
```bash
make debug
```

### Windows (manual)
```bash
g++ -std=c++17 -g -O0 src/main.cpp src/simulation.cpp -o bin/simulation.exe
```

Luego depurar con:
```bash
gdb bin/simulation
```

## Notas

- El código está escrito siguiendo estándares C++17
- Se utiliza `<random>` para generadores de alta calidad
- La simulación es reproducible con semillas
- Se puede escalar a más estaciones fácilmente

---

**Estudiante**: [Tu nombre]  
**Curso**: Simulación y Modelado  
**Año**: 2026
