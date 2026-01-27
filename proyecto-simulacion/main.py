"""
Script principal para ejecutar el proyecto completo de simulación.
"""

import argparse
import os
import sys
import time

# Módulos del proyecto
from src.distributions import load_config, generate_and_validate
from src.model import run_replica, compute_metrics, save_replica_results
from src.optimization import (
    scenario_a_min_cost,
    scenario_b_budget_2000,
    scenario_c_budget_3000,
    scenario_d_reduced_cashier_time,
    scenario_e_increased_chicken_prob,
    print_configuration_summary,
    save_configurations_to_csv
)
from src.analysis import (
    comprehensive_analysis,
    sensitivity_analysis_chicken_prob,
    sensitivity_analysis_arrival_rate,
    sensitivity_analysis_cashier_time
)


# ========================================================================
# FUNCIONES AUXILIARES
# ========================================================================

def print_header(title):
    """Imprime encabezado decorado."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def create_project_structure():
    """Crea estructura de directorios del proyecto."""
    directories = [
        "results",
        "results/validation",
        "results/replicas",
        "results/optimization",
        "results/analysis",
        "results/analysis/figures",
        "results/analysis/tables"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✓ Estructura de directorios creada")


# ========================================================================
# ETAPA 0: PREPARACIÓN
# ========================================================================

def stage_0_preparation():
    """Preparación del proyecto"""
    print_header("  PREPARACIÓN DEL PROYECTO")
    
    print("Verificando estructura del proyecto...")
    create_project_structure()
    
    print("\nVerificando archivo de configuración...")
    if not os.path.exists("config.yaml"):
        print("ERROR: No se encontró config.yaml")
        print("   Por favor, crea el archivo config.yaml antes de continuar.")
        return False
    
    try:
        config = load_config("config.yaml")
        print("✓ config.yaml cargado correctamente")
        
        print("\nParámetros de simulación:")
        print(f"  - Horizonte: {config['simulation']['horizon_hours']} horas")
        print(f"  - Tasa de llegada λ: {config['arrivals']['lambda']} clientes/hora")
        print(f"  - Réplicas: {config['simulation']['replicas']}")
        print(f"  - Presupuesto máximo: ${config['constraints']['max_budget']}")
        print(f"  - Colaboradores máximos: {config['constraints']['max_collaborators']}")
        
        return True
    except Exception as e:
        print(f"ERROR al cargar config.yaml: {e}")
        return False


# ========================================================================
# ETAPA 2: DISTRIBUCIONES Y VALIDACIÓN
# ========================================================================

def stage_2_distributions(config):
    """Generación y validación de distribuciones."""
    print_header("  GENERACIÓN Y VALIDACIÓN DE DISTRIBUCIONES")
    
    output_dir = "results/validation"
    
    print("Generando muestras y validando distribuciones estadísticas...")
    print(f"   Tamaño de muestra: {config['validation']['sample_size']}")
    print(f"   Nivel de significancia: {config['validation']['significance_level']}")
    
    start_time = time.time()
    
    try:
        summary = generate_and_validate(config, output_dir)
        
        elapsed = time.time() - start_time
        print(f"  Tiempo transcurrido: {elapsed:.2f} segundos")
        
        # Resumen de resultados
        passed = summary['Pasa'].sum()
        total = len(summary)
        
        print(f"\nResumen de validación:")
        print(f"   Pruebas que PASAN: {passed}/{total}")
        print(f"   Pruebas que NO PASAN: {total - passed}/{total}")
        
        if passed == total:
            print("   TODAS las distribuciones están validadas")
        else:
            print("   Algunas distribuciones no pasaron las pruebas")
            print("      Revisa los detalles en results/validation/")
        
        return True
    except Exception as e:
        print(f"ERROR en validación: {e}")
        import traceback
        traceback.print_exc()
        return False


# ========================================================================
# ETAPA 3: MODELO SIMPY
# ========================================================================

def stage_3_model(config):
    """Implementación del modelo y pruebas."""
    print_header("  MODELO SIMPY Y PRUEBAS")
    
    print("Ejecutando réplica de prueba...")
    
    try:
        # Ejecuta una réplica de prueba
        results = run_replica(config, seed=42, verbose=True)
        metrics = compute_metrics(results)
        
        print("\nResultados de la réplica de prueba:")
        print(f"   Clientes atendidos: {metrics['num_customers']}")
        print(f"   W promedio: {metrics['W_mean']:.4f} minutos")
        print(f"   Varianza de W: {metrics['W_variance']:.4f}")
        
        print("\nUtilización por estación:")
        for station, util in metrics['utilization'].items():
            print(f"   {station:12s}: {util:6.2%}")
        
        # Guarda réplica de prueba
        output_file = "results/replicas/test_replica.csv"
        save_replica_results(results, output_file)
        print(f"\n✓ Réplica de prueba guardada en: {output_file}")
        
        return True
    except Exception as e:
        print(f"ERROR en simulación: {e}")
        import traceback
        traceback.print_exc()
        return False


# ========================================================================
# ETAPA 4: OPTIMIZACIÓN
# ========================================================================

def stage_4_optimization(config, quick_mode=False):
    """Experimentos y optimización."""
    print_header("  OPTIMIZACIÓN Y ESCENARIOS")
    
    num_replicas = 30 if quick_mode else 200
    print(f"Modo: {'RÁPIDO' if quick_mode else 'COMPLETO'}")
    print(f"   Réplicas por configuración: {num_replicas}")
    
    output_dir = "results/optimization"
    scenarios_results = {}
    
    try:
        # Escenario (a): Costo mínimo para W ≤ 3 min
        print("\n" + "-"*70)
        configs_a = scenario_a_min_cost(config, num_replicas=num_replicas)
        print_configuration_summary(configs_a, "ESCENARIO (a)")
        save_configurations_to_csv(configs_a, f"{output_dir}/scenario_a.csv", "a")
        scenarios_results['a'] = configs_a
        
        # Escenario (b): Presupuesto $2000
        print("\n" + "-"*70)
        configs_b = scenario_b_budget_2000(config, num_replicas=num_replicas)
        print_configuration_summary(configs_b, "ESCENARIO (b)")
        save_configurations_to_csv(configs_b, f"{output_dir}/scenario_b.csv", "b")
        scenarios_results['b'] = configs_b
        
        # Escenario (c): Presupuesto $3000
        print("\n" + "-"*70)
        configs_c = scenario_c_budget_3000(config, num_replicas=num_replicas)
        print_configuration_summary(configs_c, "ESCENARIO (c)")
        save_configurations_to_csv(configs_c, f"{output_dir}/scenario_c.csv", "c")
        scenarios_results['c'] = configs_c
        
        # Escenario (d): Tiempo de caja reducido
        print("\n" + "-"*70)
        configs_d = scenario_d_reduced_cashier_time(config, num_replicas=num_replicas)
        print_configuration_summary(configs_d, "ESCENARIO (d)")
        save_configurations_to_csv(configs_d, f"{output_dir}/scenario_d.csv", "d")
        scenarios_results['d'] = configs_d
        
        # Escenario (e): P_pollo = 0.5
        print("\n" + "-"*70)
        configs_e = scenario_e_increased_chicken_prob(config, num_replicas=num_replicas)
        print_configuration_summary(configs_e, "ESCENARIO (e)")
        save_configurations_to_csv(configs_e, f"{output_dir}/scenario_e.csv", "e")
        scenarios_results['e'] = configs_e
        
        print("\nOptimización completada para todos los escenarios")
        return True, scenarios_results
    except Exception as e:
        print(f"ERROR en optimización: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


# ========================================================================
# ETAPA 5: ANÁLISIS Y VISUALIZACIÓN
# ========================================================================

def stage_5_analysis(config, quick_mode=False):
    """Análisis estadístico y visualización."""
    print_header("  ANÁLISIS Y VISUALIZACIÓN")
    
    num_replicas = 100 if quick_mode else 200
    print(f"Réplicas para análisis: {num_replicas}")
    
    output_dir = "results/analysis"
    
    try:
        # Análisis completo
        results = comprehensive_analysis(config, num_replicas=num_replicas, 
                                        output_folder=output_dir)
        
        # Análisis de sensibilidad
        print("\n" + "-"*70)
        print("ANÁLISIS DE SENSIBILIDAD")
        print("-"*70)
        
        sensitivity_dir = f"{output_dir}/sensitivity"
        
        # P_pollo
        prob_values = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
        sensitivity_analysis_chicken_prob(config, prob_values,
                                          num_replicas=200,
                                          output_folder=sensitivity_dir)
        
        # λ (tasa de llegadas)
        base_lambda = config['arrivals']['lambda']
        lambda_values = [base_lambda * f for f in [0.8, 0.9, 1.0, 1.1, 1.2]]
        sensitivity_analysis_arrival_rate(config, lambda_values,
                                          num_replicas=200,
                                          output_folder=sensitivity_dir)
        
        # Tiempo de caja
        cashier_times = [1.5, 2.0, 2.5, 3.0, 3.5]
        sensitivity_analysis_cashier_time(config, cashier_times,
                                          num_replicas=200,
                                          output_folder=sensitivity_dir)
        
        print("\nAnálisis y visualización completados")
        return True
    except Exception as e:
        print(f"ERROR en análisis: {e}")
        import traceback
        traceback.print_exc()
        return False


# ========================================================================
# FUNCIÓN PRINCIPAL
# ========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Proyecto de Simulación - Sistema de Colas en Restaurante',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py --all              # Ejecuta todas las etapas
  python main.py --stage 2          # Solo validación de distribuciones
  python main.py --stage 4 --quick  # Optimización en modo rápido
  python main.py --stages 4 5       # Etapas 4 y 5
        """
    )
    
    parser.add_argument('--all', action='store_true',
                       help='Ejecuta todas las etapas del proyecto')
    parser.add_argument('--stage', type=int, choices=[0, 2, 3, 4, 5],
                       help='Ejecuta una etapa específica')
    parser.add_argument('--stages', type=int, nargs='+', choices=[0, 2, 3, 4, 5],
                       help='Ejecuta múltiples etapas')
    parser.add_argument('--quick', action='store_true',
                       help='Modo rápido (menos réplicas para testing)')
    parser.add_argument('--config', default='config.yaml',
                       help='Archivo de configuración (default: config.yaml)')
    
    args = parser.parse_args()
    
    # Banner inicial
    print("\n" + "="*70)
    print("  PROYECTO DE SIMULACIÓN")
    print("  Sistema de Colas en Restaurante de Comida Rápida")
    print("="*70)
    
    if args.quick:
        print("\nMODO RÁPIDO ACTIVADO (para pruebas)")
    
    # Determina qué etapas ejecutar
    stages_to_run = []
    
    if args.all:
        stages_to_run = [0, 2, 3, 4, 5]
    elif args.stage is not None:
        stages_to_run = [args.stage]
    elif args.stages is not None:
        stages_to_run = args.stages
    else:
        print("\nERROR: Debes especificar --all, --stage o --stages")
        parser.print_help()
        sys.exit(1)
    
    print(f"\nEtapas a ejecutar: {stages_to_run}")
    
    # Carga configuración
    if 0 not in stages_to_run:
        # Si no se ejecuta etapa 0, aún necesitamos cargar config
        try:
            config = load_config(args.config)
            print(f"✓ Configuración cargada: {args.config}")
        except Exception as e:
            print(f"ERROR: No se pudo cargar {args.config}")
            print(f"   {e}")
            sys.exit(1)
    
    # Ejecuta etapas
    start_time = time.time()
    
    for stage in stages_to_run:
        if stage == 0:
            if not stage_0_preparation():
                print("\nEtapa 0 falló. Abortando.")
                sys.exit(1)
            config = load_config(args.config)
        
        elif stage == 2:
            if not stage_2_distributions(config):
                print("\n  Etapa 2 tuvo errores. Continuando...")
        
        elif stage == 3:
            if not stage_3_model(config):
                print("\n  Etapa 3 tuvo errores. Continuando...")
        
        elif stage == 4:
            success, results = stage_4_optimization(config, quick_mode=args.quick)
            if not success:
                print("\n  Etapa 4 tuvo errores. Continuando...")
        
        elif stage == 5:
            if not stage_5_analysis(config, quick_mode=args.quick):
                print("\n  Etapa 5 tuvo errores. Continuando...")
    
    # Resumen final
    elapsed_total = time.time() - start_time
    
    print("\n" + "="*70)
    print("  PROYECTO COMPLETADO")
    print("="*70)
    print(f"\n  Tiempo total: {elapsed_total:.2f} segundos ({elapsed_total/60:.2f} minutos)")
    print("\nResultados guardados en:")
    print("   - results/validation/      (Validación de distribuciones)")
    print("   - results/optimization/    (Configuraciones óptimas)")
    print("   - results/analysis/        (Análisis estadístico y gráficos)")
    print("   - results/sensitivity/     (Análisis de sensibilidad)")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
