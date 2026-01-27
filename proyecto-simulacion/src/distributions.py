"""
Módulo de generación y validación de distribuciones.
"""

import numpy as np
from scipy import stats
import math
import yaml
import os
import pandas as pd
from pathlib import Path


# ========================================================================
# UTILIDADES DE RNG Y CARGA DE CONFIGURACIÓN
# ========================================================================

def get_rng(seed=None):
    """Crea y devuelve un generador aleatorio reproducible (numpy Generator)."""
    return np.random.default_rng(seed)

def load_config(path="config.yaml"):
    """Carga archivo YAML de configuración si existe."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {path}")
    with open(path, "r", encoding='utf-8') as f:
        return yaml.safe_load(f)


# ========================================================================
# MUESTREADORES PRINCIPALES
# ========================================================================

def sample_from_config(rng, cfg_service):
    """
    Muestrea un valor de tiempo de servicio según la especificación en cfg_service.
    Devuelve un número (int o float) representando minutos de servicio.
    """
    dist = cfg_service.get("distribution")
    
    if dist == "exponential":
        mean = cfg_service["mean"]
        return rng.exponential(scale=mean)
    
    if dist == "normal_discrete":
        mean = cfg_service.get("mean")
        std = cfg_service.get("std")
        val = rng.normal(loc=mean, scale=std)
        val = max(val, 1.0)  # mínimo 1 minuto
        return round(val)    # discretiza a entero
    
    if dist == "binomial":
        n = cfg_service["n"]
        p = cfg_service["p"]
        return rng.binomial(n=n, p=p)
    
    if dist == "geometric":
        p = cfg_service["p"]
        # numpy geometric devuelve 1, 2, 3, ... (número de ensayos hasta el primer éxito)
        return rng.geometric(p=p)
    
    raise ValueError(f"Distribución no soportada en config: {dist}")


# Wrappers específicos por estación
def sample_cashier(rng, cfg):
    """Genera tiempo de servicio en cajas."""
    return sample_from_config(rng, cfg["service_times"]["cashiers"])

def sample_drinks(rng, cfg):
    """Genera tiempo de servicio en dispensadora de refrescos."""
    return sample_from_config(rng, cfg["service_times"]["drinks"])

def sample_fryer(rng, cfg):
    """Genera tiempo de servicio en freidora."""
    return sample_from_config(rng, cfg["service_times"]["fryer"])

def sample_desserts(rng, cfg):
    """Genera cantidad de postres (binomial)."""
    return sample_from_config(rng, cfg["service_times"]["desserts"])

def sample_chicken(rng, cfg):
    """Genera tiempo de servicio en parrilla de pollo."""
    return sample_from_config(rng, cfg["service_times"]["chicken"])


# ========================================================================
# PRUEBAS ESTADÍSTICAS
# ========================================================================

def expected_probs_binomial(n, p, max_k):
    """Probabilidades teóricas binomial para k=0..max_k."""
    probs = [stats.binom.pmf(k, n, p) for k in range(0, max_k + 1)]
    return np.array(probs)

def expected_probs_geometric(p, max_k):
    """Probabilidades teóricas geométrica para k=1..max_k (scipy geom usa 1..)."""
    probs = [stats.geom.pmf(k, p) for k in range(1, max_k + 1)]
    return np.array(probs)

def chi_square_test(sample, dist_name, params, min_expected):
    """
    Ejecuta la prueba chi-cuadrado para muestra discreta.
    Agrupa bins si la frecuencia esperada < min_expected.
    Retorna (chi2_stat, p_value, df, details_df)
    """
    sample = np.asarray(sample)
    max_k = int(np.max(sample))
    
    # Construye observados
    if dist_name == "geometric":
        labels = np.arange(1, max_k + 1)
        counts = np.array([np.sum(sample == k) for k in labels])
        expected_probs = expected_probs_geometric(params["p"], max_k)
    
    elif dist_name == "binomial":
        labels = np.arange(0, max_k + 1)
        counts = np.array([np.sum(sample == k) for k in labels])
        expected_probs = expected_probs_binomial(params["n"], params["p"], max_k)
    
    else:
        labels = np.arange(0, max_k + 1)
        counts = np.array([np.sum(sample == k) for k in labels])
        expected_probs = counts / counts.sum()
    
    n = counts.sum()
    
    # Ajusta probabilidades si no suman 1
    if expected_probs.sum() < 1.0:
        remainder = 1.0 - expected_probs.sum()
        expected_probs[-1] += remainder
    
    expected_counts = n * expected_probs
    
    # Agrupa bins con expected < min_expected
    obs = counts.tolist()
    exp = expected_counts.tolist()
    lbl = labels.tolist()
    
    i = len(exp) - 1
    while i >= 0 and len(exp) > 1:
        if exp[i] < min_expected:
            if i == 0:
                break
            # Fusiona con el anterior
            exp[i-1] += exp[i]
            obs[i-1] += obs[i]
            lbl[i-1] = f"{lbl[i-1]}+{lbl[i]}"
            del exp[i]
            del obs[i]
            del lbl[i]
        i -= 1
    
    # Calcula chi2
    exp_arr = np.array(exp)
    obs_arr = np.array(obs)
    
    if (exp_arr <= 0).any() or len(obs_arr) < 2:
        return math.nan, math.nan, 0, \
               pd.DataFrame({"bin": lbl, "observed": obs, "expected": exp})
    
    chi2_stat, p_value = stats.chisquare(f_obs=obs_arr, f_exp=exp_arr)
    
    # Grados de libertad: k - 1 - m (m = parámetros estimados)
    m = 1 if dist_name in ["geometric", "exponential"] else 1  # p o lambda estimado
    if dist_name == "binomial":
        m = 1  # solo p, n es dado
    df = len(obs_arr) - 1 - m
    df = max(df, 1)  # Al menos 1 grado de libertad
    
    details = pd.DataFrame({"bin": lbl, "observed": obs, "expected": exp})
    
    return chi2_stat, p_value, df, details

def kolmogorov_smirnov_test(sample, dist_name, params):
    """
    Ejecuta la prueba KS para distribuciones continuas.
    dist_name: 'exponential' o 'normal'
    params: dict con parámetros según scipy
    Retorna (stat, pvalue)
    """
    sample = np.asarray(sample)
    
    if dist_name == "exponential":
        scale = params.get("scale")
        stat, p = stats.kstest(sample, 'expon', args=(0, scale))
        return stat, p
    
    if dist_name == "normal":
        mu = params.get("loc")
        sigma = params.get("scale")
        stat, p = stats.kstest(sample, 'norm', args=(mu, sigma))
        return stat, p
    
    # Fallback
    return math.nan, math.nan


# ========================================================================
# VALIDACIÓN MASIVA
# ========================================================================

def generate_and_validate(cfg, output_folder):
    """
    Genera muestras según cfg['validation']['sample_size'] para cada servicio y
    ejecuta pruebas estadísticas. Guarda resultados en CSV dentro de output_folder.
    """
    os.makedirs(output_folder, exist_ok=True)
    
    rng = get_rng(cfg["simulation"]["random_seed"])
    sample_size = cfg["validation"]["sample_size"]
    alpha = cfg["validation"]["significance_level"]
    min_expected = cfg["validation"]["min_expected_frequency"]
    
    results = []
    
    # Itera estaciones
    for station, params in cfg["service_times"].items():
        print(f"\n>>> Estación: {station.upper()}")
        print(f"    Distribución: {params['distribution']}")
        
        # Genera muestra
        samples = []
        for _ in range(sample_size):
            samples.append(sample_from_config(rng, params))
        samples = np.array(samples)
        
        # Estadísticas básicas
        print(f"    n = {len(samples)}")
        print(f"    Media = {np.mean(samples):.4f}")
        print(f"    Desv.Est. = {np.std(samples, ddof=1):.4f}")
        print(f"    Min = {np.min(samples)}, Max = {np.max(samples)}")
        
        # Guarda muestra completa
        sample_file = os.path.join(output_folder, f"{station}_sample.csv")
        pd.Series(samples).to_csv(sample_file, index=False, header=False)
        print(f"    ✓ Muestra guardada: {sample_file}")
        
        # Decide prueba
        dist = params["distribution"]

        if dist == "exponential":
            # Prueba KS
            stat, p = kolmogorov_smirnov_test(
                samples, "exponential", {"scale": params["mean"]}
            )
            
            results.append({
                "Estación": station,
                "Distribución": dist,
                "Prueba": "KS",
                "Estadístico": stat,
                "p_valor": p,
                "Pasa": p >= alpha
            })
            
            print(f"    Prueba KS: D = {stat:.6f}, p-valor = {p:.6f}"
                  f" -> {'✓ PASA' if p >= alpha else '✗ NO PASA'}")
        
        elif dist == "normal_discrete":
            # Para normal discreta, valida la parte continua con KS
            stat, p = kolmogorov_smirnov_test(
                samples, "normal", {"loc": params["mean"], "scale": params.get("std")}
            )
            
            results.append({
                "Estación": station,
                "Distribución": dist,
                "Prueba": "KS (norm approx)",
                "Estadístico": stat,
                "p_valor": p,
                "Pasa": p >= alpha
            })
            
            print(f"    Prueba KS (normal): D = {stat:.6f}, p-valor = {p:.6f}"
                  f" -> {'✓ PASA' if p >= alpha else '✗ NO PASA'}")
        
        elif dist in ("binomial", "geometric"):
            # Prueba chi-cuadrado
            chi2_stat, chi2_p, df, details = chi_square_test(
                samples, dist, params, min_expected
            )
            
            results.append({
                "Estación": station,
                "Distribución": dist,
                "Prueba": "Chi-cuadrado",
                "Estadístico": chi2_stat,
                "p_valor": chi2_p,
                "Pasa": (not math.isnan(chi2_p)) and (chi2_p >= alpha)
            })
            
            print(f"    Prueba χ²: χ² = {chi2_stat:.4f}, gl = {df},"
                  f" p-valor = {chi2_p:.6f}"
                  f" -> {'✓ PASA' if chi2_p >= alpha else ' ✗NO PASA'}")
            
            # Guarda detalles de chi2
            details_file = os.path.join(output_folder, f"{station}_chi2_details.csv")
            details.to_csv(details_file, index=False)
            print(f"    ✓ Detalles χ² guardados: {details_file}")
    
    # Guarda resultados agregados
    df = pd.DataFrame(results)
    summary_file = os.path.join(output_folder, "distribution_validation_summary.csv")
    df.to_csv(summary_file, index=False)
    
    print("\n" + "="*70)
    print("  RESUMEN DE VALIDACIÓN")
    print("="*70)
    print(df.to_string(index=False))
    print(f"\n✓ Resumen guardado: {summary_file}")
    print("="*70)
    
    return df


# ========================================================================
# EJECUCIÓN DIRECTA
# ========================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("  GENERACIÓN Y VALIDACIÓN DE DISTRIBUCIONES")
    print("="*70)

    try:
        cfg = load_config("config.yaml")
    except FileNotFoundError:
        print("\n✗ ERROR: No se encontró config.yaml en el directorio actual.")
        raise

    print("\nGenerando muestras y validando distribuciones...")
    print("(Esto puede tardar unos segundos)")
    
    output_folder = os.path.join(
        cfg["simulation"].get("output_folder", "results"), "validation"
    )
    
    summary = generate_and_validate(cfg, output_folder=output_folder)
    
    print("\n✓ Validación completada exitosamente.")
    print(f"\nPruebas que PASAN: {summary['Pasa'].sum()}/{len(summary)}\n")
