import re
from typing import Dict
from .base import InquiryParser

class LocalRegexParser(InquiryParser):
    def parse(self, text: str) -> Dict:
        t = " ".join(text.split())
        m = re.search(r'(\d+(?:\.\d+)?)\s*(pcs?|units?|kg|g|mg|l|ml|liters?|bags?|drums?)\b', t, flags=re.I)
        qty = unit = None
        if m:
            qty, unit = m.group(1), m.group(2)
        else:
            n = re.search(r'\b(\d+(?:\.\d+)?)\b', t)
            if n:
                qty = n.group(1)

        # crude snippet around the match (or first 120 chars)
        if m:
            start = max(0, m.start() - 40)
            end = min(len(t), m.end() + 40)
            snippet = t[start:end]
        else:
            snippet = t[:120]

        return {
            "qty": qty,
            "unit": unit,
            "product_snippet": snippet.strip(),
            "detected": bool(qty or snippet)
        }