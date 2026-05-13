from abc import ABC, abstractmethod
from typing import Any


class AgentInterface(ABC):
    @abstractmethod
    def initialize_client(self) -> Any:
        pass

    @abstractmethod
    def generate_response(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def count_tokens(self, *args, **kwargs) -> Any:
        pass
