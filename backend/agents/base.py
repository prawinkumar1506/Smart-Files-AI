
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    async def process(self, input_data: Any, context: Optional[Dict] = None) -> Any:
        """
        Process the input data and return the result.
        
        Args:
            input_data: The main input for the agent
            context: Optional shared context dictionary
            
        Returns:
            The processed output
        """
        pass

    def log(self, message: str, level: str = "info"):
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "debug":
            self.logger.debug(message)
