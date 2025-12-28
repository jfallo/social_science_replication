#!/bin/bash

for index in {110..110}
do
    # Run the reproduce_autogpt.sh script with the current index
    ./run_reprobench.sh $index
    echo "Ran ./run_reprobench.sh with index: $index"
done