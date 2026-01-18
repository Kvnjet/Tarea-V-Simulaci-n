# 📑 ÍNDICE DEL PROYECTO - Simulación de Colas

## 🎯 INICIO RÁPIDO

**¿Acabo de descargar el proyecto?**

1. Lee: [README.md](README.md) (5 min)
2. Instala compilador: [INSTALACION.md](INSTALACION.md) (10 min)
3. Compila: Ver sección "Compilación" en README.md (2 min)
4. Ejecuta: `bin\simulation.exe`

---

## 📚 DOCUMENTACIÓN COMPLETA

### 📖 Nivel 1: Conceptual
- [DIAGRAMA.txt](DIAGRAMA.txt) - **Empieza aquí** si quieres entender el flujo
  - Máquina de estados
  - Ciclo de simulación
  - Estructura de datos

- [Instrucciones/queue_simulation_guide.md](Instrucciones/queue_simulation_guide.md) - Especificación completa
  - Definición del problema
  - Parámetros exactos
  - Criterios de evaluación

### 📖 Nivel 2: Implementación
- [ARQUITECTURA.md](ARQUITECTURA.md) - Cómo está implementado
  - Diagrama de clases
  - Flujo de datos
  - Algoritmo DES
  - Estructuras internas

- [README.md](README.md) - Instrucciones de proyecto
  - Compilación
  - Ejecución
  - Estructura de archivos

### 📖 Nivel 3: Referencia
- [REFERENCIA.md](REFERENCIA.md) - Guía rápida de APIs
  - Clases principales
  - Métodos públicos
  - Parámetros por defecto
  - Ejemplos de código

- [EJEMPLOS_USO.cpp](EJEMPLOS_USO.cpp) - 7 ejemplos comentados
  - Simulación básica
  - Múltiples réplicas
  - Búsqueda óptima
  - Análisis de sensibilidad

### 📖 Nivel 4: Continuación
- [PROXIMOS_PASOS.md](PROXIMOS_PASOS.md) - Qué hacer después
  - Tareas pendientes
  - Código para implementar
  - Orden recomendado
  - Pruebas sugeridas

---

## 💻 ARCHIVOS DE CÓDIGO

### Headers y Declaraciones
- **src/simulation.h** - Clases principales
  - `RandomGenerators` - Distribuciones aleatorias
  - `Station` - Estación con cola
  - `Event` / `Customer` / `Statistics` - Estructuras
  - `QueueSimulation` - Motor DES

- **src/config.h** - Parámetros configurables
  - Tasas de servicio
  - Probabilidades
  - Tiempos de simulación
  - Números de servidores

- **src/optimizer.h** - Interfaces para optimización (opcional)

### Implementación
- **src/main.cpp** - Punto de entrada del programa
  - Define configuración de servidores
  - Crea y ejecuta simulación
  - Muestra resultados

- **src/simulation.cpp** - Implementación de todas las clases
  - Generadores aleatorios
  - Gestión de estaciones
  - Motor DES
  - Cálculo de estadísticas

---

## 🚀 COMPILACIÓN

### Scripts Disponibles
- **compile.bat** - Para Windows (automático)
- **Makefile** - Para Linux/Mac (automático)

### Manual
```bash
# Todos los sistemas
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation.exe
```

---

## 📊 FLUJO DE NAVEGACIÓN SEGÚN TU ROL

### 👨‍🎓 "Soy estudiante y acabo de recibir esto"
1. [README.md](README.md) - Entiende estructura
2. [INSTALACION.md](INSTALACION.md) - Instala compilador
3. [DIAGRAMA.txt](DIAGRAMA.txt) - Ve cómo funciona
4. [ARQUITECTURA.md](ARQUITECTURA.md) - Aprende diseño
5. Compila y ejecuta

### 👨‍💻 "Quiero modificar/extender el código"
1. [REFERENCIA.md](REFERENCIA.md) - APIs disponibles
2. [src/simulation.h](src/simulation.h) - Lee declaraciones
3. [src/simulation.cpp](src/simulation.cpp) - Lee implementación
4. [EJEMPLOS_USO.cpp](EJEMPLOS_USO.cpp) - Ve ejemplos
5. Haz tus cambios

### 🔬 "Necesito entender el algoritmo"
1. [DIAGRAMA.txt](DIAGRAMA.txt) - Visualización
2. [ARQUITECTURA.md](ARQUITECTURA.md) - Algoritmo DES
3. [Instrucciones/queue_simulation_guide.md](Instrucciones/queue_simulation_guide.md) - Teoría
4. Lee src/simulation.cpp con breakpoints en debugger

### 🎯 "Quiero optimizar para obtener mejores notas"
1. [PROXIMOS_PASOS.md](PROXIMOS_PASOS.md) - Tareas pendientes
2. [EJEMPLOS_USO.cpp](EJEMPLOS_USO.cpp) - Ejemplo 2, 3, 5
3. Implementa múltiples réplicas
4. Implementa búsqueda de configuración
5. Presenta resultados

---

## 🗂️ ESTRUCTURA DE CARPETAS

```
📦 Proyecto/
│
├─ 📄 README.md                    ← EMPIEZA AQUÍ
├─ 📄 INSTALACION.md               ← Si no compilas
├─ 📄 ARQUITECTURA.md              ← Si quieres entender
├─ 📄 REFERENCIA.md                ← Si necesitas APIs
├─ 📄 DIAGRAMA.txt                 ← Si quieres visualizar
├─ 📄 EJEMPLOS_USO.cpp             ← Si quieres ejemplos
├─ 📄 PROXIMOS_PASOS.md            ← Si necesitas qué hacer
├─ 📄 PROYECTO_COMPLETO.md         ← Resumen de todo
├─ 📄 INDICE.md                    ← Este archivo
│
├─ 📁 Instrucciones/
│  └─ 📄 queue_simulation_guide.md  ← Especificación oficial
│
├─ 📁 src/                         ← CÓDIGO FUENTE
│  ├─ 📄 main.cpp
│  ├─ 📄 simulation.h
│  ├─ 📄 simulation.cpp
│  ├─ 📄 config.h
│  └─ 📄 optimizer.h
│
├─ 📁 bin/                         ← EJECUTABLES (después compilar)
│  └─ 📄 simulation.exe
│
├─ 📁 build/                       ← ARCHIVOS OBJETO (temporal)
│
├─ 📄 Makefile                     ← Para compilar (Linux/Mac)
├─ 📄 compile.bat                  ← Para compilar (Windows)
└─ 📁 .git/                        ← Control de versión
```

---

## 🎓 MAPA DE CONCEPTOS

```
SIMULACIÓN DE COLAS
│
├─ ENTRADA
│  ├─ Configuración de servidores
│  ├─ Parámetros de servicio
│  └─ Probabilidades de enrutamiento
│
├─ PROCESAMIENTO
│  ├─ Generador de Eventos
│  │  ├─ Tiempos de llegada (Poisson)
│  │  └─ Tiempos de servicio (distribuciones)
│  │
│  ├─ Motor DES
│  │  ├─ Cola de eventos (priority queue)
│  │  ├─ Procesamiento ARRIVAL
│  │  └─ Procesamiento SERVICE_END
│  │
│  └─ Estaciones
│     ├─ Colas FIFO
│     ├─ Servidores múltiples
│     └─ Enrutamiento probabilístico
│
└─ SALIDA
   ├─ Tiempo de espera
   ├─ Desviación estándar
   ├─ Utilización de estaciones
   └─ Clientes procesados
```

---

## 📋 CHECKLIST DE ENTENDIMIENTO

Usa esto para verificar que entiendes cada parte:

- [ ] Sé qué es un sistema DES
- [ ] Entiendo cómo funcionan las colas
- [ ] Conozco las distribuciones usadas
- [ ] He compilado el código
- [ ] Ejecuté la simulación
- [ ] Entiendo la salida
- [ ] Leí ARQUITECTURA.md
- [ ] Revisé el código en simulation.h
- [ ] Revisé el código en simulation.cpp
- [ ] Sé cómo modificar parámetros
- [ ] Entiendo cómo hacer múltiples réplicas
- [ ] Sé cómo buscar configuración óptima

---

## 🔗 REFERENCIAS EXTERNAS

Si necesitas ayuda con conceptos:

- **DES (Discrete Event Simulation)**: Wikipedia DES
- **Colas M/M/c**: Teoría de colas (Wikipedia)
- **C++17 Random**: cppreference.com/w/cpp/numeric/random
- **Jackson Networks**: Wikipedia Jackson Networks

---

## ⏱️ TIMELINE RECOMENDADO

| Día | Tarea | Duración |
|-----|-------|----------|
| 1 | Leer README + instalar | 30 min |
| 1 | Compilar y ejecutar | 15 min |
| 1 | Leer ARQUITECTURA | 30 min |
| 2 | Entender código | 1 hora |
| 2 | Implementar múltiples réplicas | 1 hora |
| 3 | Implementar búsqueda | 2 horas |
| 3 | Validar y documentar | 1 hora |
| 4 | Presentar resultados | 30 min |

**Total**: ~7 horas

---

## 🆘 NECESITO AYUDA CON...

### "No compila"
→ [INSTALACION.md](INSTALACION.md) - Instalar compilador

### "No entiendo cómo funciona"
→ [ARQUITECTURA.md](ARQUITECTURA.md) + [DIAGRAMA.txt](DIAGRAMA.txt)

### "Quiero ver ejemplos"
→ [EJEMPLOS_USO.cpp](EJEMPLOS_USO.cpp)

### "No sé qué hacer ahora"
→ [PROXIMOS_PASOS.md](PROXIMOS_PASOS.md)

### "¿Cómo cambio los parámetros?"
→ [src/config.h](src/config.h) + [REFERENCIA.md](REFERENCIA.md)

### "¿Cuál es la especificación exacta?"
→ [Instrucciones/queue_simulation_guide.md](Instrucciones/queue_simulation_guide.md)

---

## 📈 PROGRESO DEL PROYECTO

```
Status: ✅ Implementación Básica Completada

✅ Clases base
✅ Generadores aleatorios
✅ Sistema DES
✅ Estadísticas
⏳ Múltiples réplicas (PRÓXIMO)
⏳ Optimización (PRÓXIMO)
⏳ Análisis avanzado (PRÓXIMO)
```

---

## 🎁 BONUS

Archivos adicionales incluidos:
- [PROYECTO_COMPLETO.md](PROYECTO_COMPLETO.md) - Resumen ejecutivo
- [INDICE.md](INDICE.md) - Este archivo

---

## 📞 PREGUNTAS FRECUENTES

**P: ¿Qué compilador necesito?**
A: g++ 7.0+ (mínimo C++17)

**P: ¿Por qué C++17?**
A: Para usar `<random>` moderno y características como `std::optional`

**P: ¿Puedo usar otro compilador?**
A: Sí: MSVC, clang - todos soportan C++17

**P: ¿Cuánto tiempo lleva entender todo?**
A: 2-3 horas si eres nuevo en DES, 30 min si ya conoces

**P: ¿Está listo para presentar?**
A: Parcialmente. Falta agregar múltiples réplicas y optimización

**P: ¿Dónde están las múltiples réplicas?**
A: [PROXIMOS_PASOS.md](PROXIMOS_PASOS.md) tiene el código

---

## ✨ CARACTERÍSTICAS IMPLEMENTADAS

- ✅ Motor DES con eventos
- ✅ Generadores de distribuciones complejas
- ✅ Sistema de colas con múltiples servidores
- ✅ Enrutamiento probabilístico
- ✅ Estadísticas y reportes
- ✅ Configuración parametrizable
- ⏳ Múltiples réplicas (código en PROXIMOS_PASOS)
- ⏳ Optimización exhaustiva (código en EJEMPLOS_USO)
- ⏳ Visualización (pendiente)

---

## 🎯 ÚLTIMA TAREA

**Si acabas de descargar esto:**

```bash
# 1. Lee esto
cat README.md

# 2. Instala compilador (ver INSTALACION.md)

# 3. Compila
g++ -std=c++17 -O2 src/main.cpp src/simulation.cpp -o bin/simulation.exe

# 4. Ejecuta
bin\simulation.exe

# 5. Entra en ARQUITECTURA.md para aprender
```

---

**Proyecto**: Simulación de Colas - Restaurante de Comida Rápida  
**Versión**: 1.0 (Beta)  
**Fecha**: Enero 2026  
**Estado**: ✅ Listo para usar

¡Disfruta el proyecto! 🚀
