from typing import List, Tuple, Callable, Any
import abc
import json
import logging


class BaseMethod(abc.ABC):
    '''Abstract class for building custom pattern methods.'''
    def __init__(self, config: dict = {}):
        self.config = config

    def name(self) -> str:
        return self.__class__.__name__

    @abc.abstractmethod
    def run(self, image: object, dataset: dict, path: str) -> None:
        pass

    @abc.abstractmethod
    def dump(self, result_data: list, Any, dataset: dict) -> List[Tuple[str, int]]:
        pass

    @abc.abstractmethod
    def help(self) -> str:
        pass
