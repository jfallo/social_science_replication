"""
Preprocessing script for Table 1 reproduction
Prepares firm-level enforcement data for analysis
"""

import pandas as pd
import numpy as np

print("Loading firm_enf.dta...")
# Load the main firm-level enforcement dataset
df = pd.read_stata('firm_enf.dta')

print(f"Initial dataset shape: {df.shape}")
print(f"Years in data: {df['year'].min()} to {df['year'].max()}")
print(f"Quarters: {df['quarter'].unique()}")

# Check key variables
print("\nKey variables:")
print(f"- Firms with monitor <10km: {df['min_dist_10'].sum()}")
print(f"- Post-2015 observations: {df['post1'].sum()}")
print(f"- Any air enforcement events: {df['any_air'].sum()}")
print(f"- High polluter firms (key=1): {df['key'].sum()}")

# Create time identifiers for fixed effects
df['time_id'] = df['year'].astype(str) + '_Q' + df['quarter'].astype(str)
df['industry_time'] = df['industry'].astype(str) + '_' + df['time_id']
df['province_time'] = df['prov_id'].astype(str) + '_' + df['time_id']

# Create treatment variable: monitor within 10km after 2015
df['treatment'] = df['min_dist_10'] * df['post1']

# For Panel B: create triple interaction with high polluter
df['treatment_high_polluter'] = df['treatment'] * df['key']
df['min_dist_10_high_polluter'] = df['min_dist_10'] * df['key']
df['post1_high_polluter'] = df['post1'] * df['key']

# Verify intensity variables exist
# Based on data inspection: air_1 appears to be low intensity, air_2 high intensity
print("\nIntensity variables:")
print(f"- air (count): mean = {df['air'].mean():.4f}")
if 'air_1' in df.columns:
    print(f"- air_1 (low intensity): mean = {df['air_1'].mean():.4f}")
if 'air_2' in df.columns:
    print(f"- air_2 (high intensity): mean = {df['air_2'].mean():.4f}")
print(f"- leni (lenient): mean = {df['leni'].mean():.4f}")
print(f"- stri (strict): mean = {df['stri'].mean():.4f}")

# Create low and high intensity indicators based on air count
# Low intensity: exactly 1 enforcement action
# High intensity: more than 1 enforcement action
df['low_intensity'] = (df['air'] == 1).astype(float)
df['high_intensity'] = (df['air'] > 1).astype(float)

print("\nCreated intensity variables:")
print(f"- low_intensity: mean = {df['low_intensity'].mean():.4f}")
print(f"- high_intensity: mean = {df['high_intensity'].mean():.4f}")

# Save processed data
print("\nSaving processed data...")
df.to_csv('firm_enf_processed.csv', index=False)
print(f"Saved firm_enf_processed.csv with {len(df)} observations")

print("\nPreprocessing complete!")
