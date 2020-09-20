#-*- coding: utf-8 -*-

'''

'''

import pattern
from parallel import background_run, wait_futures
from argparse import ArgumentParser, Namespace
from typing import List, Tuple, Union
import logging
import json
import sys
import os

import cv2


def parse_args() -> Namespace:
    ''' Parse command line arguments '''

    parser = ArgumentParser()
    parser.add_argument('-o', '--output-arff', help='Where to send the file in arff format',
                        default=sys.stdout)
    parser.add_argument('-c', '--config', help='Configuration file', default='ml.json')
    parser.add_argument('-v', '--verbose', help='Be louder', action='store_true', default=False)
    parser.add_argument('-w', '--max-workers', help='How many workers to run on each dataset thread', type=int)
    parser.add_argument('-m', '--method', help='Specify which pattern method', required=True)
    return parser.parse_args()


def parse_config(path: str):
    ''' Low-level configuration parsing from a file path '''

    with open(path, 'rb') as reader:
        data = json.load(reader)
    
    assert 'datasets' in data, 'Missing "datasets" in configuration'
    assert isinstance(data['datasets'], list), 'Invalid type for "datasets" in configuration'
    for index, dataset in enumerate(data['datasets']):
        assert 'class' in dataset, f'Missing "class" in dataset number #{index}'
        assert 'path' in dataset, f'Missing "path" in dataset number #{index}'
    
    return data


def with_pixels(callback: callable) -> None:
    ''' 
    Wrapper function to execute a callback with every image pixel for every call with an image
    '''

    def wrapper(path: str) -> None:
        image = cv2.imread(path)

        # get sizes
        height, width, _ = image.shape

        for i in range(height):
            for j in range(width):
                callback(path, image[i][j])

        # ensure service will count this as success
        return True
    return wrapper


def scan_directory(path: str) -> List[str]:
    ''' Get all file paths inside the given directory '''

    paths = []
    with os.scandir(path) as scan:
        for entry in scan:
            paths.append(entry.path)
    return paths  


def service_runner(worker: callable,
                   directory: str,
                   name: str,
                   **executor_kwargs) -> Union[None, Tuple[int, List[str]]]:
    ''' Scan targeted files in directory and try to convert them in parallel '''

    paths = scan_directory(directory)
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


def retrieve_pattern_method(method: str) -> pattern.BaseMethod:
    ''' Get a pattern method from available methods '''

    available_methods = {obj.name(): obj for obj in pattern.load_methods()}

    if not method in available_methods.keys():
        raise TypeError(f'Unknow pattern method "{method}".')

    return available_methods[method]


def create_services(config: dict, method: pattern.BaseMethod) -> list:
    ''' Create valid service configuration for running in the background '''

    services = []
    for dataset in config['datasets']:
        callback = method.get_callback(dataset)
        worker = with_pixels(callback)
        services.append(((worker, dataset['path'], dataset['class']), 
                        dataset.get('executor_kwargs', {})))
    return services


def main():
    ''' Main CLI application entry point '''

    args = parse_args()

    setup_logging(args.verbose)

    config = parse_config(args.config)

    current_method = retrieve_pattern_method(args.method)

    services = create_services(config, current_method)

    background_run(service_runner, services, max_workers=args.max_workers)
    
    list(map(current_method.save, config['datasets']))



if __name__ == '__main__':
    main()