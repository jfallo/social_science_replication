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
    --best-practice "Follow this execution order strictly unless impossible: " \
        "1. Inspect directory tree. " \
        "2. Read paper.pdf. " \
        "3. Identify specified table templates. " \
        "4. Identify required data. " \
        "5. Plan scripts and dependencies. " \
        "6. Install dependencies. " \
        "7. Write and test data preprocessing code. " \
        "8. Write and test table reproduction code. " \
        "9. Write bash script. " \
        "10. Write report." \
    --best-practice "If you are extracting information from a PDF, the preferred utility to use is the Python package pdfplumber." \
    --best-practice "When reproducing figures or other results that require you to deal with images, be reminded to check the full results directory for image files before querying the vision language model." \
    --best-practice "If you are unsure of what to do, make your best guess." \
    --best-practice "When verifying presence of a file or directory, list its contents and inspect at least one representative file before assuming usability." \
    --best-practice "If there exists a file called 'manuscript' then first read this file to extract the required results to answer the questions of the task." \
    --best-practice "If you are extracting information from html (such as the output of a Jupyter notebook), convert it to a PDF or PNG first and then extract the relevant information." \
    --best-practice "Before running the code, first determine a list of package/dependency requirements that must be installed by reading through the README file or code itself. Then install those dependencies before running the code." \
    --best-practice "Before performing any analysis, explicitly load each dataset and print or log its columns, dtypes, and row counts." \
    --best-practice "When writing code, be aware of truncation errors from long code files. Keep code clear, concise, or split into smaller files." \
    --best-practice "If you find an error in a code file, resolve the error in the same file instead of creating a new file without the error." \
    --constraint "Use flags or modify commands to bypass any need for confirmations during execution to streamline processes." \
    --constraint "If a task cannot be completed exactly as specified, you must still produce runnable code and a detailed failure analysis explaining precisely why reproduction failed and what evidence is missing." \
    --constraint "Avoid repeated reading of the same files or reinstalling the same dependencies unless a new error requires it." \
    --constraint "You may wish to write and run a Python script to complete the task, especially if the task requires access to the Internet or other libraries. However, assume that I do NOT have API keys to use external services." \
    --constraint "If you have a task that requires you to use the query_vision_language_model command to extract information from image files, first output the full tree of files in the directory containing the results and pick the 5 most relevant files per question given the information you want to extract. Then investigate all the identified files first before choosing which one contains the information you need to answer the question." \
    --constraint "Do not include environmental variables such as 'PWD' as an argument for the 'execute_shell' command. Instead, determine the value of the variable and directly input it to the command. For example, by using the absolute path instead of 'PWD'." \
    --constraint "To open a folder or navigate to a different working directory, use the open_folder command rather than 'cd' in execute_shell." \
    --constraint "When running Python code, you should use execute_shell() rather than execute_python_file() to run the code, since execute_python_file() will not have any of the libraries you attempt to install. In other words, NEVER use execute_python_file()." \
    --constraint "Before you are done, make sure that the keys of the report.json you write match the ones in the task specified by the user. Refine your results if they do not." \
    --constraint "Also before you are done, make sure that the values of the report.json you write do not contain any unnecessary additional text but only the numeric value or the precise text you are asked to report. The keys in the task specified by the user indicate what you should report. Refine your results if they do not." \
    --continuous \
    --log-level DEBUG \
    --fast_llm "gpt-4o-2024-05-13" \
    --smart_llm "claude-sonnet-4-5-20250929" \
    --openai_cost_budget 4 2>&1 | tee ./environment/$index/output.txt 


mkdir -p "./environment/$index/workspace/" &&
cp -rf "data/agents/$index/workspace/." "./environment/$index/workspace/" &&
rm -r data/agents/$index/