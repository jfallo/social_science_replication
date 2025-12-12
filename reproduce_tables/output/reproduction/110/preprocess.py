"""
Preprocessing script for Table 1 reproduction
Prepares firm-level enforcement data
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("Starting preprocessing for Table 1...")

# Load the firm-level enforcement data
print("Loading firm_enf.dta...")
df = pd.read_stata('firm_enf.dta')

print(f"Initial data shape: {df.shape}")
print(f"Years in data: {df['year'].min()} to {df['year'].max()}")
print(f"Quarters in data: {df['quarter'].unique()}")

# Verify key variables exist
required_vars = ['id', 'year', 'quarter', 'min_dist_10', 'post1', 'city_id',
                 'industry', 'prov_id', 'key', 'any_air', 'any_air_shutdown',
                 'any_air_renovate', 'any_air_fine', 'any_air_warning',
                 'air', 'air_1', 'air_2', 'leni', 'stri']

missing_vars = [v for v in required_vars if v not in df.columns]
if missing_vars:
    print(f"Warning: Missing variables: {missing_vars}")

# Create treatment variable
df['treatment'] = df['min_dist_10'] * df['post1']

# Create time variable for fixed effects
df['time'] = df['year'].astype(int).astype(str) + '_Q' + df['quarter'].astype(int).astype(str)

# Create industry-time interaction
df['industry_time'] = df['industry'].astype(str) + '_' + df['time']

# Create province-time interaction
df['prov_time'] = df['prov_id'].astype(str) + '_' + df['time']

# Verify high polluter variable
print(f"\nHigh polluter (key) distribution:")
print(df['key'].value_counts())

# Check treatment variable
print(f"\nTreatment variable summary:")
print(f"min_dist_10 mean: {df['min_dist_10'].mean():.4f}")
print(f"post1 mean: {df['post1'].mean():.4f}")
print(f"treatment mean: {df['treatment'].mean():.4f}")

# Check outcome variables
print(f"\nOutcome variable means (Panel A):")
for var in ['any_air', 'any_air_shutdown', 'any_air_renovate', 'any_air_fine', 'any_air_warning']:
    if var in df.columns:
        print(f"{var}: {df[var].mean():.6f}")

print(f"\nOutcome variable means (Panel B):")
for var in ['air', 'air_1', 'air_2', 'leni', 'stri']:
    if var in df.columns:
        print(f"{var}: {df[var].mean():.6f}")

# Save preprocessed data
output_file = 'preprocessed_firm_data.csv'
df.to_csv(output_file, index=False)
print(f"\nPreprocessed data saved to {output_file}")
print(f"Final data shape: {df.shape}")

print("\nPreprocessing complete!")
