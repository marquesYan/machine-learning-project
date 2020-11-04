from .base import BaseMethod
from .features_extractor import (
    CsvFormat, 
    ArffFormat, 
    NullFormatter
)
from parallel import wait_futures
import librosa
import numpy

from concurrent.futures import ThreadPoolExecutor
from typing import Any
from collections import Counter
import logging


def _parse_mfcc(data, sr=None):
    mfcc = librosa.feature.mfcc(data, sr=sr)
    return list(map(numpy.mean, mfcc))


class AudioExtractor(BaseMethod):
    available_formatters = {
        'arff': ArffFormat,
        'csv': CsvFormat,
        'null': NullFormatter
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.path, self.formatters = None, []

    def init(self, datasets: list) -> None:
        self.path = self.config['feature']['output']

        classes = []
        for dataset in datasets:
            classes.append(dataset['class'])

        columns = [dict(name='class', type=classes)]
        for name in self.available_feature_names:
            columns.append(dict(name=name, type='real'))
        
        out_format = self.config['feature'].get('format', 'all')

        if out_format == 'all':
            format_classes = list(self.available_formatters.values())
        else:
            format_classes = [self.available_formatters[out_format]]

        self.formatters = [klass(self.path, columns, **self.config['feature']) 
                           for klass in format_classes]

    @property
    def available_feature_names(self) -> list:
        defaults = ['cqt', 'spct_contrast']
        for i in range(1, 21):
            defaults.append(f'mfcc{i}')
        return defaults

    @property
    def description(self) -> str:            
        return 'Extracts pre-defined audio features.'

    @property
    def options(self) -> dict:
        return {
            'ignore_split': True,
            'service_impl': ThreadPoolExecutor,
        }

    def run(self, dataset: dict, path: str) -> None:
        '''Callback to extract feature from image.'''

        data, sr = librosa.load(path)
        cqt = librosa.feature.chroma_cqt(data, sr=sr)
        spct_contrast = librosa.feature.spectral_contrast(data, sr=sr) 

        features = {
            'cqt': numpy.mean(cqt),
            'spct_contrast': numpy.mean(spct_contrast),
        }

        for i, mfcc in enumerate(_parse_mfcc(data, sr=sr)):
            features[f'mfc{i}'] = mfcc

        return features
            
    def dump(self, result_data: list, dataset: dict) -> Any:
        return [[dataset['class'], *list(counter.values())] 
                for counter in result_data]

    def save(self, path: str, result_data: list, dataset: dict) -> None:
        ''' Save results as ARFF Weka format '''

        lines = self.dump(result_data, dataset)

        for formatter in self.formatters:
            formatter.append(lines)
        