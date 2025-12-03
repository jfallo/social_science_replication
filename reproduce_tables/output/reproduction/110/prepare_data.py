import pandas as pd
import numpy as np
import os

print("Preparing data for Table 1 reproduction...")

# Load firm-level enforcement data
df = pd.read_stata('firm_enf.dta')

print(f"Initial data shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

# Create key variables
# 1. Monitor within 10km dummy
df['mon_10km'] = (df['min_dist'] < 10).astype(int)

# 2. Post dummy (2015 onwards)
df['post'] = (df['year'] >= 2015).astype(int)

# 3. Treatment variable (interaction)
df['mon_10km_post'] = df['mon_10km'] * df['post']

# 4. Create time variable for fixed effects
df['time'] = df['year'].astype(str) + '_Q' + df['quarter'].astype(int).astype(str)

# 5. Create industry-time fixed effect variable
df['industry_time'] = df['industry'].astype(str) + '_' + df['time']

# 6. Create province-time fixed effect variable  
df['prov_time'] = df['prov_id'].astype(str) + '_' + df['time']

# Create Panel B outcome variables
# Count of air enforcement actions (using air column which seems to count total actions)
df['num_air'] = df['air']

# Low intensity: only one enforcement action in quarter
df['low_intensity'] = (df['any_air'] == 1).astype(int)

# High intensity: at least two enforcement actions in quarter
df['high_intensity'] = (df['air'] >= 2).astype(int)

# Lenient: only one type of punishment among shutdown, fine, renovate
# Count how many of these are active
df['num_punishments'] = (df['any_air_shutdown'] + 
                          df['any_air_fine'] + 
                          df['any_air_renovate'])
df['lenient'] = ((df['num_punishments'] == 1) & (df['any_air'] > 0)).astype(int)

# Strict: all three types of punishments
df['strict'] = ((df['any_air_shutdown'] == 1) & 
                (df['any_air_fine'] == 1) & 
                (df['any_air_renovate'] == 1)).astype(int)

# Check sample restrictions
print(f"\nSample restrictions:")
print(f"Firms within 50km: {(df['min_dist'] <= 50).sum()} observations")
print(f"Unique firms: {df['id'].nunique()}")
print(f"Time periods: {df['time'].nunique()}")

# Save processed data
df.to_stata('firm_enf_processed.dta', write_index=False)
print("\nProcessed data saved to firm_enf_processed.dta")

# Print summary statistics for verification
print("\nSummary statistics for key variables:")
print(f"Mean any_air: {df['any_air'].mean():.6f}")
print(f"Mean any_air_shutdown: {df['any_air_shutdown'].mean():.6f}")
print(f"Mean any_air_renovate: {df['any_air_renovate'].mean():.6f}")
print(f"Mean any_air_fine: {df['any_air_fine'].mean():.6f}")
print(f"Mean any_air_warning: {df['any_air_warning'].mean():.6f}")
print(f"Mean mon_10km: {df['mon_10km'].mean():.6f}")
print(f"Mean post: {df['post'].mean():.6f}")

print("\nData preparation complete!")
