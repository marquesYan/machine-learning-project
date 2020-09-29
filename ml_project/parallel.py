#-*- coding: utf-8 -*-

'''

This module exposes functions for running several services in the background.
They all reside in the ThreadPoolExecutor implementation.

'''

from concurrent import futures
from typing import List
import logging


def background_run(runner: callable, 
                   services: list,
                   impl: futures.Executor = None,
                   max_workers: int = None) -> None:
    ''' Execute services in parallel '''

    if not services:
        logging.info('any available service to run in background, aborting...')
        return

    impl = impl or futures.ProcessPoolExecutor

    # by default, allocate 1 process for each service
    if max_workers is None:
        max_workers = len(services)

    logging.debug('starting background run for services: %s', services)

    with impl(max_workers=max_workers) as executor:
        future_to_service = {executor.submit(runner, *args, **kwargs): args[2]
                             for args, kwargs in services}
        display_service_futures(future_to_service)


def handle_futures(future_to_service: dict) -> None:
    ''' Helper function for waiting future results '''

    for future in futures.as_completed(future_to_service):
        stopped_service = future_to_service[future]
        result, error = None, None
        try:
            result = future.result()
        except Exception as exception:  # pylint: disable=broad-except
            error = exception
        yield (stopped_service, result, error)


def wait_futures(worker: callable,
                 services: list,
                 *args,
                 show_status: bool = True,
                 mask_result: bool = False,
                 impl: futures.Executor = None,
                 **executor_kwargs) -> List[str]:
    ''' Manage parallel tasks with nice logging '''

    impl = impl or futures.ProcessPoolExecutor

    index, faileds, results = 0, [], []
    if show_status:
        services_count = len(services)
    with impl(**executor_kwargs) as executor:
        future_to_service = {executor.submit(worker, service, *args): service
                             for service in services}
        for service, result, error in handle_futures(future_to_service):
            if error:
                logging.error('%s exited with: %s', service, error)
            elif not mask_result:
                logging.debug('%s resulted in: %s', service, result)

            results.append(result)
            success = result is not None
            if not success:
                faileds.append(service)

            index += 1

            if show_status:
                logging.info('fineshed: %s success: %s status: %s',
                            service,
                            success,
                            f'{index}/{services_count}')
    return faileds, results


def display_status(name: str, total: int, items_failed: list) -> None:
    ''' Helper function to display a nice overview about execution facts '''

    failure = len(items_failed)
    succeeded = total - failure
    proportion_of_success = (succeeded * 100) / total
    if failure:
        log_list(f'some items for {name} service have failed:', items_failed)
    logging.info('%s conversion done. succeeded: %d failure: %d ratio: %d%%',
                 name,
                 succeeded,
                 failure,
                 proportion_of_success)

            
def log_list(header: str, content: list) -> None:
    ''' Helper function for logging a list '''

    placeholder = [' - %s' for _ in content]
    logging.warning('\n'.join([header] + placeholder), *content)


def display_service_futures(future_to_service: dict):
    ''' Helper function to display fineshed services '''

    for service, result, error in handle_futures(future_to_service):
        if error:
            logging.error('%s service exited with: %s', service, error)
        elif result:
            display_status(service, *result)
        else:
            logging.info('no %s files found', service)

        logging.info('service fineshed: %s', service)
