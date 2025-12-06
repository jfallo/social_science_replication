"""
Reproduction of Table 1: Firm Level: Pollution Monitoring and Enforcement Activities

This script reproduces Table 1 from the paper using firm-level data
and difference-in-differences estimation with multiple fixed effects.
"""

import pandas as pd
import numpy as np
from linearmodels import PanelOLS
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("REPRODUCING TABLE 1")
print("="*80)

# Load processed data
print("\nLoading processed data...")
df = pd.read_stata('firm_enf.dta')

# Create necessary variables
df['time_id'] = df['year'].astype(str) + '_Q' + df['quarter'].astype(str)
df['industry_time'] = df['industry'].astype(str) + '_' + df['time_id']
df['province_time'] = df['prov_id'].astype(str) + '_' + df['time_id']
df['treatment'] = df['min_dist_10'] * df['post1']

# Create intensity variables
df['low_intensity'] = (df['air'] == 1).astype(float)
df['high_intensity'] = (df['air'] > 1).astype(float)

print(f"Dataset: {len(df)} observations")
print(f"Firms: {df['id'].nunique()}")
print(f"Time periods: {df['time_id'].nunique()}")

# Set index for panel regression
df = df.set_index(['id', 'time_id'])

def run_panel_regression(data, outcome_var, treatment_var='treatment', 
                         controls=None, fe_vars=['industry_time', 'province_time']):
    """
    Run panel regression with firm and time-varying fixed effects
    """
    # Prepare regression data
    reg_data = data[[outcome_var, treatment_var]].copy()
    
    # Add controls if specified
    if controls:
        for control in controls:
            if control in data.columns:
                reg_data[control] = data[control]
    
    # Add fixed effects
    for fe in fe_vars:
        if fe in data.columns:
            reg_data[fe] = data[fe]
    
    # Drop missing values
    reg_data = reg_data.dropna()
    
    # Create formula
    formula = f"{outcome_var} ~ {treatment_var}"
    if controls:
        formula += " + " + " + ".join([c for c in controls if c in reg_data.columns])
    
    # Entity effects (firm FE) + time effects
    fe_string = "EntityEffects"
    
    try:
        # Run regression with entity (firm) fixed effects
        # Industry-time and province-time FE absorbed as additional entity effects
        mod = PanelOLS.from_formula(
            formula + " + EntityEffects",
            data=reg_data,
            drop_absorbed=True
        )
        
        # Cluster standard errors by city
        # Note: clustering at city level requires city identifier
        result = mod.fit(cov_type='clustered', cluster_entity=True)
        
        return result
    except Exception as e:
        print(f"Error in regression for {outcome_var}: {str(e)}")
        return None

# Alternative approach: Use statsmodels with fixed effects
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

def run_fe_regression(data, outcome_var, treatment_var='treatment',
                      controls=None, cluster_var='city_id'):
    """
    Run fixed effects regression with clustered standard errors
    """
    # Reset index to access all columns
    reg_data = data.reset_index()
    
    # Create dummies for fixed effects (firm, industry_time, province_time)
    # This is memory intensive, so we'll use a more efficient approach
    
    # Demean data by firm (entity fixed effects)
    firm_means = reg_data.groupby('id')[[outcome_var, treatment_var]].transform('mean')
    y_demeaned = reg_data[outcome_var] - firm_means[outcome_var]
    X_demeaned = reg_data[treatment_var] - firm_means[treatment_var]
    
    # Further demean by industry-time
    temp_df = pd.DataFrame({
        'y': y_demeaned,
        'X': X_demeaned,
        'industry_time': reg_data['industry_time']
    })
    it_means = temp_df.groupby('industry_time')[['y', 'X']].transform('mean')
    y_demeaned = temp_df['y'] - it_means['y']
    X_demeaned = temp_df['X'] - it_means['X']
    
    # Further demean by province-time
    temp_df = pd.DataFrame({
        'y': y_demeaned,
        'X': X_demeaned,
        'province_time': reg_data['province_time']
    })
    pt_means = temp_df.groupby('province_time')[['y', 'X']].transform('mean')
    y_demeaned = temp_df['y'] - pt_means['y']
    X_demeaned = temp_df['X'] - pt_means['X']
    
    # Run OLS on demeaned data
    X_demeaned = X_demeaned.values.reshape(-1, 1)
    y_demeaned = y_demeaned.values
    
    # Add constant (should be close to zero after demeaning)
    X_with_const = add_constant(X_demeaned)
    
    # Fit model
    model = OLS(y_demeaned, X_with_const)
    
    # Get clustered standard errors
    # For this, we need city_id
    if cluster_var in reg_data.columns:
        clusters = reg_data[cluster_var]
        result = model.fit(cov_type='cluster', cov_kwds={'groups': clusters})
    else:
        result = model.fit(cov_type='HC1')
    
    return result

# Simpler approach: Use fixed effects library
print("\n" + "="*80)
print("PANEL A: Any enforcement action related to air pollution")
print("="*80)

# Reset index for processing
df_reset = df.reset_index()

# Function to compute fixed effects regression manually
def compute_fe_regression(df, y_var, x_var='treatment', fe_vars=['id', 'industry_time', 'province_time'],
                          cluster_var='city_id'):
    """
    Compute fixed effects regression by sequential demeaning
    """
    import scipy.stats as stats
    
    # Create working dataframe
    work_df = df[[y_var, x_var] + fe_vars + [cluster_var]].copy()
    work_df = work_df.dropna()
    
    if len(work_df) == 0:
        return None, None, None, None
    
    # Sequential demeaning for each fixed effect
    y = work_df[y_var].values.copy()
    X = work_df[x_var].values.copy()
    
    for fe in fe_vars:
        # Compute means by group
        fe_groups = work_df[fe].values
        unique_groups = np.unique(fe_groups)
        
        for group in unique_groups:
            mask = fe_groups == group
            if mask.sum() > 0:
                y[mask] -= y[mask].mean()
                X[mask] -= X[mask].mean()
    
    # Run regression
    X = X.reshape(-1, 1)
    
    # OLS: beta = (X'X)^(-1) X'y
    XtX = X.T @ X
    if XtX[0, 0] == 0:
        return None, None, None, None
    
    beta = np.linalg.solve(XtX, X.T @ y)[0]
    
    # Residuals
    resid = y - X.flatten() * beta
    
    # Clustered standard errors
    clusters = work_df[cluster_var].values
    unique_clusters = np.unique(clusters)
    n_clusters = len(unique_clusters)
    
    # Compute cluster-robust variance
    cluster_resid = np.zeros(n_clusters)
    cluster_X = np.zeros(n_clusters)
    
    for i, cluster in enumerate(unique_clusters):
        mask = clusters == cluster
        cluster_resid[i] = (X[mask].flatten() * resid[mask]).sum()
        cluster_X[i] = (X[mask].flatten() ** 2).sum()
    
    # Variance estimate
    V = (cluster_resid ** 2).sum() / XtX[0, 0] ** 2
    se = np.sqrt(V)
    
    # Degrees of freedom adjustment
    n = len(y)
    k = 1  # number of parameters
    se = se * np.sqrt(n_clusters / (n_clusters - 1))  # small sample adjustment
    
    # Mean of outcome
    mean_y = work_df[y_var].mean()
    
    # Number of observations
    n_obs = len(work_df)
    
    return beta, se, mean_y, n_obs

# Panel A: Main results
print("\nColumn 1: Any Air")
coef1, se1, mean1, n1 = compute_fe_regression(df_reset, 'any_air')
print(f"  Coefficient: {coef1:.6f}")
print(f"  Std Error: {se1:.6f}")
print(f"  Mean outcome: {mean1:.4f}")
print(f"  N: {n1}")

print("\nColumn 2: Suspension")
coef2, se2, mean2, n2 = compute_fe_regression(df_reset, 'any_air_shutdown')
print(f"  Coefficient: {coef2:.6f}")
print(f"  Std Error: {se2:.6f}")
print(f"  Mean outcome: {mean2:.4f}")

print("\nColumn 3: Upgrading")
coef3, se3, mean3, n3 = compute_fe_regression(df_reset, 'any_air_renovate')
print(f"  Coefficient: {coef3:.6f}")
print(f"  Std Error: {se3:.6f}")
print(f"  Mean outcome: {mean3:.4f}")

print("\nColumn 4: Fine")
coef4, se4, mean4, n4 = compute_fe_regression(df_reset, 'any_air_fine')
print(f"  Coefficient: {coef4:.6f}")
print(f"  Std Error: {se4:.6f}")
print(f"  Mean outcome: {mean4:.4f}")

print("\nColumn 5: Warning")
coef5, se5, mean5, n5 = compute_fe_regression(df_reset, 'any_air_warning')
print(f"  Coefficient: {coef5:.6f}")
print(f"  Std Error: {se5:.6f}")
print(f"  Mean outcome: {mean5:.4f}")

# Panel B: Heterogeneous effects by polluter type
print("\n" + "="*80)
print("PANEL B: Intensity and strictness of enforcement action related to air pollution")
print("="*80)

# Need to run regression with interaction terms
def compute_fe_regression_interaction(df, y_var, cluster_var='city_id'):
    """
    Compute FE regression with high polluter interaction
    Model: y = β1*treatment + β2*treatment*high_polluter + FE
    """
    import scipy.stats as stats
    
    # Variables
    fe_vars = ['id', 'industry_time', 'province_time']
    work_df = df[[y_var, 'treatment', 'treatment_high_polluter', 'key'] + fe_vars + [cluster_var]].copy()
    work_df = work_df.dropna()
    
    if len(work_df) == 0:
        return None, None, None, None, None, None
    
    # Demean
    y = work_df[y_var].values.copy()
    X1 = work_df['treatment'].values.copy()
    X2 = work_df['treatment_high_polluter'].values.copy()
    
    for fe in fe_vars:
        fe_groups = work_df[fe].values
        unique_groups = np.unique(fe_groups)
        
        for group in unique_groups:
            mask = fe_groups == group
            if mask.sum() > 0:
                y[mask] -= y[mask].mean()
                X1[mask] -= X1[mask].mean()
                X2[mask] -= X2[mask].mean()
    
    # Stack X
    X = np.column_stack([X1, X2])
    
    # OLS
    XtX = X.T @ X
    if np.linalg.matrix_rank(XtX) < 2:
        return None, None, None, None, None, None
    
    beta = np.linalg.solve(XtX, X.T @ y)
    
    # Residuals
    resid = y - X @ beta
    
    # Clustered standard errors
    clusters = work_df[cluster_var].values
    unique_clusters = np.unique(clusters)
    n_clusters = len(unique_clusters)
    
    # Meat of sandwich
    cluster_scores = np.zeros((n_clusters, 2))
    for i, cluster in enumerate(unique_clusters):
        mask = clusters == cluster
        cluster_scores[i] = X[mask].T @ resid[mask]
    
    Sigma = cluster_scores.T @ cluster_scores
    
    # Variance
    XtX_inv = np.linalg.inv(XtX)
    V = XtX_inv @ Sigma @ XtX_inv
    V = V * (n_clusters / (n_clusters - 1))  # small sample adjustment
    
    se = np.sqrt(np.diag(V))
    
    mean_y = work_df[y_var].mean()
    n_obs = len(work_df)
    
    return beta[0], se[0], beta[1], se[1], mean_y, n_obs

print("\nColumn 1: # Air")
b1_1, se1_1, b1_2, se1_2, mean_b1, n_b1 = compute_fe_regression_interaction(df_reset, 'air')
print(f"  Mon<10km × Post: {b1_1:.6f} ({se1_1:.6f})")
print(f"  Mon<10km × Post × H.Polluter: {b1_2:.6f} ({se1_2:.6f})")
print(f"  Mean outcome: {mean_b1:.4f}")
print(f"  N: {n_b1}")

# Create low/high intensity variables
df_reset['low_intensity'] = (df_reset['air'] == 1).astype(float)
df_reset['high_intensity'] = (df_reset['air'] > 1).astype(float)

print("\nColumn 2: Low intensity")
b2_1, se2_1, b2_2, se2_2, mean_b2, n_b2 = compute_fe_regression_interaction(df_reset, 'low_intensity')
print(f"  Mon<10km × Post: {b2_1:.6f} ({se2_1:.6f})")
print(f"  Mon<10km × Post × H.Polluter: {b2_2:.6f} ({se2_2:.6f})")
print(f"  Mean outcome: {mean_b2:.4f}")

print("\nColumn 3: High intensity")
b3_1, se3_1, b3_2, se3_2, mean_b3, n_b3 = compute_fe_regression_interaction(df_reset, 'high_intensity')
print(f"  Mon<10km × Post: {b3_1:.6f} ({se3_1:.6f})")
print(f"  Mon<10km × Post × H.Polluter: {b3_2:.6f} ({se3_2:.6f})")
print(f"  Mean outcome: {mean_b3:.4f}")

print("\nColumn 4: Lenient")
b4_1, se4_1, b4_2, se4_2, mean_b4, n_b4 = compute_fe_regression_interaction(df_reset, 'leni')
print(f"  Mon<10km × Post: {b4_1:.6f} ({se4_1:.6f})")
print(f"  Mon<10km × Post × H.Polluter: {b4_2:.6f} ({se4_2:.6f})")
print(f"  Mean outcome: {mean_b4:.4f}")

print("\nColumn 5: Strict")
b5_1, se5_1, b5_2, se5_2, mean_b5, n_b5 = compute_fe_regression_interaction(df_reset, 'stri')
print(f"  Mon<10km × Post: {b5_1:.6f} ({se5_1:.6f})")
print(f"  Mon<10km × Post × H.Polluter: {b5_2:.6f} ({se5_2:.6f})")
print(f"  Mean outcome: {mean_b5:.4f}")

# Create markdown table
print("\n" + "="*80)
print("CREATING MARKDOWN TABLE")
print("="*80)

markdown_table = """# Table 1—Firm Level: Pollution Monitoring and Enforcement Activities

| Outcome | Any Air<br>(1) | Suspension<br>(2) | Upgrading<br>(3) | Fine<br>(4) | Warning<br>(5) |
|---------|----------------|-------------------|------------------|-------------|----------------|
| **Panel A. Any enforcement action related to air pollution** |
| Mon<sub><10km</sub> × Post | {:.4f}<br>({:.5f}) | {:.4f}<br>({:.5f}) | {:.4f}<br>({:.5f}) | {:.4f}<br>({:.5f}) | {:.6f}<br>({:.5f}) |
| Mean outcome | {:.4f} | {:.4f} | {:.4f} | {:.4f} | {:.5f} |
| Observations | {:,} | {:,} | {:,} | {:,} | {:,} |

| Outcome | # Air<br>(1) | Low intensity<br>(2) | High intensity<br>(3) | Lenient<br>(4) | Strict<br>(5) |
|---------|--------------|----------------------|-----------------------|----------------|---------------|
| **Panel B. Intensity and strictness of enforcement action related to air pollution** |
| Mon<sub><10km</sub> × Post | {:.4f}<br>({:.5f}) | {:.4f}<br>({:.5f}) | {:.6f}<br>({:.5f}) | {:.6f}<br>({:.5f}) | {:.6f}<br>({:.5f}) |
| Mon<sub><10km</sub> × Post × H. Polluter | {:.2f}<br>({:.2f}) | {:.4f}<br>({:.5f}) | {:.2f}<br>({:.4f}) | {:.4f}<br>({:.5f}) | {:.2f}<br>({:.4f}) |
| Mean outcome | {:.4f} | {:.4f} | {:.6f} | {:.5f} | {:.4f} |
| Observations | {:,} | {:,} | {:,} | {:,} | {:,} |

**Notes:** This table reports estimates of the impact of air pollution monitoring on the probability of being subject to different air-pollution-related enforcement actions by the local government. All regressions control for fixed effects specific to firm, industry-by-time, and province-by-time interactions. Robust standard errors clustered on the city in parentheses. Panel B reports heterogeneity for firms identified as high polluters according to ESR during the pre-period. The outcome "low intensity" ("high intensity") corresponds to a dummy variable indicating that a firm received only one (at least two) enforcement actions in a quarter. The outcome "lenient" is a dummy variable that equals one if only one punishment (among "suspension," "upgrading," and "fine") is issued against a firm in a quarter. In contrast, the dummy variable "strict" is defined as one if all three types of punishments are issued against a firm in a quarter.
""".format(
    # Panel A
    coef1, se1, coef2, se2, coef3, se3, coef4, se4, coef5, se5,
    mean1, mean2, mean3, mean4, mean5,
    n1, n2, n3, n4, n5,
    # Panel B
    b1_1, se1_1, b2_1, se2_1, b3_1, se3_1, b4_1, se4_1, b5_1, se5_1,
    b1_2, se1_2, b2_2, se2_2, b3_2, se3_2, b4_2, se4_2, b5_2, se5_2,
    mean_b1, mean_b2, mean_b3, mean_b4, mean_b5,
    n_b1, n_b2, n_b3, n_b4, n_b5
)

# Save table
with open('Table 1.md', 'w') as f:
    f.write(markdown_table)

print("\nTable saved to 'Table 1.md'")
print("\nReproduction complete!")
