from .most_common_color import MostCommonColor
from .most_occurrent_color import MostOccurentColor
from .features_extractor import FeaturesExtractor


def load_method_classes():
    '''Entry point function to register a new method'''

    return [
        MostCommonColor,
        MostOccurentColor,
        FeaturesExtractor
    ]
