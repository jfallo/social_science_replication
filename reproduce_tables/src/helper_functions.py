import re, os, json
import fitz
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode

import pandas as pd
from anyascii import anyascii

# --- extraction --- #
def get_tables_with_docling(pdf_path):
    pdf_options = PdfPipelineOptions(
        do_table_structure= True,
        table_structure_options= TableStructureOptions(
            do_cell_matching= True,
            mode= TableFormerMode.ACCURATE
        )
    )
    converter = DocumentConverter(
        format_options = {
            InputFormat.PDF: PdfFormatOption(
                pipeline_options = pdf_options
            )
        }
    )
    result = converter.convert(source= pdf_path)

    return result.document.tables


def extract_pages_with_tables(paper_input_path, paper_output_path, tmp_path):
    doc = fitz.open(paper_input_path)
    pages_with_tables = []

    for page in range(len(doc)):
        single_page_pdf_path = os.path.join(tmp_path, 'tmp_page.pdf')
        single_page = fitz.open()
        single_page.insert_pdf(doc, from_page= page, to_page= page)
        single_page.save(single_page_pdf_path)
        single_page.close()

        tables = get_tables_with_docling(single_page_pdf_path)
        if len(tables) > 0:
            pages_with_tables.append(page)

    tables_pdf = fitz.open()

    for page in pages_with_tables:
        tables_pdf.insert_pdf(doc, from_page= page, to_page= page)

    tables_pdf.save(paper_output_path)
    tables_pdf.close()
    doc.close()



# --- reproduction --- #
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


def combine_data_files(in_path, out_path):
    dfs = []

    file_names = [name for name in os.listdir(in_path)]

    for file in file_names:
        if file.lower().endswith('.dta') or file.lower().endswith('.csv'):
            print(f'Writing {file}.')
        else:
            continue
        
        file_path = os.path.join(in_path, file)

        # read file
        if file.lower().endswith('.dta'):
            df = pd.read_stata(file_path)
        elif file.lower().endswith('.csv'):
            df = pd.read_csv(file_path)

        # only keep the first 100 rows of the file
        df = df.head(min(len(df),100))
        df['__file__'] = file
        dfs.append(df)

    data_file_paths = []

    for i in range(0, len(dfs), 10):
        out_file = os.path.join(out_path, f'combined_data_{i//10 + 1}.csv')
        data_file_paths.append(out_file)

        batch = dfs[i:i+10]
        pd.concat(batch).to_csv(out_file, index= False, encoding= 'utf-8-sig')

    return data_file_paths