import patterns

from typing import Any
import os
import json
import logging


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


def display(text, separator='#'):
    print(f'{separator}{text}{separator}')


def format_sized(string_fmt, size):
    return '{' + string_fmt + str(size) + '}'


def display_table(section, keys, table, lines=None, end="\n"):
    header_sep = ' | '
    header_sep_size = len(header_sep)

    headers = header_sep.join(keys)

    # pad left and right with space
    headers = f' {headers}'
    headers = f'{headers} '

    header_size = len(headers)

    if lines is not None:
        # take a copy for changing
        keys, lines = keys.copy(), lines.copy()

        largest_line = len(max(lines)) + 2

        line_separator = '|'
        empty_header = f"{' ' * (largest_line)}" + line_separator

        headers = empty_header + headers
        header_size = len(headers)
        line_fmt = format_sized(':^', largest_line - len(line_separator))

    def fill_line(separator='#'):
        display(f'{separator * header_size}')

    def display_padded(string_fmt, text):
        fmt = format_sized(string_fmt, header_size)
        display(fmt.format(text))

    fill_line()
    display_padded(':^', section)

    fill_line(separator='-')
    display(headers)
    fill_line(separator='-')


    for table_index, items in enumerate(table):
        line = ''
        last_index = len(items) - 1

        for key_index, value in enumerate(items):
            key_size = len(keys[key_index])

            if key_index != last_index: # decrements one time
                 key_size += header_sep_size
            else:
                key_size += 2

            formatted_line = format_sized(':^', key_size).format(value)

            if key_index == 0 and lines is not None:
                new_line = line_fmt.format(lines[table_index])
                formatted_line = ' ' + new_line + line_separator + formatted_line

            line += formatted_line
        display(line)
    fill_line()
    print(end=end)


def get_method_objs() -> dict:
    objs = {}
    for klass in patterns.load_method_classes():
        obj = klass()
        objs[obj.name] = obj
    return objs


def parse_output_name(dataset: dict, preffix: Any):
    if 'pattern' not in dataset:
        return
    name, ext = os.path.splitext(os.path.basename(dataset['pattern']['output']))
    target_name = os.path.join(os.path.dirname(dataset['pattern']['output']), name)
    return f'{target_name}-{preffix}{ext}'


def retrieve_pattern_method(method: str) -> patterns.base.BaseMethod:
    ''' Get a pattern method from available methods '''

    available_methods = get_method_objs()

    if not method in available_methods.keys():
        raise TypeError(f'Unknow pattern method "{method}".')

    return available_methods[method].__class__


def show_available_methods() -> None:
    for objs in get_method_objs().values():
        print(f' * {objs.name}:\n{objs.description}\n')