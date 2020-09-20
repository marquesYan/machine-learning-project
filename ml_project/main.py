# coding: utf-8

from parallel import background_run, wait_futures
from argparse import ArgumentParser, Namespace
from collections import Counter
from typing import List, Tuple, Union
import logging
import json
import sys
import os

import cv2


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument('-o', '--output-arff', help='Where to send the file in arff format',
                        default=sys.stdout)
    parser.add_argument('-c', '--config', help='Configuration file', default='ml.json')
    parser.add_argument('-v', '--verbose', help='Be louder', action='store_true', default=False)
    return parser.parse_args()


def parse_config(path: str):
    with open(path, 'rb') as reader:
        data = json.load(reader)
    
    assert 'datasets' in data, 'Missing "datasets" in configuration'
    assert isinstance(data['datasets'], list), 'Invalid type for "datasets" in configuration'
    for index, dataset in enumerate(data['datasets']):
        assert 'class' in dataset, f'Missing "class" in dataset number #{index}'
        assert 'path' in dataset, f'Missing "path" in dataset number #{index}'
    
    return data


def with_pixels(callback: callable) -> None:
    '''Wrapper function to execute a callback with every image pixel for every call with an image.'''

    def wrapper(path: str) -> None:
        image = cv2.imread(path)

        # get sizes
        height, width, _ = image.shape

        for i in range(height):
            for j in range(width):
                callback(image[i][j])

        # ensure service will count this as success
        return True
    return wrapper


def scan_directory(path: str) -> List[str]:
    '''Get all file paths inside the given directory'''

    paths = []
    with os.scandir(path) as scan:
        for entry in scan:
            paths.append(entry.path)
    return paths


def with_color_pattern_counter() -> Tuple[Counter, callable]:
    '''Helper wrapper to count color patterns.'''

    color_counter = Counter()
    def wrapper(rgb: list) -> None:
        # convert rgb into hex
        hex_format = rgb2hex(*rgb)

        # increment this hex color
        color_counter.update({hex_format: 1})

    return color_counter, wrapper


def rgb2hex(red, blue, green):
    # see https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    return '0x%02x%02x%02x' % (red, blue, green)  


def service_runner(worker: callable,
                   directory: str,
                   name: str,
                   **executor_kwargs) -> Union[None, Tuple[int, List[str]]]:
    ''' Scan targeted files in directory and try to convert them in parallel '''

    paths = scan_directory(directory)
    paths = paths[:1]
    if paths:
        paths_count = len(paths)
        logging.debug('%s files found: %d', name, paths_count)
        failed_items = wait_futures(worker, paths, **executor_kwargs)
        return (paths_count, failed_items)
    return None



def setup_logging(verbose: bool) -> None:
    ''' Basic configuration of logging facility '''

    log_format = ['%(asctime)s', '-', '[%(levelname)s]', '%(message)s']
    if verbose:
        log_format.insert(1, '%(funcName)s')
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(format=' '.join(log_format), level=level)
    logging.getLogger(__file__)


def save_patterns(counters: List[Counter], datasets: list) -> None:
    for dataset in datasets:
        name = dataset['class']
        patterns = counters[name].most_common(dataset['pattern'].get('max_commons', 35))
        template_patterns = {color: count for color, count in patterns}

        try:
            with open(dataset['pattern']['output'], 'w') as writer:
                json.dump(template_patterns, writer, indent=4)
            logging.info(f'patterns of {name} was saved sucessfully!')
        except Exception as exc:
            logging.error(str(exc), exc)


def main():
    args = parse_args()

    setup_logging(args.verbose)

    config = parse_config(args.config)

    services, counters =  [], {}

    for dataset in config['datasets']:
        main_counter, pattern_wrapper = with_color_pattern_counter()
        main_worker = with_pixels(pattern_wrapper)

        services.append(((main_worker, dataset['path'], dataset['class']), 
                        dataset.get('executor_kwargs', {})))
        counters[dataset['class']] = main_counter

    background_run(service_runner, services, max_workers=2)
    
    save_patterns(counters, config['datasets'])



if __name__ == '__main__':
    main()