"""
Módulo de optimización y búsqueda de configuraciones óptimas.
"""

import numpy as np
import pandas as pd
import itertools
import os
from multiprocessing import Pool, cpu_count
from .model1 import run_replica, compute_metrics
from .distributions import load_config
import copy


# ========================================================================
# CÁLCULO DE COSTOS Y VALIDACIÓN
# ========================================================================

def calculate_cost(config_resources, costs):
    """
    Calcula el costo total de una configuración de recursos.
    
    Args:
        config_resources: Dict con número de servidores por estación
        costs: Dict con costos por tipo de equipo
    
    Returns:
        int: Costo total en dólares
    """
    total_cost = 0
    
    # Mapeo de estaciones a tipos de equipo
    equipment_map = {
        'cashiers': 'cashiers',
        'drinks': 'drinks',
        'fryer': 'fryer',
        'desserts': 'fryer',  # Los postres usan la freidora
        'chicken': 'chicken'
    }
    
    for station, capacity in config_resources.items():
        equipment_type = equipment_map.get(station, station)
        unit_cost = costs.get(equipment_type, 0)
        total_cost += capacity * unit_cost
    
    return total_cost

def is_valid_configuration(config_resources, max_collaborators, max_budget, costs):
    """
    Verifica si una configuración cumple con las restricciones.
    
    Args:
        config_resources: Dict con número de servidores
        max_collaborators: Máximo número total de colaboradores
        max_budget: Presupuesto máximo
        costs: Costos por equipo
    
    Returns:
        tuple: (is_valid, total_collaborators, total_cost)
    """
    total_collaborators = sum(config_resources.values())
    total_cost = calculate_cost(config_resources, costs)
    
    is_valid = (total_collaborators <= max_collaborators) and (total_cost <= max_budget)
    
    return is_valid, total_collaborators, total_cost


# ========================================================================
# EJECUCIÓN DE MÚLTIPLES RÉPLICAS
# ========================================================================

def _run_single_replica(args):
    """
    Función auxiliar para ejecutar una réplica (debe estar en el nivel superior
    del módulo para ser serializable por multiprocessing).
    
    Args:
        args: Tupla con (config, seed)
    
    Returns:
        dict: Métricas de la réplica
    """
    config, seed = args
    results = run_replica(config, seed=seed, verbose=False)
    return compute_metrics(results)
    
def run_replicas_parallel(config, num_replicas, base_seed=42, num_processes=None):
    """
    Ejecuta múltiples réplicas en paralelo.
    
    Args:
        config: Configuración del sistema
        num_replicas: Número de réplicas a ejecutar
        base_seed: Semilla base
        num_processes: Número de procesos paralelos (None = auto)
    
    Returns:
        list: Lista de métricas de cada réplica
    """
    if num_processes is None:
        num_processes = min(cpu_count(), num_replicas)
    
    # Prepara argumentos: lista de tuplas (config, seed)
    args_list = [(config, base_seed + i) for i in range(num_replicas)]
    
    # Ejecuta en paralelo usando la función de nivel superior
    with Pool(processes=num_processes) as pool:
        metrics_list = pool.map(_run_single_replica, args_list)
    
    return metrics_list

def aggregate_replica_metrics(metrics_list):
    """
    Agrega métricas de múltiples réplicas.
    
    Args:
        metrics_list: Lista de métricas de réplicas
    
    Returns:
        dict: Métricas agregadas (media, IC, etc.)
    """
    if not metrics_list:
        return None
    
    # Extrae W de todas las réplicas
    W_means = [m['W_mean'] for m in metrics_list]
    W_variances = [m['W_variance'] for m in metrics_list]
    
    # Calcula estadísticos
    W_mean_avg = np.mean(W_means)
    W_mean_std = np.std(W_means, ddof=1) if len(W_means) > 1 else 0
    W_var_avg = np.mean(W_variances)
    
    # Intervalo de confianza 95% para la media
    z = 1.96  # Para 95% de confianza
    n = len(W_means)
    W_mean_ci = z * W_mean_std / np.sqrt(n) if n > 0 else 0
    
    # Utilización promedio por estación
    stations = metrics_list[0]['utilization'].keys()
    avg_utilization = {}
    
    for station in stations:
        utils = [m['utilization'][station] for m in metrics_list]
        avg_utilization[station] = np.mean(utils)
    
    return {
        'W_mean': W_mean_avg,
        'W_std': W_mean_std,
        'W_ci_95': W_mean_ci,
        'W_variance': W_var_avg,
        'utilization': avg_utilization,
        'num_replicas': n
    }


# ========================================================================
# BÚSQUEDA POR REJILLA CON PODA
# ========================================================================

def grid_search_configurations(base_config, budget, target_wait_time, 
                               max_servers_per_station=5, num_replicas=200,
                               verbose=True):
    """
    Búsqueda exhaustiva por rejilla con poda para encontrar configuraciones óptimas.
    
    Args:
        base_config: Configuración base del sistema
        budget: Presupuesto máximo
        target_wait_time: Tiempo objetivo (None = minimizar sin restricción)
        max_servers_per_station: Límite superior de servidores por estación
        num_replicas: Número de réplicas por configuración
        verbose: Imprimir progreso
    
    Returns:
        list: Top configuraciones encontradas
    """
    costs = base_config['costs']
    max_collaborators = base_config['constraints']['max_collaborators']
    
    stations = ['cashiers', 'drinks', 'fryer', 'desserts', 'chicken']
    
    # Genera todas las combinaciones posibles
    ranges = [range(1, max_servers_per_station + 1) for _ in stations]
    all_combinations = itertools.product(*ranges)
    
    valid_configs = []
    evaluated_count = 0
    
    if verbose:
        print(f"\nBúsqueda por rejilla (presupuesto: ${budget}, objetivo W: {target_wait_time or 'minimizar'})")
    
    for combo in all_combinations:
        config_resources = dict(zip(stations, combo))
        
        # Valida restricciones
        is_valid, total_collab, total_cost = is_valid_configuration(
            config_resources, max_collaborators, budget, costs
        )
        
        if not is_valid:
            continue
        
        # Crea configuración temporal
        temp_config = copy.deepcopy(base_config)
        temp_config['resources'] = config_resources
        
        # Ejecuta réplicas
        metrics_list = run_replicas_parallel(temp_config, num_replicas)
        agg_metrics = aggregate_replica_metrics(metrics_list)
        
        evaluated_count += 1
        
        valid_configs.append({
            'resources': config_resources,
            'cost': total_cost,
            'collaborators': total_collab,
            'W_mean': agg_metrics['W_mean'],
            'W_std': agg_metrics['W_std'],
            'W_ci_95': agg_metrics['W_ci_95'],
            'W_variance': agg_metrics['W_variance'],
            'utilization': agg_metrics['utilization'],
            'num_replicas': agg_metrics['num_replicas']
        })
        
        if verbose and evaluated_count % 50 == 0:
            print(f"  Evaluadas: {evaluated_count} configuraciones válidas...")
    
    if verbose:
        print(f"✓ Total evaluadas: {evaluated_count} configuraciones")
    
    # Filtra por objetivo si existe
    if target_wait_time is not None:
        # Considera intervalo de confianza: W_mean + CI debe ser <= target
        filtered = [c for c in valid_configs
                    if (c['W_mean'] + c['W_ci_95']) <= target_wait_time]
        
        if filtered:
            # Ordena por costo (minimizar)
            filtered.sort(key=lambda x: x['cost'])
        else:
            if verbose:
                print(f"  ⚠ No se encontraron configuraciones que cumplan W ≤ {target_wait_time} min")
            filtered = []
    else:
        # Sin restricción: ordena por W_mean (minimizar)
        filtered = sorted(valid_configs, key=lambda x: x['W_mean'])
    
    return filtered


# ========================================================================
# FUNCIONES PARA ESCENARIOS ESPECÍFICOS
# ========================================================================

def scenario_a_min_cost(base_config, target_wait=3.0, num_replicas=200, verbose=True):
    """
    (a) Costo mínimo para garantizar W ≤ 3 min
    """
    if verbose:
        print("\n" + "="*70)
        print("  ESCENARIO (a): COSTO MÍNIMO PARA W ≤ 3 MIN")
        print("="*70)
    
    # Búsqueda sin restricción de presupuesto (usa valor alto)
    configs = grid_search_configurations(
        base_config,
        budget=10000,  # Presupuesto muy alto
        target_wait_time=target_wait,
        num_replicas=num_replicas,
        verbose=verbose
    )
    
    return configs[:3] if configs else []

def scenario_b_budget_2000(base_config, num_replicas=200, verbose=True):
    """
    (b) Mejor distribución con presupuesto $2000
    """
    if verbose:
        print("\n" + "="*70)
        print("  ESCENARIO (b): MEJOR CONFIGURACIÓN CON PRESUPUESTO $2000")
        print("="*70)
    
    configs = grid_search_configurations(
        base_config,
        budget=2000,
        target_wait_time=None,  # Minimiza sin restricción
        num_replicas=num_replicas,
        verbose=verbose
    )
    
    return configs[:3] if configs else []

def scenario_c_budget_3000(base_config, num_replicas=200, verbose=True):
    """
    (c) Mejor distribución con presupuesto $3000
    """
    if verbose:
        print("\n" + "="*70)
        print("  ESCENARIO (c): MEJOR CONFIGURACIÓN CON PRESUPUESTO $3000")
        print("="*70)
    
    configs = grid_search_configurations(
        base_config,
        budget=3000,
        target_wait_time=None,
        num_replicas=num_replicas,
        verbose=verbose
    )
    
    return configs[:3] if configs else []

def scenario_d_reduced_cashier_time(base_config, num_replicas=200, verbose=True):
    """
    (d) Efecto de reducir tiempo de caja a 2 min
    """
    if verbose:
        print("\n" + "="*70)
        print("  ESCENARIO (d): TIEMPO DE CAJA REDUCIDO A 2 MIN")
        print("="*70)
    
    # Modifica configuración
    modified_config = copy.deepcopy(base_config)
    modified_config['service_times']['cashiers']['mean'] = 2.0
    
    # Busca con presupuesto $3000
    configs = grid_search_configurations(
        modified_config,
        budget=3000,
        target_wait_time=None,
        num_replicas=num_replicas,
        verbose=verbose
    )
    
    return configs[:3] if configs else []

def scenario_e_increased_chicken_prob(base_config, num_replicas=200, verbose=True):
    """
    (e) Ajuste si P_pollo = 0.5 para mantener W ≤ 3 min
    """
    if verbose:
        print("\n" + "="*70)
        print("  ESCENARIO (e): P_POLLO = 0.5, MANTENER W ≤ 3 MIN")
        print("="*70)
    
    # Modifica configuración
    modified_config = copy.deepcopy(base_config)
    modified_config['probabilities']['chicken'] = 0.5
    
    # Busca con restricción W ≤ 3
    configs = grid_search_configurations(
        modified_config,
        budget=10000,  # Presupuesto alto
        target_wait_time=3.0,
        num_replicas=num_replicas,
        verbose=verbose
    )
    
    return configs[:3] if configs else []


# ========================================================================
# FUNCIONES DE REPORTE
# ========================================================================

def print_configuration_summary(configs, scenario_name):
    """Imprime resumen de configuraciones encontradas."""
    if not configs:
        print(f"\nNo se encontraron configuraciones para {scenario_name}")
        return
    
    print(f"\nTOP 3 CONFIGURACIONES - {scenario_name}")
    print("-" * 70)
    
    for i, cfg in enumerate(configs[:3], 1):
        print(f"\nCONFIGURACIÓN #{i}")
        print(f"  Recursos: {cfg['resources']}")
        print(f"  Costo: ${cfg['cost']}")
        print(f"  Colaboradores: {cfg['collaborators']}")
        print(f"  W promedio: {cfg['W_mean']:.4f} ± {cfg['W_ci_95']:.4f} min (IC 95%)")
        print(f"  Varianza W: {cfg['W_variance']:.4f}")
        print(f"  Utilización:")
        for station, util in cfg['utilization'].items():
            print(f"    {station:12s}: {util:6.2%}")

def save_configurations_to_csv(configs, output_file, scenario_name):
    """Guarda configuraciones en CSV."""
    if not configs:
        return
    
    data = []
    for cfg in configs:
        row = {
            'scenario': scenario_name,
            'cost': cfg['cost'],
            'collaborators': cfg['collaborators'],
            'W_mean': cfg['W_mean'],
            'W_std': cfg['W_std'],
            'W_ci_95': cfg['W_ci_95'],
            'W_variance': cfg['W_variance'],
            'num_replicas': cfg['num_replicas']
        }
        
        # Agrega recursos
        for station, count in cfg['resources'].items():
            row[f'servers_{station}'] = count
        
        # Agrega utilización
        for station, util in cfg['utilization'].items():
            row[f'util_{station}'] = util
        
        data.append(row)
    
    df = pd.DataFrame(data)
    
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"  ✓ Guardado en: {output_file}")


# ========================================================================
# EJECUCIÓN PRINCIPAL
# ========================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimización de configuraciones')
    parser.add_argument('--config', default='config.yaml', help='Archivo de configuración')
    parser.add_argument('--replicas', type=int, default=200, help='Réplicas por configuración')
    parser.add_argument('--scenario', choices=['a', 'b', 'c', 'd', 'e', 'all'],
                        default='all', help='Escenario a ejecutar')
    parser.add_argument('--output', default='results/optimization', help='Carpeta de salida')
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("  OPTIMIZACIÓN Y BÚSQUEDA DE CONFIGURACIONES")
    print("="*70)
    
    # Carga configuración
    base_config = load_config(args.config)
    
    os.makedirs(args.output, exist_ok=True)
    
    # Ejecuta escenarios
    scenarios_to_run = ['a', 'b', 'c', 'd', 'e'] if args.scenario == 'all' else [args.scenario]
    
    for scenario in scenarios_to_run:
        if scenario == 'a':
            configs = scenario_a_min_cost(base_config, num_replicas=args.replicas)
            print_configuration_summary(configs, "ESCENARIO (a)")
            save_configurations_to_csv(configs, f"{args.output}/scenario_a.csv", "a")
        
        elif scenario == 'b':
            configs = scenario_b_budget_2000(base_config, num_replicas=args.replicas)
            print_configuration_summary(configs, "ESCENARIO (b)")
            save_configurations_to_csv(configs, f"{args.output}/scenario_b.csv", "b")
        
        elif scenario == 'c':
            configs = scenario_c_budget_3000(base_config, num_replicas=args.replicas)
            print_configuration_summary(configs, "ESCENARIO (c)")
            save_configurations_to_csv(configs, f"{args.output}/scenario_c.csv", "c")
        
        elif scenario == 'd':
            configs = scenario_d_reduced_cashier_time(base_config, num_replicas=args.replicas)
            print_configuration_summary(configs, "ESCENARIO (d)")
            save_configurations_to_csv(configs, f"{args.output}/scenario_d.csv", "d")
        
        elif scenario == 'e':
            configs = scenario_e_increased_chicken_prob(base_config, num_replicas=args.replicas)
            print_configuration_summary(configs, "ESCENARIO (e)")
            save_configurations_to_csv(configs, f"{args.output}/scenario_e.csv", "e")
    
    print("\n" + "="*70)
    print("  OPTIMIZACIÓN COMPLETADA")
    print("="*70)
