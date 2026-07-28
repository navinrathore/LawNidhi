from abc import ABC, abstractmethod
from typing import List, Dict, Any
from lawnidhi.models.core import ScheduleModel, CaseModel

class BaseScraper(ABC):
    """Abstract base class for scraping cases/orders from websites."""
    @abstractmethod
    def fetch_cases(self, **kwargs) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def download_order(self, diary_number: str, output_dir: str) -> str:
        """Download an order PDF and return the saved file path."""
        pass

class BaseParser(ABC):
    """Abstract base class for parsing ingested documents into structured models."""
    @abstractmethod
    def parse(self, filepath: str) -> ScheduleModel:
        """Parse a document and return a structured ScheduleModel."""
        pass
