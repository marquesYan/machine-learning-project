from .base import JSONPatternDump
from .utils import (
    FlushOnDemand, 
    TemporaryObject, 
    rgb2hex
)

from collections import Counter
from tempfile import TemporaryDirectory
from typing import Any
import logging
import os
import json


class MostOccurentColor(JSONPatternDump):
    def __init__(self, config: dict = {}):
        self.tmpdirs = {}
        self.flush_system = FlushOnDemand(config.get('flush_idle', 15), 
                                          config.get('flush_interval', 30))

    def help(self) -> str:
        return 'Collects the colors which has the most frequency.'

    def get_callback(self, dataset: dict) -> tuple:
        tmpdir = TemporaryDirectory()
        self.tmpdirs[dataset['class']] = tmpdir
        logging.debug('created temporary directory for [%s] at %s', dataset['class'], tmpdir.name)

        return self._occurrence_cb

    def _occurrence_cb(self, path: str, dataset: dict, rgb: list):
        if not self.flush_system.has(path):
            name, _ = os.path.splitext(os.path.basename(path))
            tmpdir = self.tmpdirs[dataset['class']]
            target_path = os.path.join(tmpdir.name, f'{name}.json') 

            tmpobj = TemporaryObject(target_path=target_path,
                                     key=path,
                                     objects=set())

            self.flush_system.update(tmpobj)

        hex_format = rgb2hex(*rgb)
        tmpobj = self.flush_system.get(path)
        tmpobj.objects.add(hex_format)

    def dump_content(self, dataset: dict) -> Any:
        self.flush_system.flush_all()

        result = Counter()

        tmpdir = self.tmpdirs[dataset['class']]

        with os.scandir(tmpdir.name) as scan:
            for entry in scan:
                logging.debug('reading entry at %s', entry.path)
                with open(entry.path, 'rb') as reader:
                    hexadecimals = json.load(reader)
                
                for hex_value in hexadecimals:
                    result.update({hex_value: 1})

        most_occurrences = result.most_common()
        return most_occurrences