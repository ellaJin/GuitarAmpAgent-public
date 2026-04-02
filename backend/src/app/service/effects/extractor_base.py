from abc import ABC, abstractmethod
from typing import List


class EffectExtractor(ABC):

    @abstractmethod
    def extract(self, text: str) -> List:
        """
        Return a list of RawEffect-like objects
        """
        pass
