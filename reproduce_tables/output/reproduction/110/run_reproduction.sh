#!/bin/bash

echo "========================================"
echo "Table 1 Reproduction Script"
echo "========================================"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install pandas numpy scipy statsmodels linearmodels pyreadstat

# Create output directory
echo "Creating directories..."
mkdir -p output

# Run preprocessing
echo ""
echo "========================================"
echo "Running preprocessing..."
echo "========================================"
python preprocess.py

# Run table reproduction
echo ""
echo "========================================"
echo "Running Table 1 reproduction..."
echo "========================================"
python reproduce_table1.py

# Move output files
echo ""
echo "Moving output files..."
mv "Table 1.md" output/ 2>/dev/null || true

echo ""
echo "========================================"
echo "Reproduction complete!"
echo "========================================"
echo "Output files are in the 'output' directory"
echo "- Table 1.md: Reproduced Table 1"

# Deactivate virtual environment
deactivate
