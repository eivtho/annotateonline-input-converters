import sys
import os
from argparse import ArgumentParser
import glob
import shutil
import json
import logging

import numpy as np

from sa_coco_converters.converters import Converter

ALLOWED_TASK_TYPES = [
    'panoptic_segmentation', 'instance_segmentation', 'keypoint_detection'
]
ALLOWED_PROJECT_TYPES = ['pixel', 'vector']
ALLOWED_CONVERSIONS = [
    ('pixel', 'panoptic_segmentation'), ('pixel', 'instance_segmentation'),
    ('vector', 'instance_segmentation'), ('vector', 'keypoint_detection')
]


def passes_sanity_checks(args):

    if args.train_val_split_ratio < 0 or args.train_val_split_ratio > 100:
        logging.error(
            "The split percentage should be in range (0,100), a number x will mean\
        to put x percent of input images in train set, and the rest in validation set"
        )
        return False
    if args.project_type not in ALLOWED_PROJECT_TYPES:
        logging.error('Please enter valid project type: pixel or vector')
        return False
    if args.task not in ALLOWED_TASK_TYPES:
        logging.error(
            'Please enter valid task: instance_segmentation, panoptic_segmentation, keypoint_detection'
        )
        return False
    tp = (args.project_type, args.task)
    if tp not in ALLOWED_CONVERSIONS:
        logging.error(
            'Converting from project type {} to coco format for the task {} is not supported'
            .format(args.project_type, args.task)
        )
        return False
    return True


def parse_args():
    argument_parser = ArgumentParser()

    argument_parser.add_argument(
        '-is',
        '--input_images_source',
        help="The folder where images and thei \
                                    corresponding annotation json files are located",
        type=str
    )

    argument_parser.add_argument(
        '-sr',
        '--train_val_split_ratio',
        help="What percentage of input images should be in train set",
        type=int
    )

    argument_parser.add_argument(
        '-ptype',
        '--project_type',
        help="The type of the annotate.online project can be vector or pixel",
        type=str
    )

    argument_parser.add_argument(
        '-t',
        '--task',
        help=
        "The output format of the converted file, this corresponds to one of 5 coco tasks",
        type=str
    )

    argument_parser.add_argument(
        '-dn', '--dataset_name', help="The name of the dataset", type=str
    )

    argument_parser.add_argument(
        '-od',
        '--output_dir',
        help="The output folder for the coco json files test/train images",
        type=str
    )

    argument_parser.add_argument(
        '-cp',
        '--copyQ',
        help=
        "Move or copy source images to corresponding test and train folders",
        type=bool
    )

    args = argument_parser.parse_args()
    return args


def load_files(path_to_imgs, ratio, task):
    suffix = None
    rm_len = None
    if args.project_type == 'pixel':
        suffix = '___pixel.json'
    else:
        suffix = '___objects.json'

    rm_len = len('___lores.jpg')

    all_files = None
    if task == 'keypoint_detection':
        all_files = np.array(
            [
                (fname, fname[:-rm_len] + suffix)
                for fname in glob.glob(os.path.join(path_to_imgs, '*.jpg'))
            ]
        )
    else:
        all_files = np.array(
            [
                (
                    fname, fname[:-rm_len] + suffix,
                    fname[:-rm_len] + '___save.png'
                ) for fname in glob.glob(os.path.join(path_to_imgs, '*.jpg'))
            ]
        )
    num_train_vals = int(len(all_files) * (ratio / 100))

    num_test_vals = len(all_files) - num_train_vals

    train_indices = set(
        np.random.choice(range(len(all_files)), num_train_vals, replace=False)
    )

    all_indices = set(range(len(all_files)))

    test_indices = all_indices.difference(train_indices)
    test_set = all_files[np.array(list(test_indices))]
    train_set = all_files[np.array(list(train_indices))]

    return (train_set, test_set)


def move_files(train_set, test_set, src, cp):

    train_path = os.path.join(src, 'train_set')
    test_path = os.path.join(src, 'test_set')

    move_fn = None

    if cp:
        move_fn = shutil.copy
        logging.warning(
            'Source image files will be copied to output_dir/test and output_dir/train folders'
        )
    else:
        move_fn = shutil.move
        logging.warning(
            'Source image files will be moved to output_dir/test and output_dir/train folders'
        )

    for tup in train_set:
        for i in tup:
            move_fn(i, os.path.join(train_path, i.split('/')[-1]))

    for tup in test_set:
        for i in tup:
            move_fn(i, os.path.join(test_path, i.split('/')[-1]))


def create_classes_mapper(imgs, classes_json):
    classes = {}

    j_data = json.load(open(classes_json))
    for instance in j_data:
        if 'classId' not in instance:
            continue
        classes[instance['className']] = instance['classId']

    with open(os.path.join(imgs, 'test_set', 'classes_mapper.json'), 'w') as fp:
        json.dump(classes, fp)

    with open(
        os.path.join(imgs, 'train_set', 'classes_mapper.json'), 'w'
    ) as fp:
        json.dump(classes, fp)


if __name__ == '__main__':
    args = parse_args()

    if not passes_sanity_checks(args):
        sys.exit()

    try:
        os.makedirs(os.path.join(args.output_dir, 'train_set'))
        os.makedirs(os.path.join(args.output_dir, 'test_set'))
    except Exception as e:
        logging.error(
            'Could not make test and train set paths, check if they already exist'
        )
        sys.exit()

    if args.task == 'instance_segmentation' or args.task == 'panoptic_segmentation':
        create_classes_mapper(
            args.output_dir,
            os.path.join(args.input_images_source, 'classes.json')
        )

    train_set, test_set = load_files(
        args.input_images_source, args.train_val_split_ratio, args.task
    )
    move_files(train_set, test_set, args.output_dir, args.copyQ)
    converter = Converter(
        args.project_type, args.task, args.dataset_name,
        os.path.join(args.output_dir, 'train_set'), args.output_dir
    )

    converter.strategy.set_dataset_name(args.dataset_name + '_train')

    try:
        converter.convert_from_sa()
    except Exception as e:
        logging.error('Something went wrong while converting train set')
        logging.error(e)
        sys.exit()

    converter.strategy.set_dataset_name(args.dataset_name + '_test')
    converter.strategy.set_export_root(
        os.path.join(args.output_dir, 'test_set')
    )
    try:
        converter.convert_from_sa()
    except Exception as e:
        logging.error(
            'Something went wrong while converting the validation set'
        )
        logging.error(e)
        sys.exit()
