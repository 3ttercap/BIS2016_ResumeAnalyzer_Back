"""This module have functions to help TextExtractor."""


from __future__ import print_function
from os import listdir
from os.path import isfile, join, getsize, getmtime, splitext, \
    basename
from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import re
from langdetect import detect
from docx import Document
from docx.document import Document as _Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph


mail_regex = r'[\w\.-]+@[\w\.-]+'


def get_file_list(directory):
    file_list = list()

    for checking_file in listdir(directory):
        file_path = join(directory, checking_file)
        if isfile(file_path):
            file_list.append((
                file_path, basename(file_path),
                splitext(file_path)[-1].strip('.'),
                getsize(file_path), getmtime(file_path)
            ))
        else:
            file_list += get_file_list(file_path)

    return file_list


def pdf_text_extract(file_path):
    page_nums = set()

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())

    f = file(file_path, 'rb')
    for page in PDFPage.get_pages(f, page_nums):
        PDFPageInterpreter(manager, converter).process_page(page)

    f.close()
    converter.close()
    text = output.getvalue()
    output.close()

    text = text.replace("  ", " ")

    return text, detect(text.decode("utf-8").replace("\n", " ").replace("  ", " "))


def docx_iter_block_items(parent):
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("something's not right")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def docx_text_extract(file_path):
    document = Document(file_path)
    content = u''

    for block in docx_iter_block_items(document):
        if isinstance(block, Paragraph):
            content += block.text
        elif isinstance(block, Table):
            no_of_rows = len(block.rows)
            no_of_columns = len(block.columns)
            for i in range(0, no_of_rows):
                for j in range(0, no_of_columns):
                    try:
                        content += block.cell(i, j).text
                        content += "\t"
                    except IndexError:
                        pass
                content += "\n"
        else:
            print("Unknown element %s" % block)
        content += "\n"

    text = content.replace("\n\n", "\n").replace("  ", " ")

    return text, detect(text.replace("\n", " ").replace("  ", " "))


def mail_catcher(text):
    try:
        return re.search(mail_regex, text).group(0)
    except AttributeError:
        return None
