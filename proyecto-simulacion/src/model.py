"""
Módulo de simulación del sistema de colas del restaurante.
Implementa el modelo SimPy con generación de clientes y procesamiento de servicios.
"""

import simpy
import numpy as np
import pandas as pd
import os
from .distributions import get_rng, load_config, sample_from_config


# ========================================================================
# PROCESO DE CLIENTE
# ========================================================================

def customer_process(env, id, resources, probs, service_configs, rng, metrics):
    """
    Proceso que simula el recorrido de un cliente por el restaurante.
    env: Entorno de SimPy
    id: ID del cliente
    resources: Diccionario de recursos SimPy (estaciones)
    probs: Probabilidades de visitar cada estación
    service_configs: Configuraciones de tiempos de servicio
    rng: Generador aleatorio
    metrics: Diccionario para acumular métricas
    """
    arrival_time = env.now
    
    # Registro de eventos del cliente
    customer_data = {
        'id': id,
        'arrival_time': arrival_time,
        'stations_visited': [],
        'service_times': {},
        'wait_times': {},
        'start_times': {},
        'end_times': {}
    }
    
    # CAJAS (obligatorio)
    station = 'cashiers'
    with resources[station].request() as request:
        yield request
        
        wait_time = env.now - arrival_time
        start_service = env.now
        
        # Genera tiempo de servicio
        service_time = sample_from_config(rng, service_configs[station])
        
        yield env.timeout(service_time)
        
        end_service = env.now
        
        customer_data['stations_visited'].append(station)
        customer_data['wait_times'][station] = wait_time
        customer_data['service_times'][station] = service_time
        customer_data['start_times'][station] = start_service
        customer_data['end_times'][station] = end_service
        
        # Actualiza métricas de estación
        metrics['station_metrics'][station]['visits'] += 1
        metrics['station_metrics'][station]['total_service_time'] += service_time
        metrics['station_metrics'][station]['total_wait_time'] += wait_time
    
    # OTRAS ESTACIONES (condicionales)
    optional_stations = ['drinks', 'fryer', 'desserts', 'chicken']
    
    for station in optional_stations:
        # Decide qué estación visitar
        if rng.random() < probs[station]:
            with resources[station].request() as request:
                yield request
                
                wait_time = env.now - arrival_time
                start_service = env.now
                
                # Genera tiempo de servicio
                service_time = sample_from_config(rng, service_configs[station])
                
                yield env.timeout(service_time)
                
                end_service = env.now
                
                customer_data['stations_visited'].append(station)
                customer_data['wait_times'][station] = wait_time
                customer_data['service_times'][station] = service_time
                customer_data['start_times'][station] = start_service
                customer_data['end_times'][station] = end_service
                
                # Actualiza métricas de estación
                metrics['station_metrics'][station]['visits'] += 1
                metrics['station_metrics'][station]['total_service_time'] += service_time
                metrics['station_metrics'][station]['total_wait_time'] += wait_time
    
    # Tiempo total en el sistema
    departure_time = env.now
    time_in_system = departure_time - arrival_time
    
    customer_data['departure_time'] = departure_time
    customer_data['time_in_system'] = time_in_system
    
    # Guarda datos del cliente
    metrics['customers'].append(customer_data)


# ========================================================================
# GENERADOR DE LLEGADAS
# ========================================================================

def arrival_generator(env, resources, probs, service_configs, rng, metrics,
                      lambda_arrivals, horizon):
    """
    Genera llegadas de clientes según proceso de Poisson.
    env: Entorno de SimPy
    resources: Diccionario de recursos
    probs: Probabilidades de visitar estaciones
    service_configs: Configuraciones de tiempos de servicio
    rng: Generador aleatorio
    metrics: Diccionario de métricas
    lambda_arrivals: Tasa de llegada (clientes por minuto)
    horizon: Horizonte de simulación (minutos)
    """
    customer_id = 0
    
    while env.now < horizon:
        # Genera tiempo entre llegadas (exponencial)
        interarrival_time = rng.exponential(scale=lambda_arrivals)
        
        yield env.timeout(interarrival_time)
        
        if env.now < horizon:
            customer_id += 1
            env.process(customer_process(
                env, customer_id, resources, probs,
                service_configs, rng, metrics
            ))


# ========================================================================
# FUNCIÓN PRINCIPAL DE SIMULACIÓN
# ========================================================================

def run_replica(config, seed=None, verbose=False):
    """
    Ejecuta una réplica de la simulación.
    config: Configuración del sistema (diccionario o ruta a YAML)
    seed: Semilla aleatoria para reproducibilidad
    verbose: Si True, imprime información detallada
    Retorna diccionario con métricas de la réplica
    """
    # Carga configuración si es string
    if isinstance(config, str):
        config = load_config(config)
    
    # Configura semilla
    if seed is None:
        seed = config["simulation"].get("random_seed")
    
    rng = get_rng(seed)
    
    # Crea entorno SimPy
    env = simpy.Environment()
    
    # Crea recursos (servidores por estación)
    resources = {}
    for station, capacity in config["resources"].items():
        resources[station] = simpy.Resource(env, capacity)
    
    # Parámetros de simulación
    lambda_arrivals = config["arrivals"]["lambda"]
    horizon = config["simulation"]["horizon_minutes"]
    probs = config["probabilities"]
    service_configs = config["service_times"]
    
    # Inicializa métricas
    metrics = {
        'customers': [],
        'station_metrics': {
            station: {
                'visits': 0,
                'total_service_time': 0.0,
                'total_wait_time': 0.0,
                'capacity': capacity
            }
            for station, capacity in config["resources"].items()
        },
        'config': {
            'seed': seed,
            'lambda': lambda_arrivals,
            'horizon': horizon,
            'resources': config["resources"].copy()
        }
    }
    
    # Inicia generador de llegadas
    env.process(arrival_generator(
        env, resources, probs, service_configs, rng, metrics,
        lambda_arrivals, horizon
    ))
    
    # Ejecuta simulación
    if verbose:
        print(f"\nEjecutando simulación (seed={seed}, T={horizon} min)...")
    
    env.run()
    
    if verbose:
        print("✓ Simulación completada. Clientes atendidos: "
              f"{len(metrics['customers'])}")
    
    return metrics


# ========================================================================
# PROCESAMIENTO DE MÉTRICAS
# ========================================================================

def compute_metrics(replica_results):
    """
    Calcula métricas agregadas a partir de los resultados de una réplica.
    replica_results: Resultados de run_replica()
    Retorna diccionario con métricas calculadas
    """
    customers = replica_results['customers']
    station_metrics = replica_results['station_metrics']
    horizon = replica_results['config']['horizon']
    
    if len(customers) == 0:
        return {
            'W_mean': 0,
            'W_variance': 0,
            'W_median': 0,
            'W_std': 0,
            'num_customers': 0,
            'utilization': {station: 0 for station in station_metrics},
            'avg_wait_time': {station: 0 for station in station_metrics}
        }
    
    # Tiempo en sistema (W)
    times_in_system = [c['time_in_system'] for c in customers]
    W_mean = np.mean(times_in_system)
    W_variance = np.var(times_in_system, ddof=1) if len(times_in_system) > 1 else 0
    W_median = np.median(times_in_system)
    W_std = np.std(times_in_system, ddof=1) if len(times_in_system) > 1 else 0
    
    # Utilización por estación
    utilization = {}
    avg_wait_time = {}
    
    for station, stats in station_metrics.items():
        if stats['visits'] > 0:
            # Utilización = tiempo total ocupado / (capacidad * horizonte)
            total_busy_time = stats['total_service_time']
            max_available_time = stats['capacity'] * horizon
            utilization[station] = total_busy_time / max_available_time \
                                   if max_available_time > 0 else 0
            
            # Tiempo de espera promedio
            avg_wait_time[station] = stats['total_wait_time'] / stats['visits']
        else:
            utilization[station] = 0
            avg_wait_time[station] = 0
    
    return {
        'W_mean': W_mean,
        'W_variance': W_variance,
        'W_median': W_median,
        'W_std': W_std,
        'W_min': np.min(times_in_system),
        'W_max': np.max(times_in_system),
        'num_customers': len(customers),
        'utilization': utilization,
        'avg_wait_time': avg_wait_time,
        'station_visits': {station: stats['visits'] 
                           for station, stats in station_metrics.items()}
    }


# ========================================================================
# FUNCIONES DE UTILIDAD
# ========================================================================

def save_replica_results(replica_results, output_file):
    """
    Guarda los resultados detallados de una réplica en CSV.
    replica_results: Resultados de run_replica()
    output_file: Ruta del archivo de salida
    """
    customers = replica_results['customers']
    
    # Crea DataFrame con datos de clientes
    data = []
    for c in customers:
        row = {
            'customer_id': c['id'],
            'arrival_time': c['arrival_time'],
            'departure_time': c['departure_time'],
            'time_in_system': c['time_in_system'],
            'stations_visited': ','.join(c['stations_visited'])
        }
        
        # Agrega tiempos por estación
        for station in ['cashiers', 'drinks', 'fryer', 'desserts', 'chicken']:
            row[f'{station}_wait'] = c['wait_times'].get(station, 0)
            row[f'{station}_service'] = c['service_times'].get(station, 0)
        
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    
    return df


# ========================================================================
# EJECUCIÓN DIRECTA
# ========================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Ejecuta una réplica de simulación')
    parser.add_argument('--config', default='config.yaml', help='Archivo de configuración')
    parser.add_argument('--seed', type=int, default=None, help='Semilla aleatoria')
    parser.add_argument('--output', default=None, help='Archivo de salida (CSV)')
    parser.add_argument('--verbose', action='store_true', help='Modo verbose')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  EJECUCIÓN DE RÉPLICA DE SIMULACIÓN")
    print("="*70)
    
    # Ejecuta réplica
    results = run_replica(args.config, seed=args.seed, verbose=True)
    
    # Calcula métricas
    metrics = compute_metrics(results)
    
    print("\nMÉTRICAS DE LA RÉPLICA:")
    print(f"  Clientes atendidos: {metrics['num_customers']}")
    print(f"  W (tiempo promedio en sistema): {metrics['W_mean']:.4f} min")
    print(f"  Varianza de W: {metrics['W_variance']:.4f}")
    print(f"  Mediana de W: {metrics['W_median']:.4f} min")
    print(f"  Desv. Est. de W: {metrics['W_std']:.4f}")
    print(f"  W mínimo: {metrics['W_min']:.4f} min")
    print(f"  W máximo: {metrics['W_max']:.4f} min")
    
    print("\nUTILIZACIÓN POR ESTACIÓN:")
    for station, util in metrics['utilization'].items():
        visits = metrics['station_visits'][station]
        wait = metrics['avg_wait_time'][station]
        print(f"  {station:12s}: {util:6.2%} | Visitas: {visits:4d} |"
              f" Espera prom: {wait:6.2f} min")
    
    # Guarda resultados si se especifica
    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        save_replica_results(results, args.output)
        print(f"\n✓ Resultados guardados en: {args.output}")
    
    print("="*70 + "\n")
