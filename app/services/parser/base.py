from abc import ABC, abstractmethod
from typing import Dict

class InquiryParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> Dict:
        ...