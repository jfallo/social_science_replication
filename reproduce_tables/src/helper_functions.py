import re, os
import fitz
from docling.document_converter import DocumentConverter, PdfFormatOption, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions, TableFormerMode

import pandas as pd
from anyascii import anyascii

# extraction
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



# reproduction
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


# dataframe cleaning
CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')

def has_chinese_characters(df: pd.DataFrame) -> bool:
    string_cols = df.select_dtypes(include= ['object', 'string'])

    return string_cols.astype(str).apply(
        lambda col : col.str.contains(CHINESE_RE, regex= True)
    ).any().any()


def chinese_to_english(df: pd.DataFrame) -> pd.DataFrame:
    return df.map(lambda val : anyascii(val) if isinstance(val, str) else val)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # convert chinese characters if they exist
    if has_chinese_characters(df):
        df = chinese_to_english(df)

    return df