import os
import cv2
import json
import argparse
import xmltodict
import numpy as np


# Defines parser for cmd arguments
def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pvoc-dir",
        type=str,
        required=True,
        help="Path of the directory, which contains all output data of Pascal VOC"
    )
    parser.add_argument(
        '-fd',
        action='store_true',
        help="Set if you want to convert from VOC's detection format"
    )

    parser.add_argument(
        '-fs',
        action='store_true',
        help="Set if you want to convert from VOC's segmentation format"
    )

    return parser


# Generates polygons for each instance
def generate_polygons(png_file):
    segmentation = []

    img = cv2.imread(png_file, cv2.IMREAD_GRAYSCALE)
    img_unique_colors = np.unique(img)

    for unique_color in img_unique_colors:
        if unique_color == 0 or unique_color == 220:
            continue
        else:
            mask = np.zeros_like(img)
            mask[img == unique_color] = 255
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                contour = contour.flatten().tolist()
                if len(contour) > 4:
                    segmentation.append((contour, unique_color))
                if len(segmentation) == 0:
                    continue
    return segmentation


# Converts VOC detection format to annotate.online's vector format
def from_voc_detection():

    classes = set()

    for xml_file in os.listdir(os.path.join(pvoc_folder, 'Annotations')):
        voc_dict = xmltodict.parse(
            open(os.path.join(pvoc_folder, 'Annotations', xml_file)).read()
        )
        obj_list = []
        if not isinstance(voc_dict['annotation']['object'], list):
            obj_list.append(voc_dict['annotation']['object'])
            voc_dict['annotation']['object'] = obj_list

        if isinstance(voc_dict['annotation']['object'], list):
            for obj in voc_dict['annotation']['object']:
                classes.add(obj['name'])
        else:
            classes.add(voc_dict['annotation']['object']['name'])

        sa_loader = []
        for obj in voc_dict['annotation']['object']:
            sa_bbox = {
                'type': 'bbox',
                'points':
                    {
                        'x1': obj['bndbox']['xmin'],
                        'y1': obj['bndbox']['ymin'],
                        'x2': obj['bndbox']['xmax'],
                        'y2': obj['bndbox']['ymax']
                    },
                'className': obj['name'],
                'classId': -1 * (list(classes).index(obj['name']) + 1),
                'attributes': [],
                'probability': 100,
                'locked': False,
                'visible': True,
                'groupId': 0
            }

            if 'actions' in obj.keys():
                for act_key, act_value in obj['actions'].items():
                    sa_bbox['attributes'].append(
                        {
                            'id': -1,
                            'groupId': -2,
                            act_key: act_value
                        }
                    )

            for key, value in obj.items():
                if key not in ['name', 'bndbox', 'point', 'actions']:
                    sa_bbox['attributes'].append(
                        {
                            'id': -1,
                            'groupId': -2,
                            key: value
                        }
                    )

            sa_loader.append(sa_bbox)

        with open(
            os.path.join(
                sa_folder,
                voc_dict['annotation']['filename'] + "___objects.json"
            ), "w"
        ) as new_json:
            json.dump(sa_loader, new_json, indent=2)


# Converts VOC segmentation format to annotate.online's vector format
def from_voc_segmentation():
    classes = set()
    sa_loader = []
    bad_annotations = set()

    for file in os.listdir(os.path.join(pvoc_folder, 'SegmentationClass')):
        voc_class = generate_polygons(
            os.path.join(os.path.join(pvoc_folder, 'SegmentationClass'), file)
        )
        for segment, color in voc_class:
            classes.add(color)

    for root, dirs, files in os.walk(pvoc_folder, topdown=True):
        for file_name in files:

            original_file_name = ''

            if file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
                original_file_name = file_name

            if 'SegmentationObject' in root:
                voc_masks = generate_polygons(os.path.join(root, file_name))
                voc_class_masks = generate_polygons(
                    os.path.join(
                        root.replace('SegmentationObject', 'SegmentationClass'),
                        file_name
                    )
                )

                for i, j in enumerate(voc_masks):
                    sa_polygon = {
                        'type': 'polygon',
                        'points': j[0],
                        'className': '',
                        'classId': 111,
                        'attributes': [],
                        'probability': 100,
                        'locked': False,
                        'visible': True,
                        'groupId': 0,
                        'imageId': file_name.split('.')[0]
                    }
                    if len(voc_masks) != len(
                        voc_class_masks
                    ):  # this statement for merged classes
                        bad_annotations.add(file_name)
                        continue
                    else:
                        if voc_class_masks[i][0] == j[0] and voc_class_masks[i][
                            1] in classes:
                            sa_polygon['classId'] = -1 * (
                                list(classes).index(voc_class_masks[i][1]) + 1
                            )
                        else:
                            bad_annotations.add(file_name)

                    sa_loader.append(sa_polygon)

            f_loader = []
            for data in sa_loader:
                if data['imageId'] == original_file_name.split('.')[0]:
                    f_loader.append(data)
                    with open(
                        os.path.join(
                            sa_folder, original_file_name + "___objects.json"
                        ), "w"
                    ) as new_json:
                        json.dump(f_loader, new_json, indent=2)

    print(f'List of bad annotated files = {bad_annotations}')


if __name__ == "__main__":
    p = get_parser().parse_args()

    pvoc_folder = p.pvoc_dir
    from_detection = p.fd
    from_segmentation = p.fs

    if from_detection:
        sa_folder = os.path.abspath(pvoc_folder) + "__converted_from_detection"
        os.makedirs(sa_folder, exist_ok=True)

        from_voc_detection()

    elif from_segmentation:
        sa_folder = os.path.abspath(
            pvoc_folder
        ) + "__converted_from_segmentation"
        os.makedirs(sa_folder, exist_ok=True)

        from_voc_segmentation()
