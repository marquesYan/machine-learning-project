#-*- coding: utf-8 -*-

'''
Apply supervisioned ML classification algorithms.
'''

from utils import (
    parse_config, 
    setup_logging,
    display_table,
    retrieve_pattern_method
)
from patterns.features_extractor import FeaturesExtractor
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix
import cv2
import pandas

from datetime import datetime
import argparse
import logging


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', 
                        '--config', 
                        help='Configuration file', 
                        default='ml.json',
                        required=True)
    parser.add_argument('-v', 
                        '--verbose', 
                        help='Be louder', 
                        action='store_true',
                        default=False)
    parser.add_argument('--max-workers', 
                        help='Set the number of workers for feature extraction',
                        type=int)
    parser.add_argument('-p', 
                        '--predict', 
                        help='Predict this image',
                        type=argparse.FileType('r'))
    parser.add_argument('-m', 
                        '--confusion-matrix', 
                        action='store_true',
                        help='Show the confusion matrix')
    parser.add_argument('target_dataset', 
                        help='Specify the file containing traning data.',
                        type=argparse.FileType('r'))
    return parser.parse_args()


def load_classifiers() -> dict:
    return {
        'gnb': GaussianNB,
        'dtc': DecisionTreeClassifier,
        'mlp': MLPClassifier,
    }


def get_classifier(config: dict) -> object:
    return load_classifiers()[config['classifier']]


def train(classifier: object, 
          train_dataset: str, 
          print_confusion_matrix: bool = False,
          **kwargs) -> GaussianNB:
    X, y = load_simpsons_dataset(train_dataset)

    logging.info('starting training...')
    gnb = classifier(**kwargs).fit(X, y)

    if print_confusion_matrix:
        labels = gnb.classes_
        logging.debug('building confusion matrix from trained unit')
        confusion_mat = confusion_matrix(y_true=y, 
                                        y_pred=gnb.predict(X), 
                                        labels=labels)
        matrix = []
        for index, label in enumerate(labels):
            label_matrix = [str(num) for num in confusion_mat[index]] 
            matrix.append([label] + label_matrix)

        headers = ['Label', *[str(i) for i in range(len(labels))]]
        display_table('Confusion Matrix', headers, matrix)
    return gnb


def load_simpsons_dataset(target_file: str) -> None:
    logging.debug('loading simpson\'s dataset from file...')
    csv_data = pandas.read_csv(target_file)
    X = csv_data.iloc[:, 1:].values
    y = csv_data.iloc[:, 0].values
    return X, y


def predict_character(config: dict, 
                      trained_classfier: object, 
                      image_path: str,
                      **executor_kwargs) -> None:
    logging.info('starting feature extraction...')

    extract_cfg = config['method_options']
    # avoid writing changes to disk
    extract_cfg['feature']['format'] = 'null' 

    method_factory = retrieve_pattern_method(config['method'])
    extractor = method_factory(config=extract_cfg)
    extractor.init(config['datasets'])

    logging.debug('started extraction')
    dataset = {'feature': {'executor_kwargs': executor_kwargs}}

    if config.get('worker') == 'raw':
        features = extractor.run(dataset, image_path)
    else:
        features = extractor.run(cv2.imread(image_path), dataset, None)

    logging.debug('parsing extraction data...')
    
    display_table('Image Extracted Features', 
                  ['Feature', 'Percentage'], 
                  [[feat, format(number, '.2f')]
                   for feat, number in features.items()],)

    X = [list(features.values())]
    prediction = trained_classfier.predict_proba(X)
    matrix = [[trained_classfier.classes_[index], format(proba * 100, '.2f') + '%'] 
              for index, proba in enumerate(prediction[0])]
    display_table('Prediction Probabilities', ['Label', 'Probability'], matrix)


def run(args: argparse.Namespace):
    dataset_path = args.target_dataset.name
    config = parse_config(args.config)

    classifier = get_classifier(config)
    gnb = train(classifier, 
                dataset_path,
                print_confusion_matrix=args.confusion_matrix,
                **config['classifier_kwargs'])

    if args.predict:
        image_path = args.predict.name
        predict_character(config, 
                          gnb, 
                          image_path, 
                          max_workers=args.max_workers)


def main():
    args = parse_args()
    setup_logging(args.verbose)

    start = datetime.now()
    run(args)
    logging.info('time spent: %s', datetime.now() - start)


if __name__ == '__main__':
    main()