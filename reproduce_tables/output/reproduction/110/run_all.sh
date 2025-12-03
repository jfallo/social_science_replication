#!/bin/bash

echo "================================"
echo "Reproducing Table 1"
echo "================================"

# Create directories if needed
mkdir -p output

# Install required packages
echo "Installing required Python packages..."
pip install -q pandas numpy linearmodels statsmodels scipy

# Check if data files exist
if [ ! -f "firm_enf.dta" ]; then
    echo "Error: firm_enf.dta not found!"
    exit 1
fi

# Run data preparation
echo ""
echo "Step 1: Preparing data..."
python prepare_data.py

if [ $? -ne 0 ]; then
    echo "Error in data preparation!"
    exit 1
fi

# Run regression analysis
echo ""
echo "Step 2: Running regressions..."
python reproduce_table1.py

if [ $? -ne 0 ]; then
    echo "Error in regression analysis!"
    exit 1
fi

# Format and save table
echo ""
echo "Step 3: Formatting table..."
python format_table1.py

if [ $? -ne 0 ]; then
    echo "Error in table formatting!"
    exit 1
fi

# Move output to output directory
if [ -f "Table 1.md" ]; then
    mv "Table 1.md" output/
    echo ""
    echo "================================"
    echo "Success! Table 1 saved to output/Table 1.md"
    echo "================================"
else
    echo "Error: Table 1.md not generated!"
    exit 1
fi

# Display the table
echo ""
echo "Table 1 contents:"
cat output/"Table 1.md"

echo ""
echo "Reproduction complete!"
