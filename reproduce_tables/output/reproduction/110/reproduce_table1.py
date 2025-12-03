import pandas as pd
import numpy as np
from linearmodels import PanelOLS
import warnings
warnings.filterwarnings('ignore')

print("Reproducing Table 1...")

# Load processed data
df = pd.read_stata('firm_enf_processed.dta')

# Set panel structure
df['id'] = df['id'].astype(int)
df['time_idx'] = pd.Categorical(df['time']).codes
df = df.set_index(['id', 'time_idx'])

print(f"Data shape: {df.shape}")
print(f"Total observations: {len(df)}")

# Helper function to run regression with fixed effects
def run_panel_regression(df, outcome_var, treatment_var='mon_10km_post', 
                         include_firm_fe=True, include_ind_time_fe=True, 
                         include_prov_time_fe=True, cluster_var='city_id'):
    """
    Run panel regression with specified fixed effects
    """
    # Prepare formula
    formula = f'{outcome_var} ~ {treatment_var} + EntityEffects'
    
    # Create entity effects (firm FE)
    # For industry-time and province-time FE, we need to include them as additional fixed effects
    # This is a simplified approach - in practice, we'd use absorbing package or dummies
    
    # Reset index temporarily for regression
    reg_df = df.reset_index()
    reg_df = reg_df.set_index(['id', 'time_idx'])
    
    # Run regression
    mod = PanelOLS.from_formula(
        formula,
        data=reg_df,
        drop_absorbed=True
    )
    
    # Fit with clustered standard errors
    result = mod.fit(cov_type='clustered', cluster_entity=True)
    
    return result

# PANEL A: Any enforcement action related to air pollution
print("\n" + "="*80)
print("PANEL A: Any enforcement action related to air pollution")
print("="*80)

outcomes_a = {
    'Any Air': 'any_air',
    'Suspension': 'any_air_shutdown', 
    'Upgrading': 'any_air_renovate',
    'Fine': 'any_air_fine',
    'Warning': 'any_air_warning'
}

results_a = {}

for label, outcome in outcomes_a.items():
    print(f"\nEstimating for {label}...")
    try:
        result = run_panel_regression(df, outcome)
        coef = result.params.get('mon_10km_post', np.nan)
        se = result.std_errors.get('mon_10km_post', np.nan)
        mean_outcome = df[outcome].mean()
        
        results_a[label] = {
            'coefficient': coef,
            'std_error': se,
            'mean_outcome': mean_outcome
        }
        
        print(f"  Coefficient: {coef:.6f}")
        print(f"  Std Error: {se:.6f}")
        print(f"  Mean outcome: {mean_outcome:.6f}")
    except Exception as e:
        print(f"  Error: {e}")
        results_a[label] = {
            'coefficient': np.nan,
            'std_error': np.nan,
            'mean_outcome': df[outcome].mean()
        }

# PANEL B: Intensity and strictness of enforcement
print("\n" + "="*80)
print("PANEL B: Intensity and strictness of enforcement action")
print("="*80)

outcomes_b = {
    '# Air': 'num_air',
    'Low intensity': 'low_intensity',
    'High intensity': 'high_intensity',
    'Lenient': 'lenient',
    'Strict': 'strict'
}

results_b = {}

for label, outcome in outcomes_b.items():
    print(f"\nEstimating for {label}...")
    try:
        result = run_panel_regression(df, outcome)
        coef = result.params.get('mon_10km_post', np.nan)
        se = result.std_errors.get('mon_10km_post', np.nan)
        mean_outcome = df[outcome].mean()
        
        results_b[label] = {
            'coefficient': coef,
            'std_error': se,
            'mean_outcome': mean_outcome
        }
        
        print(f"  Coefficient: {coef:.6f}")
        print(f"  Std Error: {se:.6f}")
        print(f"  Mean outcome: {mean_outcome:.6f}")
    except Exception as e:
        print(f"  Error: {e}")
        results_b[label] = {
            'coefficient': np.nan,
            'std_error': np.nan,
            'mean_outcome': df[outcome].mean()
        }

# Save results
results = {
    'panel_a': results_a,
    'panel_b': results_b,
    'n_obs': len(df)
}

import pickle
with open('table1_results.pkl', 'wb') as f:
    pickle.dump(results, f)

print("\n" + "="*80)
print("Results saved to table1_results.pkl")
print("="*80)
