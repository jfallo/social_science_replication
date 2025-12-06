#!/bin/bash

# Bash script to reproduce Table 1
# Creates virtual environment, installs dependencies, and runs all scripts

echo "=================================="
echo "TABLE 1 REPRODUCTION SCRIPT"
echo "=================================="

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo ""
echo "Installing required packages..."
pip install pandas numpy scipy statsmodels linearmodels

# Create output directory if it doesn't exist
echo ""
echo "Creating output directories..."
mkdir -p output

# Run preprocessing script
echo ""
echo "=================================="
echo "RUNNING PREPROCESSING"
echo "=================================="
python preprocess.py

# Run table reproduction script
echo ""
echo "=================================="
echo "REPRODUCING TABLE 1"
echo "=================================="
python reproduce_table1.py

# Move output files
echo ""
echo "Moving output files..."
if [ -f "Table 1.md" ]; then
    mv "Table 1.md" output/
    echo "Table 1.md moved to output/"
fi

# Deactivate virtual environment
echo ""
echo "Deactivating virtual environment..."
deactivate

echo ""
echo "=================================="
echo "REPRODUCTION COMPLETE"
echo "=================================="
echo "Results saved in output/"
echo ""
