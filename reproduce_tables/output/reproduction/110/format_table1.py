import pickle
import numpy as np

print("Formatting Table 1...")

# Load results
with open('table1_results.pkl', 'rb') as f:
    results = pickle.load(f)

def format_coef(coef, se):
    """Format coefficient with standard error in parentheses"""
    if np.isnan(coef) or np.isnan(se):
        return "—"
    return f"{coef:.6f}\n({se:.6f})"

def format_number(num):
    """Format number with commas"""
    if np.isnan(num):
        return "—"
    return f"{int(num):,}"

# Create markdown table
markdown = "# Table 1—Firm Level: Pollution Monitoring and Enforcement Activities\n\n"

# Column headers
markdown += "| Outcome | Any Air | Suspension | Upgrading | Fine | Warning |\n"
markdown += "|---------|---------|------------|-----------|---------|----------|\n"

# Panel A
markdown += "| **Panel A. Any enforcement action related to air pollution** | | | | | |\n"

# Mon<10km × Post row
coefs = []
for outcome in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    res = results['panel_a'][outcome]
    coefs.append(format_coef(res['coefficient'], res['std_error']))

markdown += "| *Mon*<10km × *Post* | " + " | ".join(coefs) + " |\n"

# Mean outcome row
means = []
for outcome in ['Any Air', 'Suspension', 'Upgrading', 'Fine', 'Warning']:
    res = results['panel_a'][outcome]
    means.append(f"{res['mean_outcome']:.6f}")

markdown += "| Mean outcome | " + " | ".join(means) + " |\n"

# Observations row
obs = format_number(results['n_obs'])
markdown += f"| Observations | {obs} | {obs} | {obs} | {obs} | {obs} |\n"

# Add spacing
markdown += "\n"

# Panel B header
markdown += "| Outcome | # Air | Low intensity | High intensity | Lenient | Strict |\n"
markdown += "|---------|--------|---------------|----------------|----------|--------|\n"

# Panel B  
markdown += "| **Panel B. Intensity and strictness of enforcement action related to air pollution** | | | | | |\n"

# Mon<10km × Post row
coefs = []
for outcome in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    res = results['panel_b'][outcome]
    coefs.append(format_coef(res['coefficient'], res['std_error']))

markdown += "| *Mon*<10km × *Post* | " + " | ".join(coefs) + " |\n"

# Mean outcome row
means = []
for outcome in ['# Air', 'Low intensity', 'High intensity', 'Lenient', 'Strict']:
    res = results['panel_b'][outcome]
    means.append(f"{res['mean_outcome']:.6f}")

markdown += "| Mean outcome | " + " | ".join(means) + " |\n"

# Observations row
markdown += f"| Observations | {obs} | {obs} | {obs} | {obs} | {obs} |\n"

# Add notes
markdown += "\n\n"
markdown += "*Notes:* This table reports estimates of the impact of air pollution monitoring on the probability of being subject to different air-pollution-related enforcement actions by the local government. All regressions control for fixed effects specific to firm, industry-by-time, and province-by-time interactions. Robust standard errors clustered at the city level in parentheses. Panel B reports heterogeneity for firms identified as high polluters. The outcome \"low intensity\" (\"high intensity\") corresponds to a dummy variable indicating that a firm received only one (at least two) enforcement actions in a quarter. The outcome \"lenient\" is a dummy variable that equals one if only one punishment (among \"suspension,\" \"upgrading,\" and \"fine\") is issued against a firm in a quarter. In contrast, the dummy variable \"strict\" is defined as one if all three types of punishments are issued against a firm in a quarter.\n"

# Save to file
with open('Table 1.md', 'w') as f:
    f.write(markdown)

print("Table 1 formatted and saved to 'Table 1.md'")
print("\nPreview:")
print(markdown[:500] + "...")
