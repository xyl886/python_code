# -*- coding: utf-8 -*-
"""
Created by 18034 on 2024/7/6.
"""

import pypandoc
import os


def convert_md_to_docx(md_path):
    """
    Convert a Markdown file to Docx format.

    Parameters:
    md_path (str): The path to the Markdown file.

    Returns:
    str: The path to the generated Docx file.
    """
    # Check if the input file exists
    if not os.path.isfile(md_path):
        raise FileNotFoundError(f"The file {md_path} does not exist.")

    # Define the output file path
    docx_path = os.path.splitext(md_path)[0] + '.docx'

    # Ensure Pandoc is installed
    try:
        pypandoc.get_pandoc_path()
    except OSError:
        print("Pandoc not found. Downloading Pandoc...")
        pypandoc.download_pandoc()

    # Convert the file
    try:
        pypandoc.convert_file(md_path, 'docx', outputfile=docx_path, extra_args=['--extract-media=./'])
    except RuntimeError as e:
        raise Exception(f"Conversion failed: {e}")

    # Verify the conversion
    if not os.path.isfile(docx_path):
        raise Exception("Conversion failed.")

    return docx_path


# Example usage
if __name__ == '__main__':
    md_file_path = '项目报告.md'
    docx_file_path = convert_md_to_docx(md_file_path)
    print(f"Markdown file converted to Docx at: {docx_file_path}")

