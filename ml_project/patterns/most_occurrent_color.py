from .base import BaseMethod
from .utils import image2hex
from parallel import wait_futures, display_status

from collections import Counter
from typing import List, Tuple, Set
from concurrent import futures
from multiprocessing import Manager
import logging


class MostOccurentColor(BaseMethod):

    def help(self) -> str:
        return 'Collects the colors which has the most frequency.'
        
    def run(self, image: object, dataset: dict, path: str) -> Set:
        hex_map = set()
        for pixel in image2hex(image):
            hex_map.add(pixel)
        return hex_map
    
    def _count_pixel_occurrences(self, input_data: tuple, results: list) -> Counter:
        current_index, pixels = input_data
        counter = Counter()

        for pixel in pixels:
            for other_index, other_pixels in enumerate(results):
                if current_index != other_index and pixel in other_pixels:
                    counter.update({pixel: 1})

        return counter

    def dump(self, hex_map, dataset: dict) -> List[Tuple[str, int]]:
        final_result = Counter()
        pixel_info = [(index, pixels) for index, pixels in enumerate(hex_map)]
        logging.info('starting jobs to count pixel occurrences')
        faileds, counters = wait_futures(self._count_pixel_occurrences, 
                                         pixel_info, 
                                         hex_map,
                                         show_status=False,
                                         mask_result=True,
                                         **dataset['pattern'].get('executor_kwargs', {}))
        logging.info('pixel occurrence count just finished')
        for counter in counters:
            for key, count in counter.items():
                if key not in final_result.keys():
                    final_result.update({key: count})

        return final_result.most_common()