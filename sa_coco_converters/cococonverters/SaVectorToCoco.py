import numpy as np
import cv2 as cv
import json
from pycocotools import mask as cocomask


def sa_vector_to_coco_instance_segmentation(
    make_annotation, image_commons, id_generator
):
    annotations_per_image = []
    grouped_polygons = {}

    image_info = image_commons.image_info
    sa_ann_json = image_commons.sa_ann_json
    for instance in sa_ann_json:
        if instance['type'] != 'polygon':
            continue

        group_id = instance['groupId']
        category_id = instance['classId']
        points = [round(point, 2) for point in instance['points']]
        grouped_polygons.setdefault(group_id, {}).setdefault(category_id,
                                                             []).append(points)

    for polygon_group in grouped_polygons.values():
        anno_id = next(id_generator)
        for cat_id, polygons in polygon_group.items():
            try:
                masks = cocomask.frPyObjects(
                    polygons, image_info['height'], image_info['width']
                )
                mask = cocomask.merge(masks)
                area = int(cocomask.area(mask))
                bbox = cocomask.toBbox(mask).tolist()
                annotation = make_annotation(
                    category_id, image_info['id'], bbox, polygons, area, anno_id
                )
                annotations_per_image.append(annotation)
            except Exception as e:
                print(e)
    return (image_info, annotations_per_image)


def sa_vector_to_coco_keypoint_detection(
    json_paths, id_generator, id_generator_anno, id_generator_img,
    make_image_info
):
    def __make_skeleton(template):
        res = [
            [connection['from'], connection['to']]
            for connection in template['connections']
        ]
        return res

    def __make_keypoints(template):
        int_dict = {
            int(key): value
            for key, value in template['pointLabels'].items()
        }

        return [int_dict[i] for i in range(len(int_dict))]

    def __make_bbox(points):
        xs = [point['x'] for point in points]
        ys = [point['y'] for point in points]

        return [
            int(min(xs)),
            int(min(ys)),
            int(max(xs)) - int(min(xs)),
            int(max(ys)) - int(min(ys))
        ]

    def __load_one_json(path_):
        with open(path_) as fp:
            data = json.load(fp)
        return data

    def __make_annotations(template, id_generator, cat_id, image_id):
        keypoints = []

        for point in template['points']:
            keypoints += [round(point['x'], 2), round(point['y'], 2), 2]
        bbox = __make_bbox(template['points'])
        annotation = {
            'id': next(id_generator),
            'image_id': image_id,
            'iscrowd': 0,
            'bbox': bbox,
            'area': bbox[2] * bbox[3],
            'num_keypoints': len(template['points']),
            'keypoints': keypoints,
            'category_id': cat_id
        }

        return annotation

    template_names = set()
    categories = []
    annotations = []
    images = []
    cnt = 0

    for path_ in json_paths:
        json_data = __load_one_json(path_)

        for instance in json_data:
            if instance['type'] == 'template' and 'templateName' not in instance:
                logging.warning(
                    'There was a template with no "templateName". \
                                This can happen if the template was deleted from annotate.online. Ignoring this annotation'
                )
                continue

            if instance['type'] != 'template' or instance['templateName'
                                                         ] in template_names:
                continue
            try:
                template_names.add(instance['templateName'])
                skeleton = __make_skeleton(instance)
                keypoints = __make_keypoints(instance)
                id_ = next(id_generator)
                supercategory = instance['className']
                name = instance['templateName']
            except Exception as e:
                logging.error(e)

            category_item = {
                'name': name,
                'supercategory': supercategory,
                'skeleton': skeleton,
                'keypoints': keypoints,
                'id': id_
            }
            categories.append(category_item)
        image_id = next(id_generator_img)
        image_info = make_image_info(path_, image_id, 'vector')
        images.append(image_info)

        for instance in json_data:
            cat_id = None
            if instance['type'] == 'template':
                for cat in categories:
                    if cat['name'] == instance['templateName']:
                        cat_id = cat['id']

                annotation = __make_annotations(
                    instance, id_generator_anno, cat_id, image_info['id']
                )
                annotations.append(annotation)
    return (categories, annotations, images)
