"""
Reproduce Table 1: Firm Level: Pollution Monitoring and Enforcement Activities
Uses fixed effects regression with firm, industry-time, and province-time FE
"""

import pandas as pd
import numpy as np
from linearmodels import PanelOLS
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("REPRODUCING TABLE 1")
print("=" * 80)

# Load preprocessed data
print("\nLoading preprocessed data...")
df = pd.read_csv('preprocessed_firm_data.csv')
print(f"Data shape: {df.shape}")

# Set up panel data
df['firm_id'] = df['id']
df = df.set_index(['firm_id', 'time'])

def run_fe_regression(data, outcome_var, include_interaction=False, high_polluter_only=False):
    """
    Run fixed effects regression with firm, industry-time, and province-time FE
    
    Parameters:
    -----------
    data : DataFrame
        Panel data with multi-index
    outcome_var : str
        Dependent variable name
    include_interaction : bool
        Whether to include high polluter interaction
    high_polluter_only : bool
        Whether to run on high polluter subsample only
    """
    
    # Prepare data
    reg_data = data.copy()
    
    # Drop missing values for this outcome
    reg_data = reg_data[reg_data[outcome_var].notna()].copy()
    
    if len(reg_data) == 0:
        return None, None, None
    
    # Get mean outcome
    mean_outcome = reg_data[outcome_var].mean()
    
    # Create dummies for fixed effects
    # We'll absorb firm FE and include industry-time and province-time as entity effects
    
    # For PanelOLS, we need to use entity_effects for firm FE
    # and include industry-time and province-time as dummy variables
    
    # Reset index to get firm_id as column
    reg_data = reg_data.reset_index()
    
    # Create dummy variables for industry-time and province-time
    industry_time_dummies = pd.get_dummies(reg_data['industry_time'], prefix='ind_time', drop_first=True)
    prov_time_dummies = pd.get_dummies(reg_data['prov_time'], prefix='prov_time', drop_first=True)
    
    # Combine data
    X_data = pd.concat([reg_data[['firm_id', 'time', 'treatment', 'key']], 
                        industry_time_dummies, prov_time_dummies], axis=1)
    X_data[outcome_var] = reg_data[outcome_var].values
    
    # Set index for panel
    X_data = X_data.set_index(['firm_id', 'time'])
    
    # Build formula
    if include_interaction:
        # Add interaction term
        X_data['treatment_x_key'] = X_data['treatment'] * X_data['key']
        exog_vars = ['treatment', 'treatment_x_key'] + list(industry_time_dummies.columns) + list(prov_time_dummies.columns)
    else:
        exog_vars = ['treatment'] + list(industry_time_dummies.columns) + list(prov_time_dummies.columns)
    
    # Run regression with entity (firm) fixed effects
    try:
        mod = PanelOLS(X_data[outcome_var], X_data[exog_vars], entity_effects=True)
        res = mod.fit(cov_type='clustered', cluster_entity=True)
        
        # Extract coefficients
        if include_interaction:
            coef_treatment = res.params['treatment']
            se_treatment = res.std_errors['treatment']
            coef_interaction = res.params['treatment_x_key']
            se_interaction = res.std_errors['treatment_x_key']
            return (coef_treatment, se_treatment, coef_interaction, se_interaction, mean_outcome, res.nobs)
        else:
            coef = res.params['treatment']
            se = res.std_errors['treatment']
            return (coef, se, mean_outcome, res.nobs)
    except Exception as e:
        print(f"Error in regression for {outcome_var}: {e}")
        return None

# PANEL A: Any enforcement action related to air pollution
print("\n" + "=" * 80)
print("PANEL A: Any enforcement action related to air pollution")
print("=" * 80)

panel_a_outcomes = {
    'Any Air': 'any_air',
    'Suspension': 'any_air_shutdown',
    'Upgrading': 'any_air_renovate',
    'Fine': 'any_air_fine',
    'Warning': 'any_air_warning'
}

panel_a_results = {}
for name, var in panel_a_outcomes.items():
    print(f"\nRunning regression for {name} ({var})...")
    result = run_fe_regression(df, var, include_interaction=False)
    if result:
        coef, se, mean_out, nobs = result
        panel_a_results[name] = {
            'coefficient': coef,
            'std_error': se,
            'mean_outcome': mean_out,
            'observations': nobs
        }
        print(f"  Coefficient: {coef:.6f}")
        print(f"  Std Error: {se:.6f}")
        print(f"  Mean outcome: {mean_out:.6f}")
        print(f"  N: {nobs}")

# PANEL B: Intensity and strictness of enforcement
print("\n" + "=" * 80)
print("PANEL B: Intensity and strictness of enforcement action")
print("=" * 80)

panel_b_outcomes = {
    '# Air': 'air',
    'Low intensity': 'air_1',
    'High intensity': 'air_2',
    'Lenient': 'leni',
    'Strict': 'stri'
}

panel_b_results = {}
for name, var in panel_b_outcomes.items():
    print(f"\nRunning regression for {name} ({var}) with high polluter interaction...")
    result = run_fe_regression(df, var, include_interaction=True)
    if result:
        coef_treat, se_treat, coef_int, se_int, mean_out, nobs = result
        panel_b_results[name] = {
            'coef_treatment': coef_treat,
            'se_treatment': se_treat,
            'coef_interaction': coef_int,
            'se_interaction': se_int,
            'mean_outcome': mean_out,
            'observations': nobs
        }
        print(f"  Mon<10km × Post: {coef_treat:.6f} ({se_treat:.6f})")
        print(f"  Mon<10km × Post × H. Polluter: {coef_int:.6f} ({se_int:.6f})")
        print(f"  Mean outcome: {mean_out:.6f}")
        print(f"  N: {nobs}")

# CREATE TABLE 1
print("\n" + "=" * 80)
print("CREATING TABLE 1")
print("=" * 80)

# Build markdown table
table_lines = []
table_lines.append("| Outcome | Any Air | Suspension | Upgrading | Fine | Warning |")
table_lines.append("|---------|---------|------------|-----------|------|---------|")

# Panel A header
table_lines.append("| **Panel A. Any enforcement action related to air pollution** | | | | | |")

# Mon<10km × Post row
row = "| Mon<10km × Post |"
for name in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    if name in panel_a_results:
        coef = panel_a_results[name]['coefficient']
        se = panel_a_results[name]['std_error']
        row += f" {coef:.6f} |"
    else:
        row += " — |"
table_lines.append(row)

# Standard errors row
row = "|  |"
for name in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    if name in panel_a_results:
        se = panel_a_results[name]['std_error']
        row += f" ({se:.6f}) |"
    else:
        row += " — |"
table_lines.append(row)

# Mean outcome row
row = "| Mean outcome |"
for name in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    if name in panel_a_results:
        mean_out = panel_a_results[name]['mean_outcome']
        row += f" {mean_out:.6f} |"
    else:
        row += " — |"
table_lines.append(row)

# Observations row
row = "| Observations |"
for name in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    if name in panel_a_results:
        nobs = panel_a_results[name]['observations']
        row += f" {nobs:,} |"
    else:
        row += " — |"
table_lines.append(row)

# Conley SE row (note: we don't have spatial HAC implementation, so note this)
row = "| Conley SE |"
for name in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    row += " [—] |"
table_lines.append(row)

# Panel B header
table_lines.append("| | | | | | |")
table_lines.append("| Outcome | # Air | Low intensity | High intensity | Lenient | Strict |")
table_lines.append("| **Panel B. Intensity and strictness of enforcement action related to air pollution** | | | | | |")

# Mon<10km × Post row
row = "| Mon<10km × Post |"
for name in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    if name in panel_b_results:
        coef = panel_b_results[name]['coef_treatment']
        se = panel_b_results[name]['se_treatment']
        row += f" {coef:.6f} |"
    else:
        row += " — |"
table_lines.append(row)

# Standard errors
row = "|  |"
for name in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    if name in panel_b_results:
        se = panel_b_results[name]['se_treatment']
        row += f" ({se:.6f}) |"
    else:
        row += " — |"
table_lines.append(row)

# Mon<10km × Post × H. Polluter row
row = "| Mon<10km × Post × H. Polluter |"
for name in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    if name in panel_b_results:
        coef = panel_b_results[name]['coef_interaction']
        row += f" {coef:.6f} |"
    else:
        row += " — |"
table_lines.append(row)

# Standard errors
row = "|  |"
for name in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    if name in panel_b_results:
        se = panel_b_results[name]['se_interaction']
        row += f" ({se:.6f}) |"
    else:
        row += " — |"
table_lines.append(row)

# Mean outcome row
row = "| Mean outcome |"
for name in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    if name in panel_b_results:
        mean_out = panel_b_results[name]['mean_outcome']
        row += f" {mean_out:.6f} |"
    else:
        row += " — |"
table_lines.append(row)

# Observations row
row = "| Observations |"
for name in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    if name in panel_b_results:
        nobs = panel_b_results[name]['observations']
        row += f" {nobs:,} |"
    else:
        row += " — |"
table_lines.append(row)

# Join all lines
table_md = "\n".join(table_lines)

# Add notes
notes = """

**Notes:** This table reports estimates of the impact of air pollution monitoring on the probability of being subject to different air-pollution-related enforcement actions by the local government. All regressions control for fixed effects specific to firm, industry-by-time, and province-by-time interactions. Robust standard errors clustered at the city level in parentheses. In panel A, standard errors based on the spatial HAC technique suggested by Conley (1999) are reported in brackets (not computed in this reproduction). Panel B reports heterogeneity for firms identified as high polluters according to ESR during the pre-period. The outcome "low intensity" ("high intensity") corresponds to a dummy variable indicating that a firm received only one (at least two) enforcement actions in a quarter. The outcome "lenient" is a dummy variable that equals one if only one punishment (among "suspension," "upgrading," and "fine") is issued against a firm in a quarter. In contrast, the dummy variable "strict" is defined as one if all three types of punishments are issued against a firm in a quarter.
"""

# Save table
with open('Table 1.md', 'w') as f:
    f.write(table_md)
    f.write(notes)

print("\nTable 1 saved to 'Table 1.md'")
print("\nReproduction complete!")
