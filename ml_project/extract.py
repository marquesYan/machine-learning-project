#-*- coding: utf-8 -*-

'''

'''

from utils import (
    parse_config, 
    setup_logging,
    parse_output_name, 
    retrieve_pattern_method,
    show_available_methods,
)
from parallel import background_run, wait_futures
from patterns.base import BaseMethod
import cv2

from argparse import ArgumentParser, Namespace
from typing import List, Tuple, Union, Callable, Any
from datetime import datetime
import logging
import json
import sys
import os


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


def with_image(path: str, dataset: dict, callback: Callable[[object, dict, str], Any]) -> None:
    ''' 
    Wrapper function to execute a service callback with a loaded opencv image. 
    '''

    image = cv2.imread(path)

    return callback(image, dataset, path)


def raw_handler(path: str, dataset: dict, callback: Callable[[dict, str], Any]):
    return callback(dataset, path)


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
                   method: BaseMethod,
                   paths: list,
                   current_loop: int,
                   *args,
                   impl=None,
                   **executor_kwargs) -> Union[None, Tuple[int, List[str]]]:
    ''' Scan targeted files in directory and try to convert them in parallel '''

    paths_count = len(paths)
    logging.debug('%s files found: %d', dataset_class, paths_count)
    failed_items, results = wait_futures(worker, 
                                        paths, 
                                        dataset, 
                                        method.run, 
                                        mask_result=True,
                                        impl=impl,
                                        *args,
                                        **executor_kwargs,)

    # save pattern result
    save_pattern_method(dataset, method, results, current_loop)

    return (paths_count, failed_items)


def create_service(config: dict, dataset: dict, *args, **kwargs) -> list:
    ''' Create valid service configuration for running in the background '''

    if config.get('worker') == 'raw':
        worker = raw_handler
    else:
        worker = with_image

    args = (worker, dataset, dataset['class'], *args)
    kwargs.update(**dataset.get('executor_kwargs', {}))
    return ((args), kwargs)


def save_pattern_method(dataset: dict, 
                        method: BaseMethod, 
                        results: list,
                        index: int) -> None:
    target_name = parse_output_name(dataset, index)
    method.save(target_name, results, dataset)
    logging.info(f'patterns of {dataset["class"]} was saved sucessfully!')


def run(config: dict) -> None:
    dataset_paths, splitted_datasets = {}, {}

    for dataset in config['datasets']:
        paths = scan_directory(dataset['path'])
        if dataset.get('only'):
            paths = paths[:dataset.get('only')]
        dataset_paths[dataset['class']] = paths

    method_factory = retrieve_pattern_method(config['method'])
    method = method_factory(config=config.get('method_options', {}))
    method.init(config['datasets'])

    global_index = 1

    while True:
        services = []
        for dataset in config['datasets']:
            all_paths = dataset_paths[dataset['class']]
            step = dataset.get('step') or len(all_paths)

            paths = all_paths[:step]

            # ensure paths are upated
            dataset_paths[dataset['class']] = all_paths[step:]

            # is dataset being split
            if len(dataset_paths[dataset['class']]) > 0:
                if dataset['class'] not in splitted_datasets:
                    splitted_datasets[dataset['class']] = [dataset, 0]

                # count how many splits
                splitted_datasets[dataset['class']][1] += 1

            if paths:
                logging.info('remaining paths for [%s]: %d', 
                             dataset['class'], 
                             len(dataset_paths[dataset['class']]))
                service = create_service(config, 
                                         dataset, 
                                         method,
                                         paths, 
                                         global_index,
                                         impl=method.options.get('service_impl'))
                services.append(service)

        # are we done?
        if not services:
            break

        background_run(service_runner, 
                       services,
                       max_workers=config.get('max_workers'),
                       impl=method.options.get('background_impl'))

        global_index += 1

    if not method.options.get('ignore_split', False):
        finish_splitted_datasets(method, splitted_datasets)


def finish_splitted_datasets(method: BaseMethod, 
                             splitted_datasets: dict) -> None:
    for dataset, count in splitted_datasets.values():
        logging.debug('recovering split stats for dataset: %s', dataset['class'])
        all_stats = []
        for index in range(1, count):
            target_name = parse_output_name(dataset, index)
            logging.debug('start reading stat: %s', target_name)
            with open(target_name, 'r') as reader:
                stats = json.load(reader)
            all_stats.append(stats)
            os.unlink(target_name)
        all_stats = [list(stats) for stats in all_stats]
        save_pattern_method(dataset, method, all_stats, 'summarized')


def main():
    ''' Main CLI application entry point '''

    args = parse_args()

    setup_logging(args.verbose)

    if args.list_methods:
        show_available_methods()
        return 0

    config = parse_config(args.config)

    start = datetime.now()
    run(config)
    logging.info('time spent: %s', datetime.now() - start)

    return 0


if __name__ == '__main__':
    sys.exit(main())