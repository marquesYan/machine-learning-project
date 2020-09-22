from .base import BaseMethod
from .utils import image2hex

from collections import Counter
from typing import Tuple, Any
from multiprocessing import Manager


class MostCommonColor(BaseMethod):

    def help(self):
        return 'Collects the top colors in all images.'

    def run(self, image: str, dataset: dict, path: str) -> None:
        '''Callback to count colors.'''

        counter = Counter()

        for pixel_hex in image2hex(image):
            # increment this hex color
            counter.update({pixel_hex: 1})
        return counter

    def dump(self, result_data: list, dataset: dict) -> Any:
        final_counter = Counter()
        for counter in result_data:
            final_counter.update(counter)
        return final_counter.most_common()