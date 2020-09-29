from .base import BaseMethod
from .utils import map_image_pixels
from parallel import wait_futures
from main import get_pattern_output_name

from collections import Counter
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod, abstractproperty
import csv
import logging


class Formatter(ABC):
    def __init__(self, path: str, columns: list, **kwargs):
        self.path = f'{path}.{self.extension}'
        self.columns = columns
        self._add_header(**kwargs)

    @abstractproperty
    def extension(self) -> str:
        pass

    @abstractmethod
    def _add_header(self, **kwargs) -> None:
        pass

    @abstractmethod
    def append(self, content: str) -> None:
        pass


class ArffFormat(Formatter):
    @property
    def extension(self) -> str:
        return 'arff'

    def _add_header(self, **kwargs):
        relation_name = kwargs.get('relation_name')
        assert relation_name, 'Missing relation name in arff header'

        def gen_arff():
            yield f'@relation {relation_name}'

            for column in self.columns:
                yield f'@attribute {column["name"]} {column["type"]}'
            yield '@data'

        with open(self.path, 'w') as writer:
            for line in gen_arff():
                writer.write(f'{line}\n')

    def append(self, lines: list) -> None:
        def gen_arff():
            for line in lines:
                attributes = ','.join((str(value) for value in line))
                yield attributes

        with open(self.path, 'a') as writer:
            for line in gen_arff():
                writer.write(f'{line}\n')


class CsvFormat(Formatter):
    @property
    def extension(self) -> str:
        return 'csv'

    def _add_header(self, **kwargs) -> None:
        fields = [col['name'] for col in self.columns]

        with open(self.path, 'w') as writer:
            csv.DictWriter(writer, fieldnames=fields).writeheader()

    def append(self, rows: list) -> None:
        with open(self.path, 'a') as writer:
            csv_writter = csv.writer(writer)
            csv_writter.writerows(rows)


class NullFormatter(Formatter):
    @property
    def extension(self):
        pass

    def _add_header(self, **kwargs):
        pass

    def append(self, lines: list):
        pass


class FeaturesExtractor(BaseMethod):
    available_formatters = {
        'arff': ArffFormat,
        'csv': CsvFormat,
        'null': NullFormatter
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path, self.feature_layouts, self.formatters = None, [], []

    def init(self, datasets: list) -> None:
        self.path = self.config['feature']['output']

        classes = []
        for dataset in datasets:
            self.feature_layouts.extend(dataset['feature']['layout'])
            classes.append(dataset['class'])

        columns = [dict(name='class', type='{{{}}}'.format(','.join(classes)))]
        for feature in self.feature_layouts:
            columns.append(dict(name=feature['name'], type='real'))
        
        out_format = self.config['feature'].get('format', 'all')

        if out_format == 'all':
            format_classes = list(self.available_formatters.values())
        else:
            format_classes = [self.available_formatters[out_format]]

        self.formatters = [klass(self.path, columns, **self.config['feature']) 
                           for klass in format_classes]

    @property
    def description(self) -> str:            
        return 'Extracts pre-defined image features.'

    @property
    def options(self) -> dict:
        return {
            'ignore_split': True
        }

    def run(self, image: str, dataset: dict, path: str) -> None:
        '''Callback to extract feature from image.'''

        height, width, _ = image.shape

        services = map_image_pixels(image)
        faileds, results = wait_futures(self._extract, 
                                        services, 
                                        height, 
                                        width,
                                        show_status=False,
                                        mask_result=True,
                                        impl=ThreadPoolExecutor,
                                        **dataset['feature'].get('executor_kwargs', {}))

        features_counter = Counter()
        for counter in results:
            features_counter.update(counter)

        pixels_count = width * height

        features = {}
        for feature in self.feature_layouts:
            count = 0
            if feature['name'] in features_counter:
                count = features_counter[feature['name']]
            features[feature['name']] = (count * 100) / pixels_count
        return features

    def _extract(self, img_info: tuple, height: int, width: int) -> Counter:
        x, y, pixel = img_info
        region_args = (width, height, x, y)
        features_counter = Counter()

        for feature in self.feature_layouts:
            if self.is_in_region(*region_args, feature.get('regions', {})) and \
                    self.is_in_color(*pixel, feature['ranges']):
                features_counter.update({feature['name']: 1})
        return features_counter

    def is_in_color(self, red, green, blue, ranges: Dict[str, Dict[str, int]]):
        is_in = lambda needle, initial, end: needle >= initial and needle <= end
        available_ranges = {
            'red': lambda *args: is_in(red, *args),
            'blue': lambda *args: is_in(blue, *args),
            'green': lambda *args: is_in(green, *args),
        }

        for range_name, ranges in ranges.items():
            margin = ranges.get('margin', 0)
            from_, to = ranges['from'] - margin, ranges.get('to', ranges['from']) + margin
            if not available_ranges[range_name](from_, to):
                return False
        return True

    def is_in_region(self, 
                     width: float, 
                     height: float, 
                     x: int, 
                     y: int, 
                     regions: Dict[str, int]) -> bool:
        available_regions = {
            # top level regions
            'bottom': lambda size: x > height * size,
            'top': lambda size: x < height * size,
            'left': lambda size: y < width * size,
            'right': lambda size: y > width * size,
        }

        for region, size in regions.items():
            formatted_size = size / 100
            if not available_regions[region](formatted_size):
                return False
        return True
            
    def dump(self, result_data: list, dataset: dict) -> Any:
        return [[dataset['class'], *list(counter.values())] 
                for counter in result_data]

    def save(self, path: str, result_data: list, dataset: dict) -> None:
        ''' Save results as ARFF Weka format '''

        lines = self.dump(result_data, dataset)

        for formatter in self.formatters:
            formatter.append(lines)
        