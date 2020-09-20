from collections import Counter
from typing import Tuple, Any, List
import abc
import json
import logging


def rgb2hex(red, green, blue):
    # see https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    return '0x%02x%02x%02x' % (red, green, blue)


def load_methods():
    '''Entry point function to register a new method'''

    return [
        MostCommonColor(),
        MostOccurenceColor()
    ]


class BaseMethod(abc.ABC):
    '''Abstract class for building custom pattern methods.'''

    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def get_callback(self, dataset: dict) -> tuple:
        pass

    @abc.abstractmethod
    def save(self, dataset: dict) -> None:
        pass


class JSONPatternDump(BaseMethod, abc.ABC):
    @abc.abstractmethod
    def dump_content(self, dataset: dict) -> List[Tuple[str, int]]:
        pass

    def save(self, dataset: dict) -> tuple:
        stats = self.dump_content(dataset)

        max_results = dataset['pattern'].get('max_results')
        if max_results:
            stats = stats[:max_results]

        content = {color: count for color, count in stats}

        with open(dataset['pattern']['output'], 'w') as writer:
            json.dump(content, writer, indent=4)
        logging.info(f'patterns of {dataset["class"]} was saved sucessfully!')


class MostCommonColor(JSONPatternDump):
    def __init__(self):
        self.counters = {}

    def name(self):
        return 'mcc'

    def get_callback(self, dataset: dict) -> tuple:
        main_counter, pattern_wrapper = self._with_color_pattern_counter()

        self.counters[dataset['class']] = main_counter

        return pattern_wrapper

    def _with_color_pattern_counter(self) -> Tuple[Counter, callable]:
        '''Helper wrapper to count color patterns.'''

        color_counter = Counter()
        def wrapper(_: str, rgb: list) -> None:
            # convert rgb into hex
            hex_format = rgb2hex(*rgb)

            # increment this hex color
            color_counter.update({hex_format: 1})

        return color_counter, wrapper

    def dump_content(self, dataset: dict) -> Any:
        name = dataset['class']
        patterns = self.counters[name].most_common()
        return patterns

    
class MostOccurenceColor(JSONPatternDump):
    def __init__(self):
        self.occurrences = {}

    def name(self) -> str:
        return 'moc'

    def get_callback(self, dataset: dict) -> tuple:
        occurrences, occurrence_wrapper = self._with_occurrence_registration()

        self.occurrences[dataset['class']] = occurrences

        return occurrence_wrapper

    def _with_occurrence_registration(self) -> Tuple[set, callable]:

        occurrences = {}
        def wrapper(path: str, rgb: list) -> None:
            # convert rgb into hex
            hex_format = rgb2hex(*rgb)

            if not path in occurrences.keys():
                occurrences[path] = set()
            occurrences[path].add(hex_format)
            memory_summary()
            
        return occurrences, wrapper

    def dump_content(self, dataset: dict) -> Any:
        result = {}
        for hexadecimals in self.occurrences[dataset['class']].values():
            for hex_value in hexadecimals:
                if hex_value in result.keys():
                    result[hex_value] += 1
                else:
                    result[hex_value] = 1
        most_occurrences = sorted(result.items(), key=lambda item: item[1], reverse=True)
        return most_occurrences
        










