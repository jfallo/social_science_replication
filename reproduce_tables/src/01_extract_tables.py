import os, time
import anthropic

from helper_functions import extract_pages_with_tables

INPUT_PATH = './input/'
INTERMEDIATE_PATH = './intermediate/'
OUTPUT_PATH = './output/ground_truth/'


def extract_tables(paper, reproduction_list, paper_path, out_path):
    print(f'Writing tables for Paper {paper}.')

    client = anthropic.Anthropic()

    # upload paper.pdf
    with open(paper_path, 'rb') as pdf:
        file_upload_response = client.beta.files.upload(
            file= ('paper.pdf', pdf, 'application/pdf'),
        )
    file_id = file_upload_response.id

    print('Uploaded paper.pdf.\n')

    for table in reproduction_list:
        print('Sleeping.')
        time.sleep(30)

        # generate task by writing tables to reproduce to task template
        with open(os.path.join(INPUT_PATH, 'task_templates/extraction.txt'), 'r') as file:
            task_template = file.read()
        
        # create task prompt
        task_prompt = task_template.format(table_name= table)

        # message request
        print('Sending message request.')

        response = client.beta.messages.create(
            model= 'claude-sonnet-4-5',
            max_tokens= 2500,
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
                    ]
                }
            ],
            betas= [
                'code-execution-2025-08-25', 
                'files-api-2025-04-14'
            ]
        )

        # write response
        with open(os.path.join(out_path, f'{table}.md'), 'w') as file:
            file.write(response.content[0].text)

        print(f'{table} written.\n')


papers = [name for name in os.listdir(INPUT_PATH) if os.path.isdir(os.path.join(INPUT_PATH, name))]

for paper in papers:
    in_path = os.path.join(INPUT_PATH, paper)
    inter_path = os.path.join(INTERMEDIATE_PATH, paper)
    out_path = os.path.join(OUTPUT_PATH, paper)
    os.makedirs(inter_path, exist_ok= True)
    os.makedirs(out_path, exist_ok= True)

    # get tables to reproduce
    with open(os.path.join(in_path, 'should_reproduce.txt'), 'r') as file:
        reproduction_list = [line.strip() for line in file.readlines() if len(line.strip()) > 0]

    # reduce pdf size
    paper_path = os.path.join(in_path, 'paper.pdf')
    reduced_paper_path = os.path.join(inter_path, f'paper.pdf')
    if not os.path.exists(reduced_paper_path):
        extract_pages_with_tables(paper_path, reduced_paper_path, tmp_path= INTERMEDIATE_PATH)

    # extract tables
    extract_tables(paper, reproduction_list, reduced_paper_path, out_path)