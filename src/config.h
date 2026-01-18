#ifndef CONFIG_H
#define CONFIG_H

/**
 * Archivo de Configuración - Sistema de Simulación de Colas
 * Ajusta estos valores según sea necesario
 */

// ============= PARÁMETROS DE LLEGADAS =============
const double LAMBDA = 3.0;                // Tasa de llegadas (clientes/minuto)

// ============= PARÁMETROS DE SERVICIO =============
// Cajas
const double MU_CASHIER = 0.4;            // Tasa de servicio (clientes/minuto)

// Refrescos
const double MU_DRINKS = 1.333;           // Tasa de servicio (clientes/minuto)

// Freidora (Normal Discreta)
const double MEAN_FRYER = 3.0;            // Media (minutos)
const double STDDEV_FRYER = 0.5;          // Desviación estándar

// Postres (Binomial)
const int N_DESSERTS = 5;                 // Parámetro n
const double P_DESSERTS = 0.6;            // Parámetro p

// Pollo (Geométrica)
const double P_CHICKEN = 0.1;             // Parámetro p

// ============= PROBABILIDADES DE ENRUTAMIENTO =============
const double PROB_DRINKS = 0.9;
const double PROB_FRYER = 0.7;
const double PROB_DESSERTS = 0.25;
const double PROB_CHICKEN = 0.3;

// ============= ÓRDENES POR CLIENTE =============
const int N_ORDERS = 5;                   // Parámetro n para Binomial
const double P_ORDERS = 0.4;              // Parámetro p para Binomial

// ============= CONFIGURACIÓN DE SIMULACIÓN =============
const double SIMULATION_TIME = 480.0;     // Tiempo total (minutos = 8 horas)
const int NUM_WARMUP_MINUTES = 60;        // Minutos de warm-up a descartar
const unsigned int DEFAULT_SEED = 42;     // Semilla para reproducibilidad

// ============= CONFIGURACIÓN DE ESTACIONES =============
// Total debe ser igual a 12
const int SERVERS_CASHIER = 3;
const int SERVERS_DRINKS = 2;
const int SERVERS_FRYER = 2;
const int SERVERS_DESSERTS = 1;
const int SERVERS_CHICKEN = 4;

const int TOTAL_SERVERS = SERVERS_CASHIER + SERVERS_DRINKS + SERVERS_FRYER 
                         + SERVERS_DESSERTS + SERVERS_CHICKEN;

// ============= CRITERIOS DE VALIDACIÓN =============
const double MAX_UTILIZATION = 0.8;       // Máxima utilización permitida
const int NUM_REPLICAS = 30;              // Número de réplicas para optimización

#endif // CONFIG_H
