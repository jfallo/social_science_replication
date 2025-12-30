index=$1

# Clear previous environment
rm -r ./environment/$index/
# Create a directory for the environment based on the index
mkdir -p ./environment/$index

# Create agent workspace
mkdir -p "./data/agents/$index/workspace/data"
# Copy paper, data, and table_templates into agent workspace
cp "../../../input/$index/paper.pdf" "./data/agents/$index/workspace/"
cp -r "../../../input/$index/data/." "./data/agents/$index/workspace/data/"
cp -r "../../../input/$index/table_templates/." "./data/agents/$index/workspace/table_templates/"

# Run the Python script to generate the task, writing the output into task.txt
python3 task_gen.py --index $index

# Read the content of the task.txt file into the task_prompt variable
task_prompt=$(cat ./environment/$index/task.txt)

# Print the task prompt to the terminal
echo "Task prompt:"
echo "$task_prompt"

. autogpt.sh run \
    --ai-task "$task_prompt" --paper-id "$index" \
    --skip-reprompt --skip-news \
    --ai-role "a seasoned digital assistant: capable, intelligent, considerate, and assertive. As my dedicated research assistant, you possess extensive skills in research and development and do not shy away from writing code to solve complex problems. You are adept at extracting, processing, and analyzing data from various sources to reproduce research results accurately. Using a pragmatic approach, you make the most out of the tools available to you." \
    --best-practice "Follow this execution order strictly unless impossible:
        1. Inspect directory tree.
        2. Read paper.pdf.
        3. Identify target tables/figures.
        4. Identify required datasets.
        5. Plan scripts and dependencies.
        6. Install dependencies.
        7. Load each dataset and log row counts, columns, and dtypes.
        8. Write and test preprocessing code.
        9. Write and test table/figure reproduction code.
        10. Write bash script.
        11. Write final report." \
    --best-practice "When verifying the presence of a file or directory, list its contents and inspect at least one representative file before assuming usability." \
    --best-practice "Avoid repeated reading of the same files or reinstalling the same dependencies unless a new error requires it." \
    --best-practice "When extracting information from PDFs, prefer the Python package pdfplumber." \
    --best-practice "If extracting information from HTML outputs (e.g. Jupyter), first convert them to PDF or PNG before extracting content." \
    --best-practice "If you are unsure of what to do, make your best guess." \
    --best-practice "Before running code, determine a list of package/dependency requirements that must be installed for the code to execute. Then install all missing dependencies before running the code." \
    --best-practice "If you find an error in a code file, resolve the error in the same file instead of creating a new file without the error." \
    --constraint "When running Python code, ALWAYS use execute_shell() rather than execute_python_file(), as the latter does not preserve installed dependencies." \
    --constraint "Use flags or modify commands to bypass confirmation prompts to enable unattended execution." \
    --constraint "When navigating directories, use open_folder rather than cd inside execute_shell." \
    --constraint "Do not reference environment variables such as PWD; resolve paths explicitly." \
    --constraint "If a task cannot be completed exactly as specified, still produce runnable code and a detailed failure analysis explaining what failed, why, and what evidence or data are missing." \
    --constraint "Do not assume access to external APIs or API keys when writing or running code." \
    --constraint "If Python code exceeds 30 minutes runtime during testing or stalls without output for more than 10 minutes, terminate execution and refactor to reduce computational complexity." \
    --constraint "When reproducing econometric regressions with fixed effects, never manually construct dummy variables (e.g., via get_dummies or one-hot encoding) for high-dimensional fixed effects. Always use estimator-native fixed-effect absorption." \
    --constraint "Before fitting any regression, explicitly log the number of observations, regressors, and fixed-effect dimensions. Abort and refactor if the number of regressors exceeds 5000." \
    --constraint "Prefer absorbed or sparse representations over dense matrices whenever possible." \
    --continuous \
    --log-level DEBUG \
    --fast_llm "claude-haiku-4-5-20251001" \
    --smart_llm "claude-sonnet-4-5-20250929" \
    --openai_cost_budget 10 2>&1 | tee ./environment/$index/output.txt 


cp "./data/agents/$index/workspace/output/report.txt" "./environment/$index/report.txt"
cp -rf "./data/agents/$index/workspace/output/reproduction_package" "./environment/$index/reproduction_package/" &&
rm -r data/agents/$index/