#!/usr/bin/env python3
"""
Data preprocessing script for Table 1 reproduction
Loads firm_enf.dta and prepares data for analysis
"""

import pandas as pd
import numpy as np
import sys

print("="*80)
print("PREPROCESSING DATA FOR TABLE 1")
print("="*80)

# Load the firm-level enforcement data
print("\nLoading firm_enf.dta...")
try:
    df = pd.read_stata('./data/firm_enf.dta')
    print(f"Successfully loaded {len(df):,} observations")
except Exception as e:
    print(f"Error loading data: {e}")
    sys.exit(1)

# Display basic information
print(f"\nDataset shape: {df.shape}")
print(f"Time period: {df['year'].min():.0f} to {df['year'].max():.0f}")
print(f"Number of unique firms: {df['id'].nunique():,}")
print(f"Number of cities: {df['city_id'].nunique()}")

# Check for required variables
required_vars = ['id', 'year', 'quarter', 'industry', 'prov_id', 
                 'min_dist_10', 'post1',
                 'any_air', 'any_air_shutdown', 'any_air_fine', 
                 'any_air_renovate', 'any_air_warning',
                 'air', 'leni', 'stri', 'key']

missing_vars = [var for var in required_vars if var not in df.columns]
if missing_vars:
    print(f"\nWARNING: Missing variables: {missing_vars}")
    sys.exit(1)
else:
    print("\nAll required variables present")

# Create time identifiers for fixed effects
print("\nCreating time identifiers...")
df['time_id'] = df['year'].astype(int) * 10 + df['quarter'].astype(int)

# Create industry-time and province-time fixed effects identifiers
df['industry_time'] = df['industry'].astype(str) + '_' + df['time_id'].astype(str)
df['prov_time'] = df['prov_id'].astype(str) + '_' + df['time_id'].astype(str)

# Create treatment variable: within 10km of monitor after policy
df['treatment'] = df['min_dist_10'] * df['post1']

# Create indicator for high polluter (key firms from ESR database)
# According to paper, key=1 indicates high polluters
df['high_polluter'] = df['key'].fillna(0)

# Create low and high intensity enforcement indicators
# Low intensity: exactly 1 enforcement action
# High intensity: 2 or more enforcement actions
df['low_intensity'] = (df['air'] == 1).astype(float)
df['high_intensity'] = (df['air'] >= 2).astype(float)

# Lenient: only one type of punishment among shutdown, fine, upgrading
# Strict: all three types of punishment
df['punishment_count'] = (df['any_air_shutdown'].fillna(0) + 
                          df['any_air_fine'].fillna(0) + 
                          df['any_air_renovate'].fillna(0))
df['lenient'] = (df['punishment_count'] == 1).astype(float)
df['strict'] = (df['punishment_count'] == 3).astype(float)

print("\nSummary statistics for key variables:")
print("-" * 80)
for var in ['any_air', 'any_air_shutdown', 'any_air_fine', 
            'any_air_renovate', 'any_air_warning', 'air', 
            'low_intensity', 'high_intensity', 'lenient', 'strict']:
    mean_val = df[var].mean()
    print(f"{var:20s}: Mean = {mean_val:.6f}, N = {df[var].notna().sum():,}")

print("\nTreatment variable summary:")
print(f"Treatment mean: {df['treatment'].mean():.6f}")
print(f"Post mean: {df['post1'].mean():.6f}")
print(f"Within 10km mean: {df['min_dist_10'].mean():.6f}")

print("\nHigh polluter summary:")
print(f"High polluter mean: {df['high_polluter'].mean():.6f}")
print(f"Number of high polluters: {df[df['high_polluter']==1]['id'].nunique():,}")

# Check for missing values in key variables
print("\nMissing values check:")
for var in ['treatment', 'any_air', 'id', 'industry_time', 'prov_time']:
    n_missing = df[var].isna().sum()
    if n_missing > 0:
        print(f"{var}: {n_missing:,} missing values ({n_missing/len(df)*100:.2f}%)")
    else:
        print(f"{var}: No missing values")

# Save preprocessed data
output_file = './output/firm_enf_preprocessed.csv'
print(f"\nSaving preprocessed data to {output_file}...")
df.to_csv(output_file, index=False)
print(f"Saved {len(df):,} observations to {output_file}")

print("\n" + "="*80)
print("PREPROCESSING COMPLETE")
print("="*80)
