"""Document parsers."""

from applications.enterprise_hub.knowledge_platform.parsers.pdf import PdfParser
from applications.enterprise_hub.knowledge_platform.parsers.docx import DocxParser
from applications.enterprise_hub.knowledge_platform.parsers.xlsx import XlsxParser
from applications.enterprise_hub.knowledge_platform.parsers.pptx import PptxParser
from applications.enterprise_hub.knowledge_platform.parsers.html import HtmlParser
from applications.enterprise_hub.knowledge_platform.parsers.markdown import MarkdownParser
from applications.enterprise_hub.knowledge_platform.parsers.email import EmailParser
from applications.enterprise_hub.knowledge_platform.parsers.images import ImageParser

__all__ = ["PdfParser", "DocxParser", "XlsxParser", "PptxParser", "HtmlParser", "MarkdownParser", "EmailParser", "ImageParser"]
