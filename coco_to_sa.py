import argparse
import os
import json
import requests
import randomcolor
import cv2
import extcolors

from collections import defaultdict
from pycocotools.coco import COCO
from imantics import Polygons, Mask

parser = argparse.ArgumentParser()
parser.add_argument("--coco-json", type=str, required=True, help="Argument must be JSON file")
p = parser.parse_args()

coco_json = p.coco_json
coco_json_folder, coco_json_file = os.path.split(coco_json)

main_dir = os.path.join(os.path.abspath(coco_json) + "__formated")
if not os.path.exists(main_dir):
    os.mkdir(main_dir)

classes_dir = os.path.join(main_dir, "classes")
if not os.path.exists(classes_dir):
    os.mkdir(classes_dir)

json_data = json.load(open(os.path.join(coco_json_folder, coco_json_file)))

classes_loader = []
def_dict = defaultdict(list)


# Downloads images from COCO website
def image_downloader(url):
    file_name_start_pos = url.rfind("/") + 1
    file_name = url[file_name_start_pos:]
    print("downloading: ", url)
    r = requests.get(url, stream=True)
    with open(os.path.join(main_dir, file_name), 'wb') as f:
        f.write(r.content)


# Generates colors in range(n)
def color_generator(n):
    rand_color = randomcolor.RandomColor()
    return rand_color.generate(count=n)


# Generates colors in range(n)
def blue_color_generator(n):
    rand_color = randomcolor.RandomColor()
    return rand_color.generate(hue="blue", count=n)


# Converts RLE format to polygon segmentation for object detection and keypoints
def rle_to_polygon(annotation):
    coco = COCO(coco_json)
    polygons = Mask(coco.annToMask(annotation)).polygons()
    return polygons.segmentation


# Merges tuples by first key
def merge_tuples(list_of_tuples):
    mergeddict = defaultdict(list)
    for group in list_of_tuples:
        mergeddict[group[:-1]].append(group[-1])
    return [(k + (tuple(v),) if len(v) > 1 else k + tuple(v)) for k, v in mergeddict.items()]


# Returns unique values of list. Values can be dicts or lists!
def dict_setter(list_of_dicts):
    return [j for n, j in enumerate(list_of_dicts) if j not in list_of_dicts[n + 1:]]


# image getter
def get_image(image_path):
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image


"""download images"""
for i in range(len(json_data['images'])):
    image_downloader(json_data['images'][i]['coco_url'])


"""classes"""
for c in range(len(json_data['categories'])):
    colors = color_generator(len(json_data['categories']))
    for class_color in colors:
        classes_dict = {'name': json_data['categories'][c]['name'], 'id': json_data['categories'][c]['id'],
                        'color': colors[c], 'attribute_groups': []}
        classes_loader.append(classes_dict)
res_list = [i for n, i in enumerate(classes_loader) if i not in classes_loader[n + 1:]]
with open(os.path.join(classes_dir, "classes.json"), "w") as classes_json:
    json.dump(res_list, classes_json, indent=2)


""" instances """
if str(coco_json_file).__contains__('instances'):

    loader = []
    for annot in json_data['annotations']:
        for cat in json_data['categories']:
            if annot['iscrowd'] == 1:
                annot['segmentation'] = rle_to_polygon(annot)
            if cat['id'] == annot['category_id']:
                sa_dict_bbox = {'type': 'bbox',
                                'points': {'x1': annot['bbox'][0], 'y1': annot['bbox'][1],
                                           'x2': annot['bbox'][0] + annot['bbox'][2],
                                           'y2': annot['bbox'][1] + annot['bbox'][3]}, 'className': cat['name'],
                                'classId': cat['id'],
                                'attributes': [], 'probability': 100, 'locked': False, 'visible': True,
                                'groupId': annot['id'], 'imageId': annot['image_id']}

                sa_polygon_loader = [
                    {'type': 'polygon', 'points': annot['segmentation'][p], 'className': cat['name'],
                     'classId': cat['id'],
                     'attributes': [], 'probability': 100, 'locked': False, 'visible': True,
                     'groupId': annot['id'], 'imageId': annot['image_id']}
                    for p in range(len(annot['segmentation']))]

                for img in json_data['images']:
                    for polygon in sa_polygon_loader:
                        if polygon['imageId'] == img['id']:
                            loader.append((img['id'], polygon))
                        if sa_dict_bbox['imageId'] == img['id']:
                            loader.append((img['id'], sa_dict_bbox))

    for img in json_data['images']:
        f_loader = []
        for img_id, img_data in loader:
            if img['id'] == img_id:
                f_loader.append(img_data)
                with open(os.path.join(main_dir, img['file_name'] + "___objects.json"), "w") as new_json:
                    json.dump([i for n, i in enumerate(f_loader) if i not in f_loader[n + 1:]], new_json, indent=2)

""" panoptic """
if str(coco_json_file).__contains__('panoptic'):

    for img in json_data['images']:
        colors, pixel_count = extcolors.extract(os.path.join(main_dir, img['file_name'].replace('jpg', 'png')))
        print(colors)

    # pan_loader = []
    # for annot in json_data['annotations']:
    #     for cat in json_data['categories']:
    #         for si in annot['segments_info']:
    #             segment_colors = color_generator(len(annot['segments_info']))
    #             if cat['id'] == si['category_id']:
    #                 sa_dict = {'classId': cat['id'], 'probability': 100, 'visible': True, 'attributes': [], 'parts': [],
    #                            'attributeNames': [], 'imageId': annot['image_id']}
    #
    #                 pan_loader.append((sa_dict['imageId'], sa_dict))
    #
    # print(pan_loader, '\n')
    #
    # for img in json_data['images']:
    #     f_loader = []
    #     for img_id, img_data in pan_loader:
    #         if img['id'] == img_id:
    #             f_loader.append(img_data)
    #             with open(os.path.join(main_dir, img['file_name'] + "___objects.json"), "w") as new_json:
    #                 json.dump([i for n, i in enumerate(f_loader) if i not in f_loader[n + 1:]], new_json, indent=2)

""" keypoints """
if str(coco_json_file).__contains__('keypoints'):
    kp_loader = []

    kp_point_loader = []
    kp_ids_loader = []
    for annot in json_data['annotations']:
        kp_ids = []
        if int(annot['num_keypoints']) > 0:
            kp_points = [item for index, item in enumerate(annot['keypoints']) if (index + 1) % 3 != 0]
            kp_points = [(kp_points[i], kp_points[i + 1]) for i in range(0, len(kp_points), 2)]
            kp_ids = merge_tuples(
                [(annot['image_id'], annot['id'], kp_points.index(tup) + 1) for tup in kp_points if tup[0] != 0])
            kp_points = [(annot['image_id'], (annot['id'], kp_points.index(tup) + 1, tup[0], tup[1])) for tup in
                         kp_points if
                         tup[0] != 0]

            for el in kp_points:
                kp_point_loader.append(el)
            for el in kp_ids:
                kp_ids_loader.append(el)

        for cat in json_data['categories']:
            coco_keypoints = cat['keypoints']
            sa_point_labels = {}

            for ckp in coco_keypoints:
                sa_point_labels[coco_keypoints.index(ckp) + 1] = ckp

            if annot['iscrowd'] == 1:
                annot['segmentation'] = rle_to_polygon(annot)

            if cat['id'] == annot['category_id']:

                sa_dict_bbox = {'type': 'bbox', 'points': {'x1': annot['bbox'][0], 'y1': annot['bbox'][1],
                                                           'x2': annot['bbox'][0] + annot['bbox'][2],
                                                           'y2': annot['bbox'][1] + annot['bbox'][3]}, 'className': cat['name'],
                                'classId': cat['id'], 'pointLabels': {}, 'attributes': [], 'probability': 100, 'locked': False,
                                'visible': True, 'groupId': annot['id'], 'imageId': annot['image_id']}

                sa_polygon_loader = [{'type': 'polygon', 'points': annot['segmentation'][p], 'className': cat['name'],
                                      'classId': cat['id'], 'pointLabels': {}, 'attributes': [], 'probability': 100,
                                      'locked': False, 'visible': True, 'groupId': annot['id'], 'imageId': annot['image_id']}
                                     for p in range(len(annot['segmentation']))]

                sa_template = {'type': 'template', 'classId': cat['id'], 'probability': 100, 'points': [], 'connections': [],
                               'attributes': [], 'groupId': annot['id'], 'pointLabels': {}, 'locked': False, 'visible': True,
                               'templateId': annot['id'] - 1, 'className': cat['name'], 'templateName': 'skeleton',
                               'imageId': annot['image_id']}

                for img_id, group_id, img_kps in kp_ids_loader:
                    for loader_img_id, loader_point_data in kp_point_loader:
                        if type(img_kps) is int:
                            for pl_k, pl_v in sa_point_labels.items():
                                if img_kps == pl_k and img_id == sa_template['imageId'] and loader_img_id == img_id:
                                    sa_template['points'].append({'id': loader_point_data[1], 'x': loader_point_data[2],
                                                                  'y': loader_point_data[3]})
                                    sa_template['pointLabels'][pl_k] = pl_v
                        else:
                            for img_kp in img_kps:
                                for pl_k, pl_v in sa_point_labels.items():
                                    if img_kp == pl_k and img_id == sa_template['imageId'] and loader_img_id == img_id \
                                            and group_id == sa_template['groupId'] and loader_point_data[0] == sa_template['groupId']:
                                        sa_template['pointLabels'][pl_k] = pl_v
                                        sa_template['points'].append(
                                            {'id': loader_point_data[1], 'x': loader_point_data[2],
                                             'y': loader_point_data[3]})

                                        print(sa_template['pointLabels'])

                            for skeleton in cat['skeleton']:
                                if loader_img_id == img_id and loader_point_data[0] == sa_template['groupId']\
                                        and skeleton[0] in img_kps and skeleton[1] in img_kps:
                                    sa_template['connections'].append({'id': 1, 'from': skeleton[0], 'to': skeleton[1]})
                                    print(skeleton, skeleton[0], skeleton[1])
                sa_template['points'] = dict_setter(sa_template['points'])
                sa_template['connections'] = dict_setter(sa_template['connections'])

                for i in range(len(sa_template['connections'])):
                    sa_template['connections'][i]['id'] += i

                for img in json_data['images']:
                    for polygon in sa_polygon_loader:
                        if polygon['imageId'] == img['id']:
                            kp_loader.append((img['id'], polygon))
                        if sa_dict_bbox['imageId'] == img['id']:
                            kp_loader.append((img['id'], sa_dict_bbox))
                        if sa_template['imageId'] == img['id']:
                            kp_loader.append((img['id'], sa_template))

    for img in json_data['images']:
        f_loader = []
        for img_id, img_data in kp_loader:
            if img['id'] == img_id:
                f_loader.append(img_data)
        with open(os.path.join(main_dir, img['file_name'] + "___objects.json"), "w") as new_json:
            json.dump(dict_setter(f_loader), new_json, indent=2)
