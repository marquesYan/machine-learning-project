from dataclasses import dataclass, field
from typing import Union, Any, List
import multiprocessing
import datetime
import logging
import json


def rgb2hex(red, green, blue):
    # see https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    return '0x%02x%02x%02x' % (red, green, blue)


def image2hex(image) -> List[str]:
    # get sizes
    height, width, _ = image.shape
    for i in range(height):
        for j in range(width):
            rgb = image[i][j]
            yield rgb2hex(*rgb)


@dataclass
class TemporaryObject:
    target_path: str
    key: str
    objects: Any
    last_access: datetime.timedelta = field(default_factory=datetime.datetime.now)


class FlushOnDemand:
    _lock = multiprocessing.RLock()

    def __init__(self, max_idle_time: int, max_interval_time: int):
        self.time_limit = datetime.timedelta(seconds=max_idle_time)

        self._objects = {}

        self._interval_limit = datetime.timedelta(seconds=max_interval_time)
        self._last_flush = datetime.datetime.now()

    def update(self, tmpobj: TemporaryObject) -> None:
        logging.debug('flushed count on "update": %d', self.flush())
        self._objects[tmpobj.key] = tmpobj

    def has(self, key: str) -> bool:
        return key in self._objects

    def get(self, key: str, default: Any = None) -> Union[None, TemporaryObject]:
        result_obj = self._objects.get(key, default)

        # maybe update object access time
        if result_obj is not None:
            result_obj.last_access = datetime.datetime.now()

        flush_count = self.flush()
        if flush_count:
            logging.debug('flushed count on "get": %d', flush_count)
        return result_obj

    def flush(self) -> int:
        now = datetime.datetime.now()

        if now - self._last_flush < self._interval_limit:
            return 0

        with self._lock:
            objs_leaving = (tmpobj for tmpobj in self._objects.values()
                            if now - tmpobj.last_access > self.time_limit)
            return self._flush_these(objs_leaving)
                
    def flush_all(self) -> int:
        with self._lock:
            return self._flush_these(self._objects.values())

    def _flush_these(self, objs_leaving: List[TemporaryObject]) -> int:
        return self._low_flush_objs(objs_leaving)

    def _low_flush_objs(self, objs_leaving: List[TemporaryObject]) -> int:
        keys_gone = []
        
        for tmpobj in objs_leaving:
            content = tmpobj.objects

            # workaround to dump set as a list
            if isinstance(content, set):
                content = list(content)

            with open(tmpobj.target_path, 'w') as writer:
                json.dump(content, writer)

            keys_gone.append(tmpobj.key)
        # logging.debug('keys: %d', len(keys_gone))
        # free memory space
        for key in keys_gone:
            try:
                del self._objects[key]
                logging.debug('just flushed object key [%s]', tmpobj.key)
            except KeyError:
                logging.debug('object already flushed key [%s]', tmpobj.key)

        self._last_flush = datetime.datetime.now()
        return len(keys_gone)
