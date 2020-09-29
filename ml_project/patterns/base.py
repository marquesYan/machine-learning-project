from typing import List, Tuple, Callable, Any
import abc
import json
import logging


class BaseMethod(abc.ABC):
    '''Abstract class for building custom pattern methods.'''
    def __init__(self, config: dict = {}):
        self.config = config

    def init(self, datasets: list) -> None:
        pass
    
    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def options(self) -> dict:
        return {}

    @abc.abstractproperty
    def description(self) -> str:
        pass

    @abc.abstractmethod
    def run(self, image: object, dataset: dict, path: str) -> None:
        pass

    @abc.abstractmethod
    def dump(self, result_data: list, Any, dataset: dict) -> List[Tuple[str, int]]:
        pass

    def save(self, path: str, result_data: list, Any, dataset: dict) -> None:
        stats = method.dump(results, dataset)

        max_results = dataset['pattern'].get('max_results')
        if max_results:
            stats = stats[:max_results]

        content = {color: count for color, count in stats}

        with open(path, 'w') as writer:
            json.dump(content, writer, indent=4)
