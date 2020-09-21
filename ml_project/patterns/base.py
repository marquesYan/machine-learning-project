from typing import List, Tuple
import abc
import json
import logging


class BaseMethod(abc.ABC):
    '''Abstract class for building custom pattern methods.'''

    def name(self) -> str:
        return self.__class__.__name__

    @abc.abstractmethod
    def get_callback(self, dataset: dict) -> callable:
        pass

    @abc.abstractmethod
    def save(self, dataset: dict) -> None:
        pass

    @abc.abstractmethod
    def help(self) -> str:
        pass


class JSONPatternDump(BaseMethod, abc.ABC):
    @abc.abstractmethod
    def dump_content(self, dataset: dict) -> List[Tuple[str, int]]:
        pass

    def save(self, dataset: dict) -> None:
        stats = self.dump_content(dataset)

        max_results = dataset['pattern'].get('max_results')
        if max_results:
            stats = stats[:max_results]

        content = {color: count for color, count in stats}

        with open(dataset['pattern']['output'], 'w') as writer:
            json.dump(content, writer, indent=4)
        logging.info(f'patterns of {dataset["class"]} was saved sucessfully!')
