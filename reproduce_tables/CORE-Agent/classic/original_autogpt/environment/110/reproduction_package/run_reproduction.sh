#!/bin/bash

################################################################################
# Reproduction Script for Table 1:
# Firm Level: Pollution Monitoring and Enforcement Activities
#
# This script automates the complete reproduction workflow:
# 1. Creates virtual environment and installs dependencies
# 2. Creates necessary directories
# 3. Runs data preprocessing
# 4. Reproduces Table 1
################################################################################

set -e  # Exit on any error

echo "================================================================================"
echo "REPRODUCTION WORKFLOW FOR TABLE 1"
echo "================================================================================"
echo ""

# Store the working directory
WORKDIR=$(pwd)
echo "Working directory: $WORKDIR"
echo ""

################################################################################
# Step 1: Create and activate virtual environment
################################################################################
echo "-------------------------------------------------------------------------------"
echo "Step 1: Setting up Python virtual environment"
echo "-------------------------------------------------------------------------------"

if [ -d "venv" ]; then
    echo "Virtual environment already exists. Removing old environment..."
    rm -rf venv
fi

echo "Creating new virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip --quiet

echo "✓ Virtual environment ready"
echo ""

################################################################################
# Step 2: Install required packages
################################################################################
echo "-------------------------------------------------------------------------------"
echo "Step 2: Installing required Python packages"
echo "-------------------------------------------------------------------------------"

echo "Installing core dependencies:"
echo "  - pandas (data manipulation)"
echo "  - numpy (numerical operations)"
echo "  - pyfixest (fixed effects regression)"
echo ""

pip install pandas numpy pyfixest --quiet

echo "✓ All dependencies installed"
echo ""

################################################################################
# Step 3: Create output directories
################################################################################
echo "-------------------------------------------------------------------------------"
echo "Step 3: Creating output directories"
echo "-------------------------------------------------------------------------------"

mkdir -p output

echo "✓ Output directory ready"
echo ""

################################################################################
# Step 4: Run data preprocessing
################################################################################
echo "-------------------------------------------------------------------------------"
echo "Step 4: Preprocessing data"
echo "-------------------------------------------------------------------------------"

if [ ! -f "preprocess_data.py" ]; then
    echo "ERROR: Preprocessing script not found!"
    exit 1
fi

echo "Running preprocessing script..."
echo "  Input: data/firm_enf.dta"
echo "  Output: output/firm_enf_preprocessed.csv"
echo ""

python3 preprocess_data.py

if [ ! -f "output/firm_enf_preprocessed.csv" ]; then
    echo "ERROR: Preprocessing failed - output file not created"
    exit 1
fi

echo "✓ Data preprocessing complete"
echo ""

################################################################################
# Step 5: Reproduce Table 1
################################################################################
echo "-------------------------------------------------------------------------------"
echo "Step 5: Reproducing Table 1"
echo "-------------------------------------------------------------------------------"

if [ ! -f "reproduce_table1.py" ]; then
    echo "ERROR: Table 1 reproduction script not found!"
    exit 1
fi

echo "Running Table 1 reproduction..."
echo "  Processing 2,087,136 firm-quarter observations"
echo "  This may take several minutes..."
echo ""

python3 reproduce_table1.py

if [ ! -f "output/table_1.md" ]; then
    echo "ERROR: Table 1 reproduction failed - output file not created"
    exit 1
fi

echo "✓ Table 1 reproduction complete"
echo ""

################################################################################
# Step 6: Verify outputs
################################################################################
echo "-------------------------------------------------------------------------------"
echo "Step 6: Verifying outputs"
echo "-------------------------------------------------------------------------------"

echo "Checking output files:"

if [ -f "output/firm_enf_preprocessed.csv" ]; then
    SIZE=$(wc -c < "output/firm_enf_preprocessed.csv" | xargs)
    echo "  ✓ firm_enf_preprocessed.csv (${SIZE} bytes)"
else
    echo "  ✗ firm_enf_preprocessed.csv NOT FOUND"
fi

if [ -f "output/table_1.md" ]; then
    LINES=$(wc -l < "output/table_1.md" | xargs)
    echo "  ✓ table_1.md (${LINES} lines)"
else
    echo "  ✗ table_1.md NOT FOUND"
fi

echo ""

################################################################################
# Summary
################################################################################
echo "================================================================================"
echo "REPRODUCTION COMPLETE"
echo "================================================================================"
echo ""
echo "Output files:"
echo "  - output/table_1.md         : Final reproduced table in Markdown format"
echo "  - output/firm_enf_preprocessed.csv : Preprocessed data (intermediate)"
echo ""
echo "To view the reproduced table:"
echo "  cat output/table_1.md"
echo ""
echo "To deactivate the virtual environment:"
echo "  deactivate"
echo ""
echo "================================================================================"
