import os, re
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

from helper_functions import extract_file_ids, combine_data_files, data_to_string


INPUT_PATH = './input/'
INTERMEDIATE_PATH = './intermediate/'
OUTPUT_PATH = './output/reproduction/'


# get papers to reproduce
papers = [name for name in os.listdir(INPUT_PATH) if os.path.isdir(os.path.join(INPUT_PATH, name))]
papers = ['110']

# get task templates for generating claude task prompts
with open(os.path.join(INPUT_PATH, 'task_templates/read_pdf.txt'), 'r') as file:
    read_pdf_task_template = file.read()
with open(os.path.join(INPUT_PATH, 'task_templates/analyze_data.txt'), 'r') as file:
    analyze_data_task_template = file.read()
with open(os.path.join(INPUT_PATH, 'task_templates/reproduction.txt'), 'r') as file:
    reproduction_task_template = file.read()

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
    
    tables_to_reproduce = '- ' + '\n- '.join([table for table in reproduction_list])

    # prepare task prompts
    read_pdf_task_prompt = read_pdf_task_template.format(
        tables_to_reproduce= tables_to_reproduce
    )
    analyze_data_task_prompt = analyze_data_task_template.format(
        tables_to_reproduce= tables_to_reproduce
    )
    reproduction_task_prompt = reproduction_task_template.format(
        tables_to_reproduce= tables_to_reproduce,
        ex_table= reproduction_list[0]
    )

    client = anthropic.Anthropic()
    
    # upload paper.pdf
    with open(paper_path, 'rb') as pdf:
        file_upload_response = client.beta.files.upload(
            file= ('paper.pdf', pdf, 'application/pdf'),
        )
    file_id = file_upload_response.id

    # define data paths
    data_in_path = os.path.join(in_path, 'data')
    data_out_path = os.path.join(inter_path, 'data')
    os.makedirs(data_out_path, exist_ok= True)

    # convert data to string
    data_string = data_to_string(data_in_path)

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
                        'type': 'document',
                        'source': {
                            'type': 'file',
                            'file_id': file_id
                        }
                    },
                    {
                        'type': 'text',
                        'text': read_pdf_task_prompt
                    }
                ]
            },
            {
                'role': 'assistant',
                'content': "I have read the paper pdf."
            },
            {
                'role': 'user',
                'content': [
                   {
                        'type': 'document',
                        'source': {
                            'type': 'file',
                            'file_id': file_id
                        }
                    },
                    {
                        'type': 'text',
                        'text': analyze_data_task_prompt
                    },
                    {
                        'type': 'text',
                        'text': data_string
                    }
                ]
            },
            {
                'role': 'assistant',
                'content': "I have analyzed and understood the available data and its structure."
            },
            {
                'role': 'user',
                'content': reproduction_task_prompt
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
