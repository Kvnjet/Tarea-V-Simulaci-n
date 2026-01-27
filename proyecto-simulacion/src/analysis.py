"""
Módulo de análisis estadístico y visualización.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
from pathlib import Path
from .model import run_replica, compute_metrics, save_replica_results
from .optimization import run_replicas_parallel, aggregate_replica_metrics
from .distributions import load_config
import copy


# Configuración de estilo para gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


# ========================================================================
# CÁLCULO DE MÉTRICAS ESTADÍSTICAS
# ========================================================================

def calculate_statistics(data):
    """
    Calcula métricas estadísticas completas de una muestra.
    
    Args:
        data: Array o lista de valores
    
    Returns:
        dict: Diccionario con todas las métricas
    """
    data = np.array(data)
    
    if len(data) == 0:
        return {}
    
    # Métricas básicas
    mean = np.mean(data)
    median = np.median(data)
    variance = np.var(data, ddof=1) if len(data) > 1 else 0
    std = np.std(data, ddof=1) if len(data) > 1 else 0
    
    # Moda (redondeada a entero)
    data_rounded = np.round(data).astype(int)
    mode_result = stats.mode(data_rounded, keepdims=True)
    mode = mode_result.mode[0] if len(mode_result.mode) > 0 else 0
    
    # Rango
    min_val = np.min(data)
    max_val = np.max(data)
    range_val = max_val - min_val
    
    # Cuartiles
    q1 = np.percentile(data, 25)
    q2 = np.percentile(data, 50)  # = mediana
    q3 = np.percentile(data, 75)
    
    # Percentiles adicionales
    p10 = np.percentile(data, 10)
    p90 = np.percentile(data, 90)
    p95 = np.percentile(data, 95)
    p99 = np.percentile(data, 99)
    
    return {
        'mean': mean,
        'median': median,
        'variance': variance,
        'std': std,
        'mode': mode,
        'min': min_val,
        'max': max_val,
        'range': range_val,
        'q1': q1,
        'q2': q2,
        'q3': q3,
        'p10': p10,
        'p90': p90,
        'p95': p95,
        'p99': p99,
        'n': len(data)
    }


def calculate_covariance_matrix(replica_results_list):
    """
    Calcula matriz de covarianzas entre tiempos de servicio de estaciones.
    
    Args:
        replica_results_list: Lista de resultados de réplicas
    
    Returns:
        DataFrame: Matriz de covarianzas
    """
    stations = ['cashiers', 'drinks', 'fryer', 'desserts', 'chicken']
    
    # Recolecta tiempos de servicio por estación
    station_times = {station: [] for station in stations}
    
    for results in replica_results_list:
        for customer in results['customers']:
            for station in stations:
                if station in customer['service_times']:
                    station_times[station].append(customer['service_times'][station])
    
    # Crea DataFrame
    df_times = pd.DataFrame({
        station: pd.Series(times) for station, times in station_times.items()
    })
    
    # Calcula matriz de covarianzas
    cov_matrix = df_times.cov()
    
    return cov_matrix


# ========================================================================
# VISUALIZACIONES
# ========================================================================

def plot_histogram(data, title, xlabel, output_file, bins='auto'):
    """Genera histograma de frecuencias absolutas y relativas."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histograma absoluto
    counts, bins_edges, patches = ax1.hist(data, bins=bins, color='steelblue', 
                                           edgecolor='black', alpha=0.7)
    ax1.set_xlabel(xlabel, fontsize=12)
    ax1.set_ylabel('Frecuencia Absoluta', fontsize=12)
    ax1.set_title(f'{title} - Frecuencias Absolutas', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Agrega valores en las barras
    #for count, patch in zip(counts, patches):
    #    height = patch.get_height()
    #    if height > 0:
    #        ax1.text(patch.get_x() + patch.get_width()/2, height,
    #                f'{int(count)}', ha='center', va='bottom', fontsize=8)
    
    # Histograma relativo
    ax2.hist(data, bins=bins, density=True, color='coral',
             edgecolor='black', alpha=0.7)
    ax2.set_xlabel(xlabel, fontsize=12)
    ax2.set_ylabel('Densidad / Frecuencia Relativa', fontsize=12)
    ax2.set_title(f'{title} - Frecuencias Relativas', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Histograma guardado: {output_file}")


def plot_boxplot(data_dict, title, ylabel, output_file):
    """Genera boxplot comparativo para múltiples series."""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Prepara datos
    labels = list(data_dict.keys())
    data_list = [data_dict[label] for label in labels]
    
    bp = ax.boxplot(data_list, tick_labels=labels, patch_artist=True,
                   notch=True, showmeans=True)
    
    # Personaliza colores
    colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Boxplot guardado: {output_file}")


def plot_covariance_heatmap(cov_matrix, output_file):
    """Genera heatmap de matriz de covarianzas."""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(cov_matrix, annot=True, fmt='.4f', cmap='coolwarm',
               center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    
    ax.set_title('Matriz de Covarianzas entre Estaciones', 
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Heatmap guardado: {output_file}")


def plot_sensitivity_curve(param_values, W_means, W_stds, param_name, 
                          output_file, target_line=None):
    """Genera curva de sensibilidad."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Línea principal con área de confianza
    ax.plot(param_values, W_means, 'o-', linewidth=2, markersize=8,
           color='steelblue', label='W promedio')
    
    # Área de confianza (±1 std)
    ax.fill_between(param_values, 
                    np.array(W_means) - np.array(W_stds),
                    np.array(W_means) + np.array(W_stds),
                    alpha=0.3, color='steelblue', label='±1 desv. est.')
    
    # Línea objetivo
    if target_line is not None:
        ax.axhline(y=target_line, color='red', linestyle='--', 
                  linewidth=2, label=f'Objetivo: {target_line} min')
    
    ax.set_xlabel(param_name, fontsize=12)
    ax.set_ylabel('Tiempo en Sistema W (min)', fontsize=12)
    ax.set_title(f'Sensibilidad de W ante cambios en {param_name}', 
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_file, format='pdf', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ Curva de sensibilidad guardada: {output_file}")


# ========================================================================
# ANÁLISIS DE SENSIBILIDAD
# ========================================================================

def sensitivity_analysis_chicken_prob(base_config, prob_values, num_replicas,
                                      output_folder='results/sensitivity'):
    """
    Análisis de sensibilidad variando P_pollo.
    
    Args:
        base_config: Configuración base
        prob_values: Lista de valores de probabilidad a probar
        num_replicas: Réplicas por valor
        output_folder: Carpeta de salida
    
    Returns:
        DataFrame: Resultados del análisis
    """
    print("\nAnálisis de sensibilidad: P_pollo")
    
    os.makedirs(output_folder, exist_ok=True)
    
    results = []
    W_means = []
    W_stds = []
    
    for p_chicken in prob_values:
        print(f"  Evaluando P_pollo = {p_chicken:.2f}...")
        
        # Modifica configuración
        temp_config = copy.deepcopy(base_config)
        temp_config['probabilities']['chicken'] = p_chicken
        
        # Ejecuta réplicas
        metrics_list = run_replicas_parallel(temp_config, num_replicas)
        agg = aggregate_replica_metrics(metrics_list)
        
        results.append({
            'P_chicken': p_chicken,
            'W_mean': agg['W_mean'],
            'W_std': agg['W_std'],
            'W_ci_95': agg['W_ci_95'],
            'W_variance': agg['W_variance']
        })
        
        W_means.append(agg['W_mean'])
        W_stds.append(agg['W_std'])
    
    # Genera gráfico
    plot_sensitivity_curve(
        prob_values, W_means, W_stds,
        'Probabilidad de Pollo (P_pollo)',
        f'{output_folder}/sensitivity_chicken_prob.pdf',
        target_line=3.0
    )
    
    # Guarda resultados
    df = pd.DataFrame(results)
    df.to_csv(f'{output_folder}/sensitivity_chicken_prob.csv', index=False)
    
    return df


def sensitivity_analysis_arrival_rate(base_config, lambda_values, num_replicas,
                                      output_folder='results/sensitivity'):
    """Análisis de sensibilidad variando λ (tasa de llegadas)."""
    print("\nAnálisis de sensibilidad: λ (tasa de llegadas)")
    
    os.makedirs(output_folder, exist_ok=True)
    
    results = []
    W_means = []
    W_stds = []
    
    for lambda_val in lambda_values:
        print(f"  Evaluando λ = {lambda_val:.2f} clientes/hora...")
        
        temp_config = copy.deepcopy(base_config)
        temp_config['arrivals']['lambda'] = lambda_val
        
        metrics_list = run_replicas_parallel(temp_config, num_replicas)
        agg = aggregate_replica_metrics(metrics_list)
        
        results.append({
            'lambda': lambda_val,
            'W_mean': agg['W_mean'],
            'W_std': agg['W_std'],
            'W_ci_95': agg['W_ci_95'],
            'W_variance': agg['W_variance']
        })
        
        W_means.append(agg['W_mean'])
        W_stds.append(agg['W_std'])
    
    plot_sensitivity_curve(
        lambda_values, W_means, W_stds,
        'Tasa de Llegadas λ (clientes/hora)',
        f'{output_folder}/sensitivity_arrival_rate.pdf',
        target_line=3.0
    )
    
    df = pd.DataFrame(results)
    df.to_csv(f'{output_folder}/sensitivity_arrival_rate.csv', index=False)
    
    return df


def sensitivity_analysis_cashier_time(base_config, cashier_means, num_replicas,
                                     output_folder='results/sensitivity'):
    """Análisis de sensibilidad variando tiempo de servicio en cajas."""
    print("\nAnálisis de sensibilidad: Tiempo de caja")
    
    os.makedirs(output_folder, exist_ok=True)
    
    results = []
    W_means = []
    W_stds = []
    
    for mean_time in cashier_means:
        print(f"  Evaluando tiempo de caja = {mean_time:.2f} min...")
        
        temp_config = copy.deepcopy(base_config)
        temp_config['service_times']['cashiers']['mean'] = mean_time
        
        metrics_list = run_replicas_parallel(temp_config, num_replicas)
        agg = aggregate_replica_metrics(metrics_list)
        
        results.append({
            'cashier_mean_time': mean_time,
            'W_mean': agg['W_mean'],
            'W_std': agg['W_std'],
            'W_ci_95': agg['W_ci_95'],
            'W_variance': agg['W_variance']
        })
        
        W_means.append(agg['W_mean'])
        W_stds.append(agg['W_std'])
    
    plot_sensitivity_curve(
        cashier_means, W_means, W_stds,
        'Tiempo Promedio de Servicio en Cajas (min)',
        f'{output_folder}/sensitivity_cashier_time.pdf',
        target_line=3.0
    )
    
    df = pd.DataFrame(results)
    df.to_csv(f'{output_folder}/sensitivity_cashier_time.csv', index=False)
    
    return df


# ========================================================================
# ANÁLISIS COMPLETO DE CONFIGURACIÓN
# ========================================================================

def comprehensive_analysis(config, num_replicas=200, output_folder='results/analysis'):
    """
    Realiza análisis completo de una configuración.
    
    Args:
        config: Configuración del sistema
        num_replicas: Número de réplicas
        output_folder: Carpeta de salida
    
    Returns:
        dict: Resultados del análisis
    """
    print("\n" + "="*70)
    print("  ANÁLISIS COMPLETO DE CONFIGURACIÓN")
    print("="*70)
    
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(f'{output_folder}/figures', exist_ok=True)
    os.makedirs(f'{output_folder}/tables', exist_ok=True)
    
    # Ejecuta réplicas
    print(f"\nEjecutando {num_replicas} réplicas...")
    replica_results_list = []
    
    for i in range(num_replicas):
        results = run_replica(config, seed=42+i, verbose=False)
        replica_results_list.append(results)
        
        if (i+1) % 50 == 0:
            print(f"  Completadas: {i+1}/{num_replicas}")
    
    print(f"  ✓ {num_replicas} réplicas completadas")
    
    # Extrae tiempos en sistema
    all_W = []
    for results in replica_results_list:
        for customer in results['customers']:
            all_W.append(customer['time_in_system'])
    
    # Calcula estadísticas
    print("\nCalculando estadísticas...")
    stats_W = calculate_statistics(all_W)
    
    print(f"  Media: {stats_W['mean']:.4f} min")
    print(f"  Mediana: {stats_W['median']:.4f} min")
    print(f"  Varianza: {stats_W['variance']:.4f}")
    print(f"  Desv. Est.: {stats_W['std']:.4f}")
    print(f"  Moda: {stats_W['mode']}")
    print(f"  Rango: [{stats_W['min']:.4f}, {stats_W['max']:.4f}]")
    print(f"  Cuartiles: Q1={stats_W['q1']:.4f}, Q2={stats_W['q2']:.4f}, Q3={stats_W['q3']:.4f}")
    
    # Guarda tabla de estadísticas
    stats_df = pd.DataFrame([stats_W])
    stats_df.to_csv(f'{output_folder}/tables/statistics_W.csv', index=False)
    
    # Histogramas
    print("\nGenerando histogramas...")
    plot_histogram(
        all_W, 
        'Tiempo en Sistema (W)',
        'Tiempo (minutos)',
        f'{output_folder}/figures/histogram_W.pdf'
    )
    
    # Boxplots por estación
    print("\nGenerando boxplots...")
    stations = ['cashiers', 'drinks', 'fryer', 'desserts', 'chicken']
    station_times = {station: [] for station in stations}
    
    for results in replica_results_list:
        for customer in results['customers']:
            for station in stations:
                if station in customer['service_times']:
                    station_times[station].append(customer['service_times'][station])
    
    # Filtra estaciones con datos
    station_times_filtered = {k: v for k, v in station_times.items() if len(v) > 0}
    
    if station_times_filtered:
        plot_boxplot(
            station_times_filtered,
            'Tiempos de Servicio por Estación',
            'Tiempo (minutos)',
            f'{output_folder}/figures/boxplot_stations.pdf'
        )
    
    # 6. Matriz de covarianzas
    print("\nCalculando matriz de covarianzas...")
    cov_matrix = calculate_covariance_matrix(replica_results_list)
    cov_matrix.to_csv(f'{output_folder}/tables/covariance_matrix.csv')
    
    plot_covariance_heatmap(
        cov_matrix,
        f'{output_folder}/figures/covariance_heatmap.pdf'
    )
    
    print("\nAnálisis completo finalizado")
    print(f"Resultados guardados en: {output_folder}")
    
    return {
        'statistics': stats_W,
        'covariance_matrix': cov_matrix,
        'replica_count': num_replicas
    }


# ========================================================================
# EJECUCIÓN PRINCIPAL
# ========================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Análisis y visualización')
    parser.add_argument('--config', default='config.yaml', help='Archivo de configuración')
    parser.add_argument('--replicas', type=int, default=200, help='Número de réplicas')
    parser.add_argument('--sensitivity', action='store_true', help='Ejecutar análisis de sensibilidad')
    parser.add_argument('--output', default='results/analysis', help='Carpeta de salida')
    
    args = parser.parse_args()
    
    print("="*70)
    print("  ANÁLISIS ESTADÍSTICO Y VISUALIZACIÓN")
    print("="*70)
    
    # Carga configuración
    config = load_config(args.config)
    
    # Análisis completo
    results = comprehensive_analysis(config, num_replicas=args.replicas, 
                                    output_folder=args.output)
    
    # Análisis de sensibilidad (opcional)
    if args.sensitivity:
        print("\n" + "="*70)
        print("  ANÁLISIS DE SENSIBILIDAD")
        print("="*70)
        
        sensitivity_folder = f'{args.output}/sensitivity'
        
        # Sensibilidad P_pollo
        prob_values = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
        sensitivity_analysis_chicken_prob(config, prob_values, 
                                         num_replicas=200,
                                         output_folder=sensitivity_folder)
        
        # Sensibilidad λ
        base_lambda = config['arrivals']['lambda']
        lambda_values = [base_lambda * f for f in [0.8, 0.9, 1.0, 1.1, 1.2]]
        sensitivity_analysis_arrival_rate(config, lambda_values,
                                         num_replicas=200,
                                         output_folder=sensitivity_folder)
        
        # Sensibilidad tiempo de caja
        cashier_times = [1.5, 2.0, 2.5, 3.0, 3.5]
        sensitivity_analysis_cashier_time(config, cashier_times,
                                         num_replicas=200,
                                         output_folder=sensitivity_folder)
    
    print("\n" + "="*70)
    print("  ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*70)
