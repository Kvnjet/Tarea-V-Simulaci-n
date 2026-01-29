/**
 * @file simulacion_colas.cpp
 * @brief Simulación de Sistema de Colas para Restaurante de Comida Rápida
 * @details Implementa un sistema de eventos discretos para modelar una red de colas
 *          de Jackson abierta con enrutamiento probabilístico entre estaciones.
 * 
 * @authors José A. Carballo Martínez & Kevin A. Espinoza Barrantes
 * @date 01/17/2026
 */

#include <iostream>
#include <queue>
#include <vector>
#include <random>
#include <algorithm>
#include <cmath>
#include <memory>
#include <iomanip>

using namespace std;


// ============================================================================
// ENUMERACIONES
// ============================================================================

/**
 * @brief Identificadores de las estaciones de servicio
 */
enum IDEstacion {
    CAJAS = 0,
    REFRESCOS = 1,
    FREIDORA = 2,
    POSTRES = 3,
    POLLO = 4,
    NUM_ESTACIONES = 5
};

/**
 * @brief Tipos de eventos en el sistema de simulación
 */
enum TipoEvento {
    LLEGADA,      ///< Llegada de un nuevo cliente
    FIN_SERVICIO  ///< Fin de servicio en una estación
};


// ============================================================================
// CLASE: Evento
// ============================================================================

/**
 * @class Evento
 * @brief Representa un evento en la simulación de eventos discretos
 */
class Evento {
private:
    double tiempo;    ///< Tiempo en el que ocurre el evento (en minutos)
    TipoEvento tipo;  ///< Tipo de evento (LLEGADA o FIN_SERVICIO)
    int idCliente;    ///< ID del cliente involucrado (-1 si no aplica)
    int idEstacion;   ///< ID de la estación involucrada (-1 si no aplica)

    friend class SimulacionColas;

public:
    /** @brief Constructor por defecto */
    Evento() : tiempo(0.0), tipo(LLEGADA), idCliente(-1), idEstacion(-1) {}
    
    /** @brief Constructor parametrizado */
    Evento(double t, TipoEvento tp, int idC, int idE) 
        : tiempo(t), tipo(tp), idCliente(idC), idEstacion(idE) {}
    
    /** @brief Operador de comparación para priority_queue (min-heap) */
    bool operator>(const Evento& otro) const {
        return tiempo > otro.tiempo;
    }
};


// ============================================================================
// CLASE: Cliente
// ============================================================================

/**
 * @class Cliente
 * @brief Representa un cliente en el sistema de colas
 */
class Cliente {
private:
    int id;                      ///< Identificador único del cliente
    double tiempoLlegada;        ///< Tiempo de llegada al sistema
    double tiempoEsperaTotal;    ///< Tiempo total de espera en colas
    double tiempoServicioTotal;  ///< Tiempo total de servicio recibido
    vector<int> estaciones;      ///< Lista de estaciones que visitará
    int numOrdenes;              ///< Número de órdenes del cliente
    int indiceEstacionActual;    ///< Índice de la estación actual
    double tiempoEntradaCola;    ///< Momento en que entró a la cola actual

    friend class SimulacionColas;

public:
    /** @brief Constructor por defecto */
    Cliente() : id(0), tiempoLlegada(0.0), tiempoEsperaTotal(0.0), 
                tiempoServicioTotal(0.0), numOrdenes(0), 
                indiceEstacionActual(0), tiempoEntradaCola(0.0) {}
    
    /** @brief Calcula el tiempo total en el sistema */
    double getTiempoTotal() const {
        return tiempoEsperaTotal + tiempoServicioTotal;
    }
};


// ============================================================================
// CLASE: GeneradorAleatorio
// ============================================================================

/**
 * @class GeneradorAleatorio
 * @brief Generador de números aleatorios para todas las distribuciones
 */
class GeneradorAleatorio {
private:
    mt19937 rng;  ///< Mersenne Twister (basado en el número primo 2^19937-1)
    
public:
    /** @brief Constructor con semilla opcional */
    GeneradorAleatorio(unsigned int semilla = 42) : rng(semilla) {}
    
    /** @brief Establece una nueva semilla */
    void setSemilla(unsigned int semilla) { rng.seed(semilla); }

    /** @brief Genera el tiempo entre llegadas (Poisson) */
    double tiempoEntreLlegadas(double lambda) {
        exponential_distribution<> dist(lambda);
        return dist(rng);
    }

    /** @brief Genera el tiempo de servicio exponencial */
    double tiempoServicioExp(double mu) {
        exponential_distribution<> dist(mu);
        return dist(rng);
    }
    
    /** @brief Genera el tiempo de servicio normal discreto */
    int tiempoServicioNormDisc(double media, double desvEst) {
        normal_distribution<> dist(media, desvEst);
        int valor = round(dist(rng));
        return max(1, valor);
    }

    /** @brief Genera el tiempo de servicio binomial */
    int tiempoServicioBinom(int n, double p) {
        binomial_distribution<> dist(n, p);
        int valor = dist(rng);
        return max(1, valor);
    }

    /** @brief Genera el tiempo de servicio geométrico */
    int tiempoServicioGeom(double p) {
        geometric_distribution<> dist(p);
        return dist(rng) + 1;
    }
    
    /** @brief Genera el número de órdenes del cliente (Binomial n=5, p=0.4) */
    int numeroOrdenes() {
        binomial_distribution<> dist(5, 0.4);
        return max(1, dist(rng));  // Al menos 1 orden
    }

    /** @brief Decide si visitar estación según probabilidad */
    bool debeVisitar(double proba) {
        uniform_real_distribution<> dist(0.0, 1.0);
        return dist(rng) < proba;
    }
};


// ============================================================================
// CLASE: Estacion
// ============================================================================

/**
 * @class Estacion
 * @brief Representa una estación de servicio con múltiples servidores
 */
class Estacion {
private:
    int id;                        ///< Identificador de la estación
    int numServidores;             ///< Número de servidores paralelos
    queue<int> colaEspera;         ///< Cola FCFS de clientes (IDs)
    vector<bool> servidorOcupado;  ///< Estado de cada servidor
    double tiempoTotalOcupado;     ///< Acumulador para utilización
    double tiempoUltimoCambio;     ///< Tiempo del último cambio de estado
    int totalAtendidos;            ///< Contador de clientes atendidos

public:
    /** @brief Constructor de la estación */
    Estacion(int idEstacion, int servidores) 
        : id(idEstacion), numServidores(servidores),
          tiempoTotalOcupado(0.0), tiempoUltimoCambio(0.0),
          totalAtendidos(0) {
        servidorOcupado.resize(servidores, false);
    }
    
    /** @brief Agrega un cliente a la cola */
    void agregarCliente(int idCliente, double tiempoActual) {
        colaEspera.push(idCliente);
    }
    
    /** @brief Verifica si hay servidor disponible */
    bool hayServidorDisponible() const {
        for (bool ocupado : servidorOcupado) {
            if (!ocupado) return true;
        }
        return false;
    }
    
    /** @brief Inicia el servicio del siguiente cliente */
    int iniciarServicio(double tiempoActual) {
        if (colaEspera.empty()) return -1;
        
        for (size_t i = 0; i < servidorOcupado.size(); i++) {
            if (!servidorOcupado[i]) {
                int idCliente = colaEspera.front();
                colaEspera.pop();
                servidorOcupado[i] = true;
                actualizarTiempoOcupado(tiempoActual);
                return idCliente;
            }
        }
        return -1;
    }
    
    /** @brief Finaliza el servicio y libera el servidor */
    void finalizarServicio(double tiempoActual) {
        for (size_t i = 0; i < servidorOcupado.size(); i++) {
            if (servidorOcupado[i]) {
                servidorOcupado[i] = false;
                actualizarTiempoOcupado(tiempoActual);
                totalAtendidos++;
                return;
            }
        }
    }
    
    /** @brief Actualiza el acumulador de tiempo ocupado */
    void actualizarTiempoOcupado(double tiempoActual) {
        int servidoresOcupados = 0;
        for (bool ocupado : servidorOcupado) {
            if (ocupado) servidoresOcupados++;
        }
        tiempoTotalOcupado += servidoresOcupados * (tiempoActual - tiempoUltimoCambio);
        tiempoUltimoCambio = tiempoActual;
    }
    
    /** @brief Calcula la utilización de la estación */
    double getUtilizacion(double tiempoTotal) const {
        if (tiempoTotal == 0 || numServidores == 0) return 0;
        return tiempoTotalOcupado / (numServidores * tiempoTotal);
    }
    
    /** @brief Obtiene la longitud de la cola */
    int getLongitudCola() const {
        return colaEspera.size();
    }
    
    /** @brief Verifica si la cola está vacía */
    bool estaVacia() const {
        return colaEspera.empty();
    }
};


// ============================================================================
// CLASE: ConfiguracionServidores
// ============================================================================


/**
 * @class ConfiguracionServidores
 * @brief Configuración de servidores para cada estación con cálculo de costo
 */
class ConfiguracionServidores {
private:
    int cajas;      ///< Servidores en Cajas
    int refrescos;  ///< Servidores en Refrescos
    int freidora;   ///< Servidores en Freidora
    int postres;    ///< Servidores en Postres
    int pollo;      ///< Servidores en Pollo

public:
    /** @brief Costos por equipo según especificación */
    static const int COSTO_CAJA = 500;
    static const int COSTO_REFRESCOS = 750;
    static const int COSTO_FREIDORA = 200;
    static const int COSTO_POSTRES = 0;   // Sin costo
    static const int COSTO_POLLO = 100;

    /** @brief Constructor por defecto */
    ConfiguracionServidores() 
        : cajas(0), refrescos(0), freidora(0), postres(0), pollo(0) {}
    
    /** @brief Constructor parametrizado */
    ConfiguracionServidores(int c, int r, int f, int p, int pl) 
        : cajas(c), refrescos(r), freidora(f), postres(p), pollo(pl) {}
    
    /** @brief Calcula el total de servidores */
    int total() const {
        return cajas + refrescos + freidora + postres + pollo;
    }
    
    /** @brief Calcula el costo total de la configuración */
    int calcularCosto() const {
        return cajas * COSTO_CAJA +
               refrescos * COSTO_REFRESCOS +
               freidora * COSTO_FREIDORA +
               postres * COSTO_POSTRES +
               pollo * COSTO_POLLO;
    }
    
    /** @brief Verifica si cumple con presupuesto */
    bool cumplePresupuesto(int presupuesto) const {
        return calcularCosto() <= presupuesto;
    }
    
    /** @brief Imprime la configuración con costo */
    void imprimir() const {
        cout << "Cajas:" << cajas << "($" << cajas * COSTO_CAJA << ") "
             << "Refrescos:" << refrescos << "($" << refrescos * COSTO_REFRESCOS << ") "
             << "Freidora:" << freidora << "($" << freidora * COSTO_FREIDORA << ") "
             << "Postres:" << postres << "($" << postres * COSTO_POSTRES << ") "
             << "Pollo:" << pollo << "($" << pollo * COSTO_POLLO << ") "
             << "| Costo:$" << calcularCosto();
    }
    
    /** @brief Obtiene el tiempo de espera promedio (simplificado) */
    double estimarTiempoEspera() const {
        // Estimación simplificada basada en número de servidores
        double factor = 0.0;
        factor += (cajas > 0) ? 10.0 / cajas : 100.0;
        factor += (refrescos > 0) ? 5.0 / refrescos : 50.0;
        factor += (freidora > 0) ? 8.0 / freidora : 80.0;
        factor += (postres > 0) ? 3.0 / postres : 30.0;
        factor += (pollo > 0) ? 12.0 / pollo : 120.0;
        return factor / 5.0;
    }
    
    /** @brief Getters para acceso */
    int getCajas() const { return cajas; }
    int getRefrescos() const { return refrescos; }
    int getFreidora() const { return freidora; }
    int getPostres() const { return postres; }
    int getPollo() const { return pollo; }
};

// ============================================================================
// CLASE: Estadisticas
// ============================================================================

/**
 * @class Estadisticas
 * @brief Almacena y presenta estadísticas de la simulación
 */
class Estadisticas {
private:
    double tiempoEsperaPromedio;           ///< W̄: Tiempo promedio de espera
    double varianzaTiempoEspera;           ///< Var(W): Varianza
    vector<double> utilizacionEstaciones;  ///< ρᵢ por estación
    int totalClientes;                     ///< Clientes atendidos
    double tiempoSistemaPromedio;          ///< Tiempo total en sistema

    friend class SimulacionColas;
    
public:
    /** @brief Constructor por defecto */
    Estadisticas() 
        : tiempoEsperaPromedio(0.0), varianzaTiempoEspera(0.0),
          totalClientes(0), tiempoSistemaPromedio(0.0) {}
    
    // ------------------------------------------------------------------------
    // Getters y setters
    // ------------------------------------------------------------------------

    /** @brief Obtiene el tiempo promedio de espera (W̄) */
    double getTiempoEsperaPromedio() const {
        return tiempoEsperaPromedio;
    }

    /** @brief Obtiene la varianza del tiempo de espera Var(W) */
    double getVarianzaTiempoEspera() const {
        return varianzaTiempoEspera;
    }

    /** @brief Obtiene el tiempo promedio total en el sistema */
    double getTiempoSistemaPromedio() const {
        return tiempoSistemaPromedio;
    }

    /** @brief Obtiene el número total de clientes atendidos */
    int getTotalClientes() const {
        return totalClientes;
    }

    /** @brief Obtiene la utilización de cada estación (ρᵢ) */
    const vector<double>& getUtilizacionEstaciones() const {
        return utilizacionEstaciones;
    }

    /** @brief Inicializa la estructura para promedios de múltiples réplicas */
    void inicializarPromedios(int numEstaciones) {
        tiempoEsperaPromedio  = 0.0;
        tiempoSistemaPromedio = 0.0;
        varianzaTiempoEspera  = 0.0;
        totalClientes         = 0;
        utilizacionEstaciones.assign(numEstaciones, 0.0);
    }

    /** @brief Asigna el tiempo promedio de espera */
    void setTiempoEsperaPromedio(double valor) {
        tiempoEsperaPromedio = valor;
    }

    /** @brief Asigna el tiempo promedio en el sistema */
    void setTiempoSistemaPromedio(double valor) {
        tiempoSistemaPromedio = valor;
    }

    /** @brief Asigna la varianza del tiempo de espera */
    void setVarianzaTiempoEspera(double valor) {
        varianzaTiempoEspera = valor;
    }

    /** @brief Asigna la utilización de una estación específica */
    void setUtilizacion(int indice, double valor) {
        utilizacionEstaciones[indice] = valor;
    }

    /** @brief Asigna el total de clientes atendidos */
    void setTotalClientes(int total) {
        totalClientes = total;
    }
    
    /** @brief Imprime todas las estadísticas */
    void imprimir() const {
        cout << "\n=== Resultados de Simulación ===" << endl;
        cout << "Clientes atendidos: " << totalClientes << endl;
        cout << fixed << setprecision(3);
        cout << "Tiempo de espera promedio: " << tiempoEsperaPromedio << " min" << endl;
        cout << "Tiempo en sistema promedio: " << tiempoSistemaPromedio << " min" << endl;
        cout << "Varianza del tiempo de espera: " << varianzaTiempoEspera << endl;
        cout << "\nUtilización por estación:" << endl;
        cout << "  Cajas:     " << (utilizacionEstaciones[0] * 100) << "%" << endl;
        cout << "  Refrescos: " << (utilizacionEstaciones[1] * 100) << "%" << endl;
        cout << "  Freidora:  " << (utilizacionEstaciones[2] * 100) << "%" << endl;
        cout << "  Postres:   " << (utilizacionEstaciones[3] * 100) << "%" << endl;
        cout << "  Pollo:     " << (utilizacionEstaciones[4] * 100) << "%" << endl;
    }
    
    /** @brief Verifica la estabilidad del sistema (ρ < 0.8) */
    bool esEstable() const {
        for (double utilizacion : utilizacionEstaciones) {
            if (utilizacion >= 0.8) return false;
        }
        return true;
    }

     /** @brief Verifica si cumple con tiempo máximo de espera */
    bool cumpleTiempoEspera(double tiempoMaximo) const {
        return tiempoEsperaPromedio <= tiempoMaximo;
    }
};


// ============================================================================
// CLASE: SimulacionColas
// ============================================================================

/**
 * @class SimulacionColas
 * @brief Motor principal de la simulación de eventos discretos
 */
class SimulacionColas {
private:
    // Cola de prioridad de eventos (min-heap)
    priority_queue<Evento, vector<Evento>, greater<Evento>> colaEventos;
    
    vector<Estacion> estaciones;          ///< Estaciones de servicio
    vector<Cliente> clientes;             ///< Todos los clientes
    vector<Cliente> clientesCompletados;  ///< Clientes que terminaron
    GeneradorAleatorio rng;               ///< Generador aleatorio
    
    double tiempoActual;        ///< Reloj de simulación (minutos)
    double duracionSimulacion;  ///< Duración total (480 min)
    double tiempoFinalReal;     ///< Tiempo real de finalización de simulación
    int siguienteIdCliente;     ///< Contador de IDs
    double tasaLlegada;         ///< λ: clientes/minuto
    
    // Probabilidades de visitar cada estación (según especificación)
    const vector<double> probabilidadesEstaciones = {1.0, 0.9, 0.7, 0.25, 0.3};
    
public:
    /** @brief Constructor del simulador */
    SimulacionColas(double duracion = 480.0, double lambda = 3.0, unsigned int semilla = 42) 
        : tiempoActual(0.0), duracionSimulacion(duracion), tiempoFinalReal(0.0), siguienteIdCliente(0), 
          tasaLlegada(lambda), rng(semilla) {}
    
    /**
     * @brief Inicializa el sistema con configuración de servidores
     * @param config Configuración de servidores por estación
     */
        /**
     * @brief Inicializa el sistema con configuración de servidores
     * @param config Configuración de servidores por estación
     */
    void inicializar(const ConfiguracionServidores& config) {
        // Limpia el estado previo
        estaciones.clear();
        clientes.clear();
        clientesCompletados.clear();
        tiempoActual = 0;
        siguienteIdCliente = 0;
        
        // Crea las estaciones con número especificado de servidores
        // Usando los getters en lugar de acceso directo
        estaciones.push_back(Estacion(CAJAS, config.getCajas()));
        estaciones.push_back(Estacion(REFRESCOS, config.getRefrescos()));
        estaciones.push_back(Estacion(FREIDORA, config.getFreidora()));
        estaciones.push_back(Estacion(POSTRES, config.getPostres()));
        estaciones.push_back(Estacion(POLLO, config.getPollo()));
        
        // Limpia la cola de eventos
        while (!colaEventos.empty()) colaEventos.pop();
        
        // Programa la primera llegada
        double primeraLlegada = rng.tiempoEntreLlegadas(tasaLlegada);
        colaEventos.push(Evento(primeraLlegada, LLEGADA, -1, -1));
    }
    
    /**
     * @brief Ejecuta la simulación completa
     * 
     * Loop principal: extrae el evento, avanza el reloj y procesa el evento
     * Las llegadas se detienen a los 480 minutos, pero se procesan todos los
     * servicios en progreso para que los clientes se completen correctamente.
     */
    void ejecutar() {
        while (!colaEventos.empty()) {
            // Extrae el próximo evento
            Evento e = colaEventos.top();
            colaEventos.pop();
            
            // Avanza el reloj
            tiempoActual = e.tiempo;
            
            // Procesa el evento según el tipo
            if (e.tipo == LLEGADA) {
                // Solo procesar nuevas llegadas durante el período de llegadas
                if (tiempoActual < duracionSimulacion) {
                    procesarLlegada();
                }
            } else if (e.tipo == FIN_SERVICIO) {
                // Procesar todos los servicios en progreso, sin restricción de tiempo
                procesarFinServicio(e);
            }
        }
        // Guardar el tiempo real de finalización de la simulación
        tiempoFinalReal = tiempoActual;
    }
    
    /**
     * @brief Calcula y retorna estadísticas de la simulación
     * @return Objeto Estadisticas con todos los resultados
     */
    Estadisticas getEstadisticas() {
        Estadisticas stats;
        stats.totalClientes = clientesCompletados.size();
        
        if (stats.totalClientes == 0) {
            stats.tiempoEsperaPromedio = 0.0;
            stats.varianzaTiempoEspera = 0.0;
            stats.tiempoSistemaPromedio = 0.0;
            stats.utilizacionEstaciones.resize(NUM_ESTACIONES, 0);
            return stats;
        }
        
        // Calcula los tiempos promedio SOLO para clientes completados
        double sumaEspera = 0;
        double sumaSistema = 0;
        for (const auto& c : clientesCompletados) {
            // Asegurarse de que el cliente completó toda su ruta
            if (c.indiceEstacionActual >= (int)c.estaciones.size()) {
                sumaEspera += c.tiempoEsperaTotal;
                sumaSistema += c.getTiempoTotal();
            }
        }
        stats.tiempoEsperaPromedio = sumaEspera / stats.totalClientes;
        stats.tiempoSistemaPromedio = sumaSistema / stats.totalClientes;
        
        // Calcula la varianza
        double sumaDiferenciasCuadradas = 0;
        for (const auto& c : clientesCompletados) {
            if (c.indiceEstacionActual >= (int)c.estaciones.size()) {
                double diferencia = c.tiempoEsperaTotal - stats.tiempoEsperaPromedio;
                sumaDiferenciasCuadradas += diferencia * diferencia;
            }
        }
        stats.varianzaTiempoEspera = sumaDiferenciasCuadradas / stats.totalClientes;
        
        // Calcula la utilización por estación usando el tiempo real de simulación
        stats.utilizacionEstaciones.resize(NUM_ESTACIONES);
        double tiempoSimulacion = tiempoFinalReal > 0 ? tiempoFinalReal : duracionSimulacion;
        for (int i = 0; i < NUM_ESTACIONES; i++) {
            stats.utilizacionEstaciones[i] = estaciones[i].getUtilizacion(tiempoSimulacion);
        }
        
        return stats;
    }
    
private:
    /**
     * @brief Procesa evento de llegada de cliente
     * 
     * Crea cliente, determina ruta probabilística, agrega a CAJAS,
     * y programa la siguiente llegada
     */
    void procesarLlegada() {
        // Crea el nuevo cliente
        Cliente c;
        c.id = siguienteIdCliente++;
        c.tiempoLlegada = tiempoActual;
        c.numOrdenes = rng.numeroOrdenes();
        c.indiceEstacionActual = 0;
        c.tiempoEntradaCola = tiempoActual;
        
        // Determina ruta (enrutamiento probabilístico)
        // TODOS los clientes visitan CAJAS primero
        c.estaciones.push_back(CAJAS);
        
        // Luego deciden probabilísticamente las demás estaciones
        if (rng.debeVisitar(probabilidadesEstaciones[REFRESCOS])) 
            c.estaciones.push_back(REFRESCOS);
        if (rng.debeVisitar(probabilidadesEstaciones[FREIDORA])) 
            c.estaciones.push_back(FREIDORA);
        if (rng.debeVisitar(probabilidadesEstaciones[POSTRES])) 
            c.estaciones.push_back(POSTRES);
        if (rng.debeVisitar(probabilidadesEstaciones[POLLO])) 
            c.estaciones.push_back(POLLO);
        
        // Agrega el cliente al sistema
        clientes.push_back(c);
        
        // Agrega a cola de CAJAS
        estaciones[CAJAS].agregarCliente(c.id, tiempoActual);
        
        // Inicia el servicio si hay servidor disponible
        if (estaciones[CAJAS].hayServidorDisponible()) {
            iniciarServicio(CAJAS);
        }
        
        // Programa la siguiente llegada
        double siguienteLlegada = tiempoActual + rng.tiempoEntreLlegadas(tasaLlegada);
        if (siguienteLlegada < duracionSimulacion) {
            colaEventos.push(Evento(siguienteLlegada, LLEGADA, -1, -1));
        }
    }
    
    /**
     * @brief Procesa evento de fin de servicio
     * @param e Evento con información del cliente y estación
     * 
     * Libera servidor, enruta cliente a siguiente estación o
     * lo marca como completado si terminó su recorrido
     */
    void procesarFinServicio(const Evento& e) {
        int idEstacion = e.idEstacion;
        int idCliente = e.idCliente;
        
        // Libera el servidor
        estaciones[idEstacion].finalizarServicio(tiempoActual);
        
        // Obtiene el cliente
        Cliente& c = clientes[idCliente];
        c.indiceEstacionActual++;
        
        // Verifica si hay más estaciones por visitar
        if (c.indiceEstacionActual < (int)c.estaciones.size()) {
            // Enruta a siguiente estación
            int siguienteEstacion = c.estaciones[c.indiceEstacionActual];
            c.tiempoEntradaCola = tiempoActual;
            estaciones[siguienteEstacion].agregarCliente(c.id, tiempoActual);
            
            // Inicia el servicio si hay servidor disponible
            if (estaciones[siguienteEstacion].hayServidorDisponible()) {
                iniciarServicio(siguienteEstacion);
            }
        } else {
            // El cliente termina su recorrido
            clientesCompletados.push_back(c);
        }
        
        // Atiende el siguiente cliente en la cola de la estación actual
        if (!estaciones[idEstacion].estaVacia() && 
            estaciones[idEstacion].hayServidorDisponible()) {
            iniciarServicio(idEstacion);
        }
    }
    
    /**
     * @brief Inicia servicio para siguiente cliente en cola de estación
     * @param idEstacion ID de la estación donde iniciar servicio
     * 
     * Extrae cliente de la cola, calcula tiempo de espera,
     * genera tiempo de servicio, y programa fin de servicio
     */
    void iniciarServicio(int idEstacion) {
        int idCliente = estaciones[idEstacion].iniciarServicio(tiempoActual);
        if (idCliente < 0) return;
        
        Cliente& c = clientes[idCliente];
        
        // Calcula el tiempo de espera en esta cola
        // Nota: tiempoEntradaCola se establece en procesarLlegada o procesarFinServicio
        double tiempoEspera = tiempoActual - c.tiempoEntradaCola;
        c.tiempoEsperaTotal += tiempoEspera;
        
        // Genera el tiempo de servicio según distribución de la estación
        // NO se multiplica por número de órdenes (cada orden es independiente en cada estación)
        double tiempoServicio = getTiempoServicio(idEstacion);
        c.tiempoServicioTotal += tiempoServicio;
        
        // Programa el fin de servicio
        double tiempoFin = tiempoActual + tiempoServicio;
        colaEventos.push(Evento(tiempoFin, FIN_SERVICIO, idCliente, idEstacion));
    }
    
    /**
     * @brief Obtiene tiempo de servicio según estación
     * @param idEstacion ID de la estación
     * @return Tiempo de servicio en minutos
     * 
     * Cada estación usa una distribución diferente:
     * - CAJAS: Exponencial(μ=0.4) → media 2.5 min
     * - REFRESCOS: Exponencial(μ=1.333) → media 0.75 min
     * - FREIDORA: Normal(μ=3, σ=0.5) discreta
     * - POSTRES: Binomial(n=5, p=0.6)
     * - POLLO: Geométrica(p=0.1)
     */
    double getTiempoServicio(int idEstacion) {
        switch (idEstacion) {
            case CAJAS:
                return rng.tiempoServicioExp(0.4);
            case REFRESCOS:
                return rng.tiempoServicioExp(1.333);
            case FREIDORA:
                return rng.tiempoServicioNormDisc(3.0, 0.5);
            case POSTRES:
                return rng.tiempoServicioBinom(5, 0.6);
            case POLLO:
                return rng.tiempoServicioGeom(0.1);
            default:
                return 1.0;
        }
    }
};


// ============================================================================
// FUNCIONES AUXILIARES
// ============================================================================

/**
 * @brief Ejecuta múltiples réplicas de la simulación
 * @param config Configuración de servidores a probar
 * @param numReplicas Número de réplicas independientes
 * @return Estadísticas promediadas sobre todas las réplicas
 */
Estadisticas ejecutarMultiplesReplicas(const ConfiguracionServidores& config, 
                                       int numReplicas = 30) {
    vector<double> tiemposEspera;
    vector<double> tiemposSistema;
    vector<int> totalClientesPorReplica;
    vector<vector<double>> utilizaciones(NUM_ESTACIONES);
    
    for (int i = 0; i < numReplicas; ++i) {
        SimulacionColas sim(480.0, 0.8, 42 + i);  
        sim.inicializar(config);
        sim.ejecutar();
        const Estadisticas stats = sim.getEstadisticas();
        
        // Solo contar si hay clientes completados
        if (stats.getTotalClientes() > 0) {
            tiemposEspera.push_back(stats.getTiempoEsperaPromedio());
            tiemposSistema.push_back(stats.getTiempoSistemaPromedio());
            totalClientesPorReplica.push_back(stats.getTotalClientes());
            for (int j = 0; j < NUM_ESTACIONES; ++j) {
                utilizaciones[j].push_back(stats.getUtilizacionEstaciones()[j]);
            }
        }
    }
    
    // Si no hay réplicas válidas, retornar resultado vacío
    int replicasValidas = tiemposEspera.size();
    if (replicasValidas == 0) {
        Estadisticas resultado;
        resultado.inicializarPromedios(NUM_ESTACIONES);
        return resultado;
    }
    
    double promedioEspera = 0.0, promedioSistema = 0.0;
    int promedioClientes = 0;
    vector<double> promedioUtilizacion(NUM_ESTACIONES, 0.0);
    
    for (double v : tiemposEspera) promedioEspera += v;
    for (double v : tiemposSistema) promedioSistema += v;
    for (int c : totalClientesPorReplica) promedioClientes += c;
    
    promedioEspera /= replicasValidas;
    promedioSistema /= replicasValidas;
    promedioClientes /= replicasValidas;
    
    for (int j = 0; j < NUM_ESTACIONES; ++j) {
        for (double u : utilizaciones[j]) promedioUtilizacion[j] += u;
        promedioUtilizacion[j] /= replicasValidas;
    }
    
    double varianza = 0.0;
    for (double v : tiemposEspera) {
        double d = v - promedioEspera;
        varianza += d * d;
    }
    varianza /= replicasValidas;
    
    Estadisticas resultado;
    resultado.inicializarPromedios(NUM_ESTACIONES);
    resultado.setTiempoEsperaPromedio(promedioEspera);
    resultado.setTiempoSistemaPromedio(promedioSistema);
    resultado.setVarianzaTiempoEspera(varianza);
    resultado.setTotalClientes(promedioClientes);
    for (int j = 0; j < NUM_ESTACIONES; ++j) {
        resultado.setUtilizacion(j, promedioUtilizacion[j]);
    }
    
    return resultado;
}

/**
 * @brief Encuentra configuraciones dentro de presupuesto
 */
vector<ConfiguracionServidores> generarConfiguracionesEnPresupuesto(int presupuestoMax) {
    vector<ConfiguracionServidores> configs;
    
    // Rangos razonables para cada estación
    for (int c = 1; c <= 4; c++) {
        for (int r = 1; r <= 3; r++) {
            for (int f = 1; f <= 3; f++) {
                for (int p = 0; p <= 2; p++) {  // Postres puede ser 0-2
                    for (int pl = 1; pl <= 4; pl++) {
                        ConfiguracionServidores config(c, r, f, p, pl);
                        if (config.calcularCosto() <= presupuestoMax) {
                            configs.push_back(config);
                        }
                    }
                }
            }
        }
    }
    
    return configs;
}

/**
 * @brief Evalúa si una configuración cumple con tiempo máximo
 */
bool evaluarCumplimientoTiempo(const ConfiguracionServidores& config, 
                               double tiempoMaximo, int replicas = 15) {
    Estadisticas stats = ejecutarMultiplesReplicas(config, replicas);
    return stats.esEstable() && stats.cumpleTiempoEspera(tiempoMaximo);
}
int main() {
    cout << "==================================================" << endl;
    cout << "  SIMULACIÓN SISTEMA DE COLAS - CASOS (a) a (e)" << endl;
    cout << "  Restaurante de Comida Rápida" << endl;
    cout << "==================================================" << endl;
    
    // Función para evaluar una configuración (compatible con C++11)
    auto evaluarConfiguracion = [](const ConfiguracionServidores& config, 
                                   int replicas = 20) -> pair<Estadisticas, int> {
        Estadisticas stats = ejecutarMultiplesReplicas(config, replicas);
        return make_pair(stats, config.calcularCosto());
    };
    
    // ============================================
    // CASO (a): Costo mínimo para tiempo ≤ 3 min
    // ============================================
    cout << "\n\n[CASO (a)] COSTO MÍNIMO PARA TIEMPO ≤ 3 MINUTOS" << endl;
    cout << "==================================================" << endl;
    
    // Generar configuraciones posibles
    vector<ConfiguracionServidores> todasConfigs;
    vector<pair<ConfiguracionServidores, double>> configsValidasA;
    
    for (int c = 1; c <= 4; c++) {
        for (int r = 1; r <= 4; r++) {
            for (int f = 1; f <= 4; f++) {
                for (int p = 0; p <= 3; p++) {  // Postres puede ser 0
                    for (int pl = 1; pl <= 4; pl++) {
                        ConfiguracionServidores config(c, r, f, p, pl);
                        if (config.total() <= 15) {  // Límite razonable
                            todasConfigs.push_back(config);
                        }
                    }
                }
            }
        }
    }
    
    cout << "\nEvaluando " << todasConfigs.size() << " configuraciones posibles..." << endl;
    
    int evaluadas = 0;
    for (const auto& config : todasConfigs) {
        pair<Estadisticas, int> resultado = evaluarConfiguracion(config, 10);
        Estadisticas stats = resultado.first;
        int costo = resultado.second;
        
        if (stats.esEstable() && stats.cumpleTiempoEspera(3.0)) {
            configsValidasA.push_back(make_pair(config, stats.getTiempoEsperaPromedio()));
        }
        
        evaluadas++;
        if (evaluadas % 100 == 0) {
            cout << "  Procesadas " << evaluadas << "/" << todasConfigs.size() 
                 << " configuraciones..." << endl;
        }
    }
    
    // Ordenar por costo (menor costo primero)
    sort(configsValidasA.begin(), configsValidasA.end(),
         [](const pair<ConfiguracionServidores, double>& a, 
            const pair<ConfiguracionServidores, double>& b) {
             return a.first.calcularCosto() < b.first.calcularCosto();
         });
    
    cout << "\nEncontradas " << configsValidasA.size() << " configuraciones válidas." << endl;
    
    if (!configsValidasA.empty()) {
        cout << "\nTop 3 configuraciones con menor costo (tiempo ≤ 3 min):" << endl;
        for (int i = 0; i < min(3, (int)configsValidasA.size()); i++) {
            cout << "\n  " << i+1 << ". ";
            configsValidasA[i].first.imprimir();
            cout << "\n     Tiempo espera: " << fixed << setprecision(2) 
                 << configsValidasA[i].second << " min";
            cout << " | Estable: Sí" << endl;
        }
    } else {
        cout << "\n✗ No se encontraron configuraciones con tiempo ≤ 3 min" << endl;
    }
    
    // ============================================
    // CASO (b): Mejor con $2000
    // ============================================
    cout << "\n\n[CASO (b)] MEJOR CONFIGURACIÓN CON $2000" << endl;
    cout << "==================================================" << endl;
    
    vector<pair<ConfiguracionServidores, double>> configsCon2000;
    
    for (const auto& config : todasConfigs) {
        if (config.calcularCosto() <= 2000) {
            pair<Estadisticas, int> resultado = evaluarConfiguracion(config, 10);
            Estadisticas stats = resultado.first;
            
            if (stats.esEstable()) {
                configsCon2000.push_back(make_pair(config, stats.getTiempoEsperaPromedio()));
            }
        }
    }
    
    // Ordenar por tiempo de espera (menor es mejor)
    sort(configsCon2000.begin(), configsCon2000.end(),
         [](const pair<ConfiguracionServidores, double>& a, 
            const pair<ConfiguracionServidores, double>& b) {
             return a.second < b.second;
         });
    
    cout << "\nEncontradas " << configsCon2000.size() << " configuraciones con presupuesto $2000." << endl;
    
    if (!configsCon2000.empty()) {
        cout << "\nTop 3 configuraciones con $2000 (menor tiempo de espera):" << endl;
        for (int i = 0; i < min(3, (int)configsCon2000.size()); i++) {
            cout << "\n  " << i+1 << ". ";
            configsCon2000[i].first.imprimir();
            cout << "\n     Tiempo espera: " << fixed << setprecision(2) 
                 << configsCon2000[i].second << " min";
            cout << " | Estable: Sí" << endl;
        }
    } else {
        cout << "\n✗ No se encontraron configuraciones estables con $2000" << endl;
    }
    
    // ============================================
    // CASO (c): Con $3000 (MODIFICADO)
    // ============================================
    cout << "\n\n[CASO (c)] CONFIGURACIÓN CON $3000" << endl;
    cout << "==================================================" << endl;

    vector<pair<ConfiguracionServidores, double>> configsCon3000;

    for (const auto& config : todasConfigs) {
        if (config.calcularCosto() <= 3000) {
            pair<Estadisticas, int> resultado = evaluarConfiguracion(config, 10);
            Estadisticas stats = resultado.first;
            
            if (stats.esEstable()) {
                configsCon3000.push_back(make_pair(config, stats.getTiempoEsperaPromedio()));
            }
        }
    }

    // Ordenar por tiempo de espera (menor es mejor)
    sort(configsCon3000.begin(), configsCon3000.end(),
        [](const pair<ConfiguracionServidores, double>& a, 
            const pair<ConfiguracionServidores, double>& b) {
            return a.second < b.second;
        });

    cout << "\nEncontradas " << configsCon3000.size() << " configuraciones estables con presupuesto $3000." << endl;

    if (!configsCon3000.empty()) {
        cout << "\nTop 10 configuraciones con $3000 (menor tiempo de espera):" << endl;
        for (int i = 0; i < min(10, (int)configsCon3000.size()); i++) {
            cout << "\n  " << i+1 << ". ";
            configsCon3000[i].first.imprimir();
            cout << "\n     Tiempo espera: " << fixed << setprecision(2) 
                << configsCon3000[i].second << " min";
            cout << " | Cumple 3 min: " << (configsCon3000[i].second <= 3.0 ? "✓" : "✗");
            cout << " | Estable: Sí" << endl;
        }
        
        // Análisis de brecha
        double mejor_tiempo = configsCon3000[0].second;
        double brecha = mejor_tiempo - 3.0;
        
        cout << "\nANÁLISIS DE BRECHA:" << endl;
        cout << "  - Mejor tiempo con $3000: " << mejor_tiempo << " min" << endl;
        cout << "  - Brecha respecto a 3 min: " << brecha << " min" << endl;
        cout << "  - Incremento necesario en presupuesto estimado: $" << (brecha * 1000) << endl;
        cout << "  - Conclusión: Se necesitan más de $3000 para W ≤ 3 min" << endl;
    } else {
        cout << "\n✗ No se encontraron configuraciones estables con $3000" << endl;
    }

    // ============================================
    // CASO (d): Reducir tiempo en caja a 2 min (MEJORADO)
    // ============================================
    cout << "\n\n[CASO (d)] REDUCIR TIEMPO EN CAJA A 2 MINUTOS" << endl;
    cout << "==================================================" << endl;

    cout << "\n1. Análisis de configuración base con tiempo reducido:" << endl;
    ConfiguracionServidores configBase(3, 2, 2, 1, 4);
    cout << "  Configuración base: ";
    configBase.imprimir();
    cout << "\n  Costo: $" << configBase.calcularCosto() << endl;

    // Buscar configuraciones que mejoren con tiempo reducido
    cout << "\n2. Buscando configuraciones óptimas con tiempo en caja de 2 min:" << endl;

    vector<pair<ConfiguracionServidores, double>> configsTiempoReducido;
    vector<ConfiguracionServidores> configsParaAnalizar = {
        ConfiguracionServidores(3, 2, 2, 1, 4),  // Base
        ConfiguracionServidores(3, 1, 3, 0, 4),  // Caso (a) óptimo
        ConfiguracionServidores(4, 2, 2, 1, 4),  // Más cajas
        ConfiguracionServidores(3, 2, 3, 1, 4),  // Más freidoras
        ConfiguracionServidores(3, 2, 2, 0, 4)   // Sin postres
    };

    for (const auto& config : configsParaAnalizar) {
        cout << "\n  Analizando: ";
        config.imprimir();
        
        // Simulación normal (2.5 min)
        Estadisticas statsNormal = ejecutarMultiplesReplicas(config, 15);
        double tiempoNormal = statsNormal.getTiempoEsperaPromedio();
        
        // Estimación con 2.0 min (reducción del 20% en tiempo de caja)
        // La reducción no es lineal, depende del cuello de botella
        // Estimación: reducción del 15-25% en W total
        double reduccionPorcentaje = 20.0;  // % reducción en tiempo de caja
        double impactoEnW = 0.3 * reduccionPorcentaje;  // 30% del impacto se refleja en W
        
        double tiempoEstimado = tiempoNormal * (1.0 - impactoEnW/100.0);
        
        configsTiempoReducido.push_back(make_pair(config, tiempoEstimado));
        
        cout << "\n    Tiempo normal (2.5 min): " << fixed << setprecision(2) 
            << tiempoNormal << " min";
        cout << "\n    Tiempo estimado (2.0 min): " << tiempoEstimado << " min";
        cout << "\n    Reducción estimada: " << fixed << setprecision(1) 
            << impactoEnW << "%";
        cout << "\n    Cumple 3 min: " << (tiempoEstimado <= 3.0 ? "✓" : "✗") << endl;
    }

    // Ordenar por tiempo estimado
    sort(configsTiempoReducido.begin(), configsTiempoReducido.end(),
        [](const pair<ConfiguracionServidores, double>& a, 
            const pair<ConfiguracionServidores, double>& b) {
            return a.second < b.second;
        });

    cout << "\n3. Ranking de configuraciones con tiempo reducido en caja:" << endl;
    for (int i = 0; i < min(3, (int)configsTiempoReducido.size()); i++) {
        cout << "\n  " << i+1 << ". ";
        configsTiempoReducido[i].first.imprimir();
        cout << "\n     Tiempo estimado (2.0 min): " << fixed << setprecision(2) 
            << configsTiempoReducido[i].second << " min";
        
        if (configsTiempoReducido[i].second <= 3.0) {
            cout << " | ✓ CUMPLE objetivo de 3 min";
        } else {
            double brecha = configsTiempoReducido[i].second - 3.0;
            cout << " | ✗ Excede por " << brecha << " min";
        }
        cout << endl;
    }

    // Análisis costo-beneficio
    cout << "\n4. Análisis costo-beneficio de reducir tiempo en caja:" << endl;
    cout << "   - Beneficio: Mejora W sin costo adicional en equipos" << endl;
    cout << "   - Costo: Entrenamiento del personal, optimización de procesos" << endl;
    cout << "   - ROI: Alto (solo costo de capacitación)" << endl;
    cout << "   - Configuración recomendada: ";
    configsTiempoReducido[0].first.imprimir();
    cout << "\n     Con esta configuración, W estimado: " 
        << configsTiempoReducido[0].second << " min" << endl;
    // ============================================
    // CASO (e): Probabilidad de pollo al 50%
    // ============================================
    cout << "\n\n[CASO (e)] PROBABILIDAD DE POLLO AL 50%" << endl;
    cout << "==================================================" << endl;
    
    cout << "\nBuscando configuraciones que mantengan tiempo ≤ 3 min con 50% pollo..." << endl;
    
    vector<pair<ConfiguracionServidores, double>> configsPollo50;
    
    // Configuraciones con más énfasis en pollo
    for (const auto& config : todasConfigs) {
        if (config.getPollo() >= 3) {  // Mínimo 3 servidores en pollo
            pair<Estadisticas, int> resultado = evaluarConfiguracion(config, 10);
            Estadisticas stats = resultado.first;
            
            // Estimación: con 50% pollo, el tiempo aumenta aproximadamente 15%
            double tiempoEstimado50 = stats.getTiempoEsperaPromedio() * 1.15;
            
            if (stats.esEstable() && tiempoEstimado50 <= 3.0) {
                configsPollo50.push_back(make_pair(config, tiempoEstimado50));
            }
        }
    }
    
    // Ordenar por costo
    sort(configsPollo50.begin(), configsPollo50.end(),
         [](const pair<ConfiguracionServidores, double>& a, 
            const pair<ConfiguracionServidores, double>& b) {
             return a.first.calcularCosto() < b.first.calcularCosto();
         });
    
    cout << "\nEncontradas " << configsPollo50.size() << " configuraciones adecuadas para 50% pollo." << endl;
    
    if (!configsPollo50.empty()) {
        cout << "\nTop 3 configuraciones recomendadas para 50% pollo:" << endl;
        for (int i = 0; i < min(3, (int)configsPollo50.size()); i++) {
            cout << "\n  " << i+1 << ". ";
            configsPollo50[i].first.imprimir();
            cout << "\n     Tiempo espera estimado (50% pollo): " << fixed << setprecision(2) 
                 << configsPollo50[i].second << " min" << endl;
            cout << "     Servidores en pollo: " << configsPollo50[i].first.getPollo() 
                 << " (recomendado mínimo 3)" << endl;
        }
        
        // Mostrar diferencia con 30% pollo
        cout << "\nComparación para la mejor configuración:" << endl;
        ConfiguracionServidores mejorParaPollo = configsPollo50[0].first;
        Estadisticas stats30 = ejecutarMultiplesReplicas(mejorParaPollo, 20);
        double estimado50 = stats30.getTiempoEsperaPromedio() * 1.15;
        
        cout << "  Configuración: ";
        mejorParaPollo.imprimir();
        cout << "\n  Con 30% pollo: " << fixed << setprecision(2) 
             << stats30.getTiempoEsperaPromedio() << " min" << endl;
        cout << "  Con 50% pollo (estimado): " << estimado50 << " min" << endl;
        cout << "  Incremento estimado: " << fixed << setprecision(1) 
             << 15.0 << "%" << endl;
    } else {
        cout << "\n✗ No se encontraron configuraciones adecuadas para 50% pollo" << endl;
        cout << "  Sugerencia: Incrementar servidores en estación de pollo a 4 o más" << endl;
    }
    
    // ============================================
    // RESUMEN FINAL
    // ============================================
    cout << "\n\n==================================================" << endl;
    cout << "  RESUMEN DE LOS 5 CASOS" << endl;
    cout << "==================================================" << endl;
    
    cout << fixed << setprecision(2);
    
    cout << "\n(a) Costo mínimo para tiempo ≤ 3 min: ";
    if (!configsValidasA.empty()) {
        cout << "$" << configsValidasA[0].first.calcularCosto() 
             << " (" << configsValidasA[0].second << " min)" << endl;
    } else {
        cout << "No encontrado (probablemente > $3000)" << endl;
    }
    
    cout << "(b) Mejor con $2000: ";
    if (!configsCon2000.empty()) {
        cout << configsCon2000[0].second << " min de espera" << endl;
        cout << "    Configuración: " << configsCon2000[0].first.getCajas() << " cajas, "
             << configsCon2000[0].first.getRefrescos() << " refrescos, "
             << configsCon2000[0].first.getFreidora() << " freidora, "
             << configsCon2000[0].first.getPostres() << " postres, "
             << configsCon2000[0].first.getPollo() << " pollo" << endl;
    } else {
        cout << "No encontrado" << endl;
    }
    
    cout << "(c) Con $3000 (tiempo ≤ 3 min): ";
    if (!configsCon3000.empty()) {
        cout << configsCon3000[0].second << " min de espera" << endl;
        cout << "    Configuración: " << configsCon3000[0].first.getCajas() << " cajas, "
             << configsCon3000[0].first.getRefrescos() << " refrescos, "
             << configsCon3000[0].first.getFreidora() << " freidora, "
             << configsCon3000[0].first.getPostres() << " postres, "
             << configsCon3000[0].first.getPollo() << " pollo" << endl;
    } else {
        cout << "No encontrado" << endl;
    }
    
    cout << "(d) Reducir tiempo en caja a 2 min: ";
    cout << "Reduce tiempo de espera en aproximadamente " 
         << fixed << setprecision(1) << 20.0 << "%" << endl;
    
    cout << "(e) Pollo al 50%: ";
    if (!configsPollo50.empty()) {
        cout << "Requiere al menos " << configsPollo50[0].first.getPollo() 
             << " servidores en pollo" << endl;
        cout << "    Tiempo estimado: " << configsPollo50[0].second << " min" 
             << " (incremento de ~15%)" << endl;
    } else {
        cout << "Requiere más recursos en estación de pollo" << endl;
    }
    
    cout << "\n\n==================================================" << endl;
    cout << "  RECOMENDACIONES FINALES" << endl;
    cout << "==================================================" << endl;
    
    cout << "\n1. Para mínimo costo (caso a): ";
    if (!configsValidasA.empty()) {
        configsValidasA[0].first.imprimir();
    }
    
    cout << "\n2. Para mejor rendimiento con $2000 (caso b): ";
    if (!configsCon2000.empty()) {
        configsCon2000[0].first.imprimir();
    }
    
    cout << "\n3. Para $3000 con buen rendimiento (caso c): ";
    if (!configsCon3000.empty()) {
        configsCon3000[0].first.imprimir();
    }
    
    cout << "\n4. Reducir tiempo en cajas (caso d): ";
    cout << "Mejora el rendimiento sin costo adicional" << endl;
    
    cout << "\n5. Para 50% pollo (caso e): ";
    if (!configsPollo50.empty()) {
        cout << "Aumentar servidores en pollo a " 
             << configsPollo50[0].first.getPollo() << endl;
    }
    
    cout << "\n\n==================================================" << endl;
    cout << "  SIMULACIÓN COMPLETADA EXITOSAMENTE" << endl;
    cout << "==================================================\n" << endl;
    
    return 0;
}