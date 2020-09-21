from .base import JSONPatternDump
from .utils import rgb2hex

from collections import Counter
from typing import Tuple, Any


class MostCommonColor(JSONPatternDump):
    def __init__(self, config: dict = {}):
        self.counters = {}

    def help(self):
        return 'Collects the top colors in all images.'

    def get_callback(self, dataset: dict) -> callable:
        self.counters[dataset['class']] = Counter()

        return self._color_counter

    def _color_counter(self, 
                       _: str, 
                       dataset: dict, 
                       rgb: list) -> Tuple[Counter, callable]:
        '''Helper wrapper to count colors.'''

        # convert rgb into hex
        hex_format = rgb2hex(*rgb)

        color_counter = self.counters[dataset['class']]

        # increment this hex color
        color_counter.update({hex_format: 1})

    def dump_content(self, dataset: dict) -> Any:
        name = dataset['class']
        patterns = self.counters[name].most_common()
        return patterns