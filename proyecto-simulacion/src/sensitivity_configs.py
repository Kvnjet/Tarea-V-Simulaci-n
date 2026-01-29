# sensitivity_configs.py - VERSIÓN COMPLETA
import copy
import numpy as np
import pandas as pd
from analysis import load_config, run_replicas_parallel, aggregate_replica_metrics
from analysis import sensitivity_analysis_configuration, get_base_value

def get_configuration_details(base_config, config_id):
    """Devuelve la configuración específica para cada caso"""
    # meterle a la IA en esta parte para que te actualice las configuraciones
    # con las que estes usando actualmente despues de correr simulacion_colas
    config_templates = {
        # CASO (a) - Costo mínimo para tiempo ≤ 3 minutos
        'a_min_cost_1': {
            'name': 'Caso (a) - Configuración Óptima (2.17 min)',
            'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 0, 'chicken': 4},
            'modifications': {
                'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 0, 'chicken': 4},
                'service_times': {'cashiers': {'mean': 2.5}},  # Valor base
                'probabilities': {'chicken': 0.3, 'desserts': 0.25, 'drinks': 0.9},
                'arrivals': {'lambda': 25}  # Asumiendo 25 clientes/hora
            }
        },
        
        # CASO (b) - Mejor con $2000
        'b_budget_2000': {
            'name': 'Caso (b) - Mejor con $2000 (216.28 min)',
            'servers': {'cashiers': 1, 'drinks': 1, 'fryer': 1, 'desserts': 3, 'chicken': 2},
            'modifications': {
                'servers': {'cashiers': 1, 'drinks': 1, 'fryer': 1, 'desserts': 3, 'chicken': 2},
                'service_times': {'cashiers': {'mean': 2.5}},
                'probabilities': {'chicken': 0.3, 'desserts': 0.25, 'drinks': 0.9},
                'arrivals': {'lambda': 25}
            }
        },
        
        # CASO (c) - Con $3000
        'c_budget_3000': {
            'name': 'Caso (c) - Con $3000 (5.44 min)',
            'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 2, 'desserts': 0, 'chicken': 3},
            'modifications': {
                'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 2, 'desserts': 0, 'chicken': 3},
                'service_times': {'cashiers': {'mean': 2.5}},
                'probabilities': {'chicken': 0.3, 'desserts': 0.25, 'drinks': 0.9},
                'arrivals': {'lambda': 25}
            }
        },
        
        # CASO (d) - Tiempo reducido en caja (2 min)
        'd_reduced_cashier': {
            'name': 'Caso (d) - Caja a 2 min (2.02 min)',
            'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 0, 'chicken': 4},
            'modifications': {
                'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 0, 'chicken': 4},
                'service_times': {'cashiers': {'mean': 2.0}},  # REDUCIDO A 2 MIN
                'probabilities': {'chicken': 0.3, 'desserts': 0.25, 'drinks': 0.9},
                'arrivals': {'lambda': 25}
            }
        },
        
        # CASO (e) - Probabilidad de pollo al 50%
        'e_50pct_chicken': {
            'name': 'Caso (e) - 50% Pollo (2.50 min)',
            'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 0, 'chicken': 4},
            'modifications': {
                'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 0, 'chicken': 4},
                'service_times': {'cashiers': {'mean': 2.5}},
                'probabilities': {'chicken': 0.5, 'desserts': 0.25, 'drinks': 0.9},  # 50% POLLO
                'arrivals': {'lambda': 25}
            }
        },
        
        # CASO (a) - Otras configuraciones del top 3
        'a_min_cost_2': {
            'name': 'Caso (a) - Segunda Mejor (2.40 min)',
            'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 2, 'chicken': 4},
            'modifications': {
                'servers': {'cashiers': 3, 'drinks': 1, 'fryer': 3, 'desserts': 2, 'chicken': 4},
                'service_times': {'cashiers': {'mean': 2.5}},
                'probabilities': {'chicken': 0.3, 'desserts': 0.25, 'drinks': 0.9},
                'arrivals': {'lambda': 25}
            }
        },
    }
    
    return config_templates.get(config_id)

def apply_configuration_modifications(base_config, config_template):
    """Aplica las modificaciones de una configuración específica"""
    modified_config = copy.deepcopy(base_config)
    
    # Aplica modificaciones
    for section, values in config_template['modifications'].items():
        if section in modified_config:
            if section == 'servers':
                # Actualiza número de servidores
                for station, count in values.items():
                    if station in modified_config['servers']:
                        modified_config['servers'][station] = count
            elif isinstance(values, dict):
                # Para diccionarios anidados (service_times, probabilities, etc.)
                for key, value in values.items():
                    if key in modified_config[section]:
                        if isinstance(value, dict):
                            modified_config[section][key].update(value)
                        else:
                            modified_config[section][key] = value
    
    return modified_config

def analyze_selected_configurations():
    """Analiza sensibilidad para TODAS las configuraciones clave"""
    
    # Carga configuración base
    base_config = load_config('config.yaml')
    
    # Define TODAS las configuraciones a analizar
    config_ids = [
        'a_min_cost_1',    # Caso (a) - Óptima
        'a_min_cost_2',    # Caso (a) - Segunda
        'b_budget_2000',   # Caso (b) - $2000
        'c_budget_3000',   # Caso (c) - $3000
        'd_reduced_cashier', # Caso (d) - Caja reducida
        'e_50pct_chicken'  # Caso (e) - 50% pollo
    ]
    
    # Parámetros para análisis de sensibilidad
    sensitivity_params = [
        {
            'name': 'prob_chicken',
            'range': np.arange(0.1, 0.8, 0.1).tolise(),  # 0.1, 0.2, ..., 0.7
            'description': 'Probabilidad de pedir pollo',
            'target_W_max': 3.0
        },
        {
            'name': 'prob_desserts',
            'range': np.arange(0.1, 0.6, 0.1).tolise(),  # 0.1, 0.2, ..., 0.5
            'description': 'Probabilidad de pedir postres',
            'target_W_max': 3.0
        },
        {
            'name': 'prob_drinks',
            'range': np.arange(0.5, 1.05, 0.1).tolise(),  # 0.5, 0.6, ..., 1.0
            'description': 'Probabilidad de pedir bebidas',
            'target_W_max': 3.0
        },
        {
            'name': 'lambda',
            'range': np.arange(15, 40, 5).tolise(),  # 15, 20, ..., 35 clientes/hora
            'description': 'Tasa de llegadas (clientes/hora)',
            'target_W_max': 3.0
        },
        {
            'name': 'cashier_time',
            'range': np.arange(1.5, 4.0, 0.5).tolise(),  # 1.5, 2.0, ..., 3.5 min
            'description': 'Tiempo de servicio en cajas',
            'target_W_max': 3.0
        }
    ]
    
    results_summary = []
    
    print("\n" + "="*80)
    print("ANÁLISIS DE SENSIBILIDAD COMPLETO - 6 CONFIGURACIONES CLAVE")
    print("="*80)
    
    # Analiza cada configuración
    for config_id in config_ids:
        config_template = get_configuration_details(base_config, config_id)
        
        if not config_template:
            print(f"\n⚠️  Configuración {config_id} no encontrada")
            continue
        
        print(f"\n{'='*60}")
        print(f"ANALIZANDO: {config_template['name']}")
        print(f"Servidores: {config_template['servers']}")
        print(f"{'='*60}")
        
        # Crea configuración modificada
        modified_config = apply_configuration_modifications(base_config, config_template)
        
        # Obtiene estadísticas base (con menos réplicas para velocidad)
        print("  Obteniendo estadísticas base...")
        metrics_list = run_replicas_parallel(modified_config, num_replicas=30)
        base_stats = aggregate_replica_metrics(metrics_list)
        
        print(f"  W base: {base_stats['W_mean']:.2f} min")
        print(f"  IC 95%: [{base_stats['W_ci_95'][0]:.2f}, {base_stats['W_ci_95'][1]:.2f}]")
        
        # Realiza análisis de sensibilidad para cada parámetro
        config_results = {
            'config_id': config_id,
            'config_name': config_template['name'],
            'servers': config_template['servers'],
            'W_base': base_stats['W_mean'],
            'W_std': base_stats['W_std'],
            'W_ci': base_stats['W_ci_95'],
            'breaking_points': {},
            'margins': {},
            'sensitivities': {}
        }
        
        for param in sensitivity_params:
            print(f"\n  → Variando {param['description']}...")
            
            # Ejecuta análisis de sensibilidad
            df_results, breaking_point = sensitivity_analysis_configuration(
                config=modified_config,
                config_name=config_id,
                base_stats=base_stats,
                param_name=param['name'],
                param_range=param['range'],
                target_W_max=param['target_W_max'],
                num_replicas=20,  # Réplicas por valor
                output_folder=f'results/sensitivity/{config_id}'
            )
            
            # Almacena resultados
            config_results['breaking_points'][param['name']] = breaking_point
            
            # Calcula margen de seguridad
            if breaking_point is not None:
                try:
                    base_value = get_base_value(modified_config, param['name'])
                    if base_value is not None and base_value != 0:
                        margin_abs = abs(breaking_point - base_value)
                        margin_percent = (margin_abs / base_value) * 100
                        config_results['margins'][param['name']] = margin_percent
                        
                        # Calcula sensibilidad (ΔW/ΔParam)
                        if df_results is not None and len(df_results) > 1:
                            # Encuentra los valores alrededor del punto base
                            df_results['W_change'] = df_results['W_mean'] - base_stats['W_mean']
                            df_results['param_change'] = df_results[param['name']] - base_value
                            df_results['sensitivity'] = df_results['W_change'] / df_results['param_change']
                            
                            # Sensibilidad promedio
                            avg_sensitivity = df_results['sensitivity'].abs().mean()
                            config_results['sensitivities'][param['name']] = avg_sensitivity
                            
                            print(f"    Punto de quiebre: {breaking_point:.2f}")
                            print(f"    Margen: {margin_percent:.1f}%")
                            print(f"    Sensibilidad: {avg_sensitivity:.3f} (min/Δparam)")
                        else:
                            print(f"    Punto de quiebre: {breaking_point:.2f}")
                    else:
                        print(f"    Punto de quiebre: {breaking_point:.2f} (no se pudo calcular margen)")
                except Exception as e:
                    print(f"    Error calculando margen: {e}")
            else:
                print(f"    ✅ Mantiene W ≤ {param['target_W_max']}min en todo el rango")
                config_results['margins'][param['name']] = float('inf')
        
        results_summary.append(config_results)
    
    # Genera reportes
    generate_sensitivity_report(results_summary)
    save_detailed_results(results_summary)
    
    return results_summary

def generate_sensitivity_report(results):
    """Genera un reporte comparativo de sensibilidad"""
    print(f"\n{'='*80}")
    print("REPORTE COMPARATIVO DE SENSIBILIDAD")
    print(f"{'='*80}")
    
    print("\n" + "="*120)
    print("RESUMEN DE MÁRGENES DE SEGURIDAD (% de cambio tolerable antes de W > 3 min)")
    print("="*120)
    
    headers = ["Configuración", "W_base", "P_pollo", "P_postres", "P_bebidas", "λ", "T_caja", "Punto más débil"]
    print(f"{headers[0]:<30} {headers[1]:<8} {headers[2]:<10} {headers[3]:<10} {headers[4]:<10} {headers[5]:<10} {headers[6]:<10} {headers[7]}")
    print("-" * 120)
    
    for result in results:
        config_name = result['config_name'][:30]
        w_base = f"{result['W_base']:.2f}"
        
        # Formatea márgenes
        margins = result['margins']
        chicken = f"{margins.get('prob_chicken', 'N/A'):.1f}%" if 'prob_chicken' in margins else 'N/A'
        desserts = f"{margins.get('prob_desserts', 'N/A'):.1f}%" if 'prob_desserts' in margins else 'N/A'
        drinks = f"{margins.get('prob_drinks', 'N/A'):.1f}%" if 'prob_drinks' in margins else 'N/A'
        lambda_val = f"{margins.get('lambda', 'N/A'):.1f}%" if 'lambda' in margins else 'N/A'
        cashier = f"{margins.get('cashier_time', 'N/A'):.1f}%" if 'cashier_time' in margins else 'N/A'
        
        # Identifica punto más débil (menor margen)
        finite_margins = {k: v for k, v in margins.items() 
                         if isinstance(v, (int, float)) and v != float('inf')}
        
        if finite_margins:
            weakest = min(finite_margins.items(), key=lambda x: x[1])
            weakest_str = f"{weakest[0]}: {weakest[1]:.1f}%"
        else:
            weakest_str = "Robusta"
        
        print(f"{config_name:<30} {w_base:<8} {chicken:<10} {desserts:<10} {drinks:<10} {lambda_val:<10} {cashier:<10} {weakest_str}")
    
    print("-" * 120)
    
    # Análisis de sensibilidad
    print("\n" + "="*80)
    print("ANÁLISIS DE SENSIBILIDAD (ΔW/ΔParam - mayor = más sensible)")
    print("="*80)
    
    # Ordena por sensibilidad promedio
    sensitivities_summary = []
    for result in results:
        sensitivities = result.get('sensitivities', {})
        if sensitivities:
            avg_sens = np.mean(list(sensitivities.values()))
        else:
            avg_sens = 0
        
        sensitivities_summary.append({
            'name': result['config_name'],
            'avg_sensitivity': avg_sens,
            'most_sensitive_param': max(sensitivities.items(), key=lambda x: x[1])[0] if sensitivities else 'N/A'
        })
    
    # Ordena de más a menos sensible
    sensitivities_summary.sort(key=lambda x: x['avg_sensitivity'], reverse=True)
    
    for item in sensitivities_summary:
        print(f"  • {item['name'][:40]:<40} Sensibilidad promedio: {item['avg_sensitivity']:.3f}")
        print(f"    Parámetro más sensible: {item['most_sensitive_param']}")
    
    # Recomendaciones
    print("\n" + "="*80)
    print("RECOMENDACIONES BASADAS EN EL ANÁLISIS:")
    print("="*80)
    
    print("\n1. CONFIGURACIÓN MÁS ROBUSTA:")
    # Encuentra la con mayor margen promedio
    robust_config = max(results, key=lambda x: np.mean([v for v in x['margins'].values() 
                                                       if isinstance(v, (int, float)) and v != float('inf')]))
    print(f"   {robust_config['config_name']}")
    print(f"   W: {robust_config['W_base']:.2f} min, Márgenes amplios en todos los parámetros")
    
    print("\n2. CONFIGURACIÓN MÁS SENSIBLE:")
    sensitive_config = min(results, key=lambda x: np.mean([v for v in x['margins'].values() 
                                                          if isinstance(v, (int, float)) and v != float('inf')]))
    print(f"   {sensitive_config['config_name']}")
    print(f"   W: {sensitive_config['W_base']:.2f} min, Requiere monitoreo constante")
    
    print("\n3. PARA IMPLEMENTACIÓN PRÁCTICA:")
    print("   • Usar configuraciones robustas en horarios pico")
    print("   • Monitorear parámetros críticos identificados")
    print("   • Considerar redundancia en estaciones sensibles")

def save_detailed_results(results):
    """Guarda resultados detallados en CSV"""
    import os
    os.makedirs('results/sensitivity_summary', exist_ok=True)
    
    # Convierte a DataFrame
    rows = []
    for result in results:
        row = {
            'config_id': result['config_id'],
            'config_name': result['config_name'],
            'W_base': result['W_base'],
            'W_std': result['W_std'],
            'cashiers': result['servers'].get('cashiers', 0),
            'drinks': result['servers'].get('drinks', 0),
            'fryer': result['servers'].get('fryer', 0),
            'desserts': result['servers'].get('desserts', 0),
            'chicken': result['servers'].get('chicken', 0),
        }
        
        # Agrega márgenes
        for param, margin in result['margins'].items():
            row[f'margin_{param}'] = margin if margin != float('inf') else None
        
        # Agrega sensibilidades
        for param, sens in result.get('sensitivities', {}).items():
            row[f'sens_{param}'] = sens
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv('results/sensitivity_summary/detailed_results.csv', index=False)
    
    # También guarda un resumen compacto
    summary_df = df[['config_name', 'W_base', 'cashiers', 'drinks', 'fryer', 'desserts', 'chicken']]
    summary_df.to_csv('results/sensitivity_summary/configurations_summary.csv', index=False)
    
    print(f"\n✓ Resultados guardados en:")
    print(f"  - results/sensitivity_summary/detailed_results.csv")
    print(f"  - results/sensitivity_summary/configurations_summary.csv")

if __name__ == "__main__":
    # Ejecuta el análisis completo
    print("\n" + "="*80)
    print("INICIANDO ANÁLISIS DE SENSIBILIDAD PARA 6 CONFIGURACIONES")
    print("="*80)
    
    results = analyze_selected_configurations()
    
    print("\n" + "="*80)
    print("ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*80)