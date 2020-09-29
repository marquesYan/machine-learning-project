from typing import Union, Any, List, Callable, Generator
import os


def rgb2hex(red, green, blue):
    # see https://www.codespeedy.com/convert-rgb-to-hex-color-code-in-python/
    return '0x%02x%02x%02x' % (red, green, blue)


def image2hex(image) -> List[str]:
    return map_image_pixels(image, function=lambda _,__,px: rgb2hex(*px))


def map_image_pixels(image, 
                     function: Callable[[int, int, int, int, int], Any] = None) -> Generator:
    if function is None:
        function = lambda *args: [*args]
    # get sizes
    height, width, _ = image.shape
    for i in range(height):
        for j in range(width):
            rgb = image[i][j]
            yield function(i, j, rgb)
