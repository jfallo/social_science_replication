import os, re
import anthropic
import pandas as pd
import unicodedata

INPUT_PATH = './input/'
INTERMEDIATE_PATH = './intermediate/'
OUTPUT_PATH = './output/reproduction/'

# helper functions
def extract_file_ids(response):
    file_ids = []

    for item in response.content:
        if item.type == 'bash_code_execution_tool_result':
            content_item = item.content

            if content_item.type == 'bash_code_execution_result':
                for file in content_item.content:
                    if hasattr(file, 'file_id'):
                        file_ids.append(file.file_id)

    return file_ids

def replace_non_latin1_chars(s):
    if not isinstance(s, str):
        return s
    
    return s.encode('latin-1', 'replace').decode('latin-1')

# get papers to reproduce
papers = [name for name in os.listdir(INPUT_PATH) if os.path.isdir(os.path.join(INPUT_PATH, name))]
papers = ['35']

# get task template for generating claude task prompt
with open(os.path.join(INPUT_PATH, 'reproduction_task_template.txt'), 'r') as file:
    task_template = file.read()

# for each paper...
for paper in papers:
    in_path = os.path.join(INPUT_PATH, paper)
    inter_path = os.path.join(INTERMEDIATE_PATH, paper)
    out_path = os.path.join(OUTPUT_PATH, paper)
    paper_path = os.path.join(in_path, 'paper.pdf')

    # create intermediate and output directories if they do not exist
    os.makedirs(inter_path, exist_ok= True)
    os.makedirs(out_path, exist_ok= True)
    os.makedirs(os.path.join(out_path, 'figs'), exist_ok= True)
    os.makedirs(os.path.join(out_path, 'repo'), exist_ok= True)

    # get tables to reproduce
    with open(os.path.join(in_path, 'should_reproduce.txt'), 'r') as file:
        reproduction_list = [line.strip() for line in file.readlines() if len(line.strip()) > 0]

    # prepare task prompt
    task_prompt = task_template.format(
        tables_to_reproduce= '- ' + '\n- '.join([table for table in reproduction_list]),
        ex_table= reproduction_list[0]
    )

    client = anthropic.Anthropic()
    
    # upload paper.pdf
    with open(paper_path, 'rb') as pdf:
        file_upload_response = client.beta.files.upload(
            file= ('paper.pdf', pdf, 'application/pdf'),
        )
    file_id = file_upload_response.id

    # upload data files
    data_in_path = os.path.join(in_path, 'data')
    data_out_path = os.path.join(inter_path, 'data')
    os.makedirs(data_out_path, exist_ok= True)

    data_file_names = [name for name in os.listdir(data_in_path)]
    data_file_ids = []

    for data_file_name in data_file_names:
        print(f'Writing {data_file_name}.')
        
        data_file_in_path = os.path.join(data_in_path, data_file_name)
        data_file_out_path = os.path.join(data_out_path, data_file_name)

        # only keep the first 100 rows of the file
        if data_file_name.lower().endswith('.dta'):
            df = pd.read_stata(data_file_in_path)
            df = df.head(min(len(df),100)).map(replace_non_latin1_chars)
            df.to_stata(data_file_out_path)
        elif data_file_name.lower().endswith('.csv'):
            df = pd.read_csv(data_file_in_path)
            df = df.head(min(len(df),100)).map(replace_non_latin1_chars)
            df.to_csv(data_file_out_path, index= False, encoding= 'utf-8')
        else:
            continue

        # upload file and store file id
        with open(data_file_out_path, 'rb') as data_file:
            data_file_object = client.beta.files.upload(
                file= data_file
            )
        data_file_ids.append(data_file_object.id)

    # message request
    print(f'\nSending message request.')

    response = client.beta.messages.create(
        model= 'claude-sonnet-4-5',
        max_tokens= 20000,
        system= (
            "You are a seasoned digital assistant: capable, intelligent, considerate, and assertive. "
            "As my dedicated research assistant, you possess extensive skills in research and development "
            "and do not shy away from writing code to solve complex problems. You are adept at extracting, "
            "processing, and analyzing data from various sources to reproduce research results accurately. "
            "Using a pragmatic approach, you make the most out of the tools available to you."
        ),
        messages= [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': task_prompt
                    },
                    {
                        'type': 'document',
                        'source': {
                            'type': 'file',
                            'file_id': file_id
                        }
                    }
                ] + [
                    {
                        'type': 'container_upload',
                        'file_id': data_file_id
                    }
                    for data_file_id in data_file_ids
                ]
            }
        ],
        betas= [
            'code-execution-2025-08-25', 
            'files-api-2025-04-14'
        ]
    )

    response_text = response.content[0].text

    with open(os.path.join(out_path, 'response.txt'), 'w') as file:
        file.write(response_text)

    # detect files in response text
    pattern = r'<file="(.*?)">(.*?)</file>'
    output_files = re.findall(pattern, response_text, flags= re.DOTALL)

    for path, content in output_files:
        with open(os.path.join(out_path, path), 'w', encoding= 'utf-8') as file:
            file.write(content.strip() + '\n')

    """
    for file_id in extract_file_ids(response):
        file_metadata = client.beta.files.retrieve_metadata(file_id)
        file_content = client.beta.files.download(file_id)
        file_content.write_to_file(out_path + file_metadata.filename)
    """

""",
tools= [
    {
        "type": "code_execution_20250825",
        "name": "code_execution"
    }
]"""