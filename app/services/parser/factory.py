import os
from .local_regex import LocalRegexParser
from .base import InquiryParser

def get_parser() -> InquiryParser:
    backend = os.getenv("PARSER_BACKEND", "LOCAL").upper()
    if backend == "VERTEX":
        from .vertex import VertexParser  # we'll add this file later
        return VertexParser()
    return LocalRegexParser()