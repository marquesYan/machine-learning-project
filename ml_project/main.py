#-*- coding: utf-8 -*-

'''

'''

import patterns
from parallel import background_run, wait_futures
from argparse import ArgumentParser, Namespace
from typing import List, Tuple, Union
from datetime import datetime
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
    parser.add_argument('-l', '--list-methods', help='Lista all available pattern methods.',
                        action='store_true', default=False)

    return parser.parse_args()


def parse_config(path: str):
    ''' Low-level configuration parsing from a file path '''

    with open(path, 'rb') as reader:
        data = json.load(reader)
    
    assert 'method' in data, 'Missing "method" in configuration'
    assert 'datasets' in data, 'Missing "datasets" in configuration'
    assert isinstance(data['datasets'], list), 'Invalid type for "datasets" in configuration'
    for index, dataset in enumerate(data['datasets']):
        assert 'class' in dataset, f'Missing "class" in dataset number #{index}'
        assert 'path' in dataset, f'Missing "path" in dataset number #{index}'
    
    return data


def with_pixels(path: str, dataset: dict, callback: callable) -> None:
    ''' 
    Wrapper function to execute a callback with every image pixel for every call with an image
    '''

    image = cv2.imread(path)

    # get sizes
    height, width, _ = image.shape

    for i in range(height):
        for j in range(width):
            callback(path, dataset, image[i][j])

    # ensure service will count this as success
    return True


def scan_directory(path: str) -> List[str]:
    ''' Get all file paths inside the given directory '''

    paths = []
    with os.scandir(path) as scan:
        for entry in scan:
            paths.append(entry.path)
    return paths  


def service_runner(worker: callable,
                   dataset: dict,
                   dataset_class: str,
                   method: patterns.base.BaseMethod,
                   *args,
                   **executor_kwargs) -> Union[None, Tuple[int, List[str]]]:
    ''' Scan targeted files in directory and try to convert them in parallel '''

    paths = scan_directory(dataset['path'])
    paths = paths[:60]
    if paths:
        callback = method.get_callback(dataset)
        paths_count = len(paths)
        logging.debug('%s files found: %d', dataset_class, paths_count)
        failed_items = wait_futures(worker, 
                                    paths, 
                                    dataset, 
                                    callback, 
                                    *args, 
                                    **executor_kwargs)
        wait_futures(method.save, [dataset])
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


def get_pattern_method_objs() -> dict:
    objs = {}
    for klass in patterns.load_method_classes():
        obj = klass()
        objs[obj.name()] = obj
    return objs 


def retrieve_pattern_method(method: str) -> patterns.base.BaseMethod:
    ''' Get a pattern method from available methods '''

    available_methods = get_pattern_method_objs()

    if not method in available_methods.keys():
        raise TypeError(f'Unknow pattern method "{method}".')

    return available_methods[method].__class__


def create_services(config: dict, method: patterns.base.BaseMethod) -> list:
    ''' Create valid service configuration for running in the background '''

    services = []
    for dataset in config['datasets']:
        services.append(((with_pixels, dataset, dataset['class'], method), 
                        dataset.get('executor_kwargs', {})))
    return services


def display_available_methods() -> None:
    for objs in get_pattern_method_objs().values():
        print(f'{objs.name()}\t\t - {objs.help()}')


def main():
    ''' Main CLI application entry point '''

    args = parse_args()

    setup_logging(args.verbose)

    if args.list_methods:
        display_available_methods()
        return 0

    config = parse_config(args.config)

    # retrieve and instantiate method class
    current_method_class = retrieve_pattern_method(config['method'])
    current_method = current_method_class(config=config.get('method_options', {}))

    services = create_services(config, current_method)

    start = datetime.now()
    background_run(service_runner, services, max_workers=config.get('max_workers'))
    logging.info('time spent: %s', datetime.now() - start)

    return 0



if __name__ == '__main__':
    sys.exit(main())