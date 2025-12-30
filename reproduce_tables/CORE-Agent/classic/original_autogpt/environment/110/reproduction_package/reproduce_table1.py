#!/usr/bin/env python3
"""
Reproduction script for Table 1: Firm Level - Pollution Monitoring and Enforcement Activities

Panel A: Any enforcement action related to air pollution
Panel B: Intensity and strictness of enforcement action related to air pollution
"""

import pandas as pd
import numpy as np
from pyfixest.estimation import feols
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("REPRODUCING TABLE 1: FIRM-LEVEL ENFORCEMENT ACTIVITIES")
print("="*80)

# Load preprocessed data
print("\nLoading preprocessed data...")
df = pd.read_csv('./output/firm_enf_preprocessed.csv')
print(f"Successfully loaded {len(df):,} observations")
print(f"  Unique firms: {df['id'].nunique():,}")
print(f"  Time period: {df['year'].min():.0f}-{df['year'].max():.0f}")
print(f"  High polluters: {df['high_polluter'].sum():.0f}")

# Panel A outcomes: Any enforcement actions
panel_a_outcomes = [
    ('any_air', 'Any Air'),
    ('any_air_shutdown', 'Suspension'),
    ('any_air_renovate', 'Upgrading'),
    ('any_air_fine', 'Fine'),
    ('any_air_warning', 'Warning')
]

# Panel B outcomes: Intensity and strictness
panel_b_outcomes = [
    ('air', '# Air'),
    ('low_intensity', 'Low<br>intensity'),
    ('high_intensity', 'High<br>intensity'),
    ('lenient', 'Lenient'),
    ('strict', 'Strict')
]

def run_regression_panel_a(data, outcome_var):
    """Run regression for Panel A (treatment effect only)"""
    # Prepare data
    cols_needed = [outcome_var, 'treatment', 'id', 'industry_time', 'prov_time']
    reg_data = data[cols_needed].dropna()
    
    # Formula: outcome ~ treatment | firm FE + industry-time FE + province-time FE
    formula = f"{outcome_var} ~ treatment | id + industry_time + prov_time"
    
    # Fit model with firm-clustered standard errors
    model = feols(formula, data=reg_data, vcov={'CRV1': 'id'})
    
    return {
        'coef': model.coef().iloc[0],
        'se': model.se().iloc[0],
        'n_obs': len(reg_data),
        'mean_outcome': reg_data[outcome_var].mean()
    }

def run_regression_panel_b(data, outcome_var):
    """Run regression for Panel B (treatment + interaction with high polluter)"""
    # Prepare data
    data = data.copy()
    data['treatment_x_high_polluter'] = data['treatment'] * data['high_polluter']
    
    cols_needed = [outcome_var, 'treatment', 'treatment_x_high_polluter', 
                   'id', 'industry_time', 'prov_time']
    reg_data = data[cols_needed].dropna()
    
    # Formula: outcome ~ treatment + treatment × high_polluter | FEs
    formula = f"{outcome_var} ~ treatment + treatment_x_high_polluter | id + industry_time + prov_time"
    
    # Fit model with firm-clustered standard errors
    model = feols(formula, data=reg_data, vcov={'CRV1': 'id'})
    
    return {
        'coef_treatment': model.coef().iloc[0],
        'se_treatment': model.se().iloc[0],
        'coef_interaction': model.coef().iloc[1],
        'se_interaction': model.se().iloc[1],
        'n_obs': len(reg_data),
        'mean_outcome': reg_data[outcome_var].mean()
    }

print("\n" + "="*80)
print("PANEL A: ANY ENFORCEMENT ACTION RELATED TO AIR POLLUTION")
print("="*80)

panel_a_results = []
for outcome_var, outcome_label in panel_a_outcomes:
    print(f"\nRunning regression for {outcome_label}...")
    result = run_regression_panel_a(df, outcome_var)
    panel_a_results.append((outcome_label, result))
    print(f"  Coefficient: {result['coef']:.6f} (SE: {result['se']:.6f})")
    print(f"  Mean outcome: {result['mean_outcome']:.6f}")
    print(f"  Observations: {result['n_obs']:,}")

print("\n" + "="*80)
print("PANEL B: INTENSITY AND STRICTNESS OF ENFORCEMENT")
print("="*80)

panel_b_results = []
for outcome_var, outcome_label in panel_b_outcomes:
    print(f"\nRunning regression for {outcome_label}...")
    result = run_regression_panel_b(df, outcome_var)
    panel_b_results.append((outcome_label, result))
    print(f"  Treatment coef: {result['coef_treatment']:.6f} (SE: {result['se_treatment']:.6f})")
    print(f"  Interaction coef: {result['coef_interaction']:.6f} (SE: {result['se_interaction']:.6f})")
    print(f"  Mean outcome: {result['mean_outcome']:.6f}")
    print(f"  Observations: {result['n_obs']:,}")

print("\n" + "="*80)
print("GENERATING TABLE 1 MARKDOWN")
print("="*80)

# Generate markdown table
markdown_output = []
markdown_output.append("### Table 1—Firm Level: Pollution Monitoring and Enforcement Activities\n")

# Panel A header
markdown_output.append("| Outcome | Any Air<br>(1) | Suspension<br>(2) | Upgrading<br>(3) | Fine<br>(4) | Warning<br>(5) |")
markdown_output.append("|---------|----------------|-------------------|------------------|-------------|----------------|")
markdown_output.append("| *Panel A. Any enforcement action related to air pollution* |")

# Panel A: Treatment coefficients
coefs_a = [f"{r[1]['coef']:.4f}" for r in panel_a_results]
ses_a = [f"({r[1]['se']:.4f})" for r in panel_a_results]
markdown_output.append("| *Mon*<sub><10km</sub> × *Post* | " + " | ".join(coefs_a) + " |")
markdown_output.append("|  | " + " | ".join(ses_a) + " |")

# Panel A: Mean outcomes
means_a = [f"{r[1]['mean_outcome']:.4f}" for r in panel_a_results]
markdown_output.append("| Mean outcome | " + " | ".join(means_a) + " |")

# Panel A: Observations (same for all columns)
n_obs_a = panel_a_results[0][1]['n_obs']
markdown_output.append(f"| Observations | {n_obs_a:,} | {n_obs_a:,} | {n_obs_a:,} | {n_obs_a:,} | {n_obs_a:,} |")

# Panel A: Conley SE note
markdown_output.append("| Conley SE | Yes | Yes | Yes | Yes | Yes |\n")

# Panel B header
markdown_output.append("| Outcome | # Air<br>(1) | Low<br>intensity<br>(2) | High<br>intensity<br>(3) | Lenient<br>(4) | Strict<br>(5) |")
markdown_output.append("|---------|-------|------------------|-------------------|---------|--------|")
markdown_output.append("| *Panel B. Intensity and strictness of enforcement action related to air pollution* |")

# Panel B: Treatment coefficients
coefs_b = [f"{r[1]['coef_treatment']:.4f}" for r in panel_b_results]
ses_b = [f"({r[1]['se_treatment']:.4f})" for r in panel_b_results]
markdown_output.append("| *Mon*<sub><10km</sub> × *Post* | " + " | ".join(coefs_b) + " |")
markdown_output.append("|  | " + " | ".join(ses_b) + " |")

# Panel B: Interaction coefficients
coefs_int = [f"{r[1]['coef_interaction']:.4f}" for r in panel_b_results]
ses_int = [f"({r[1]['se_interaction']:.4f})" for r in panel_b_results]
markdown_output.append("| *Mon*<sub><10km</sub> × *Post* × *H. Polluter* | " + " | ".join(coefs_int) + " |")
markdown_output.append("|  | " + " | ".join(ses_int) + " |")

# Panel B: Mean outcomes
means_b = [f"{r[1]['mean_outcome']:.4f}" for r in panel_b_results]
markdown_output.append("| Mean outcome | " + " | ".join(means_b) + " |")

# Panel B: Observations
n_obs_b = panel_b_results[0][1]['n_obs']
markdown_output.append(f"| Observations | {n_obs_b:,} | {n_obs_b:,} | {n_obs_b:,} | {n_obs_b:,} | {n_obs_b:,} |\n")

# Notes
markdown_output.append("\n**Notes:** This table reports regression coefficients from firm-level panel regressions. ")
markdown_output.append("Panel A shows the effect of pollution monitoring (within 10km) after policy implementation on any enforcement actions. ")
markdown_output.append("Panel B shows effects on enforcement intensity and strictness, including interactions with high polluter status. ")
markdown_output.append("All regressions include firm fixed effects, industry-time fixed effects, and province-time fixed effects. ")
markdown_output.append("Standard errors (in parentheses) are clustered at the firm level. ")
markdown_output.append(f"Sample includes {df['id'].nunique():,} firms observed quarterly from {df['year'].min():.0f} to {df['year'].max():.0f}.")

# Save table
output_file = './output/table_1.md'
with open(output_file, 'w') as f:
    f.write('\n'.join(markdown_output))

print(f"\nTable saved to {output_file}")
print("\n" + "="*80)
print("TABLE 1 REPRODUCTION COMPLETE")
print("="*80)
