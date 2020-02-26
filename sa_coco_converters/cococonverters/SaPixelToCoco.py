import cv2 as cv
from pycocotools import mask as cocomask
import numpy as np


def sa_pixel_to_coco_instance_segmentation(
    make_annotation, image_commons, id_generator
):

    annotations_per_image = []
    sa_ann_json = image_commons.sa_ann_json
    image_info = image_commons.image_info
    for instance in sa_ann_json:
        if "parts" not in instance:
            continue
        anno_id = next(id_generator)
        parts = [int(part["color"][1:], 16) for part in instance["parts"]]

        category_id = instance['classId']

        instance_bitmask = np.isin(image_commons.flat_mask, parts)
        size = instance_bitmask.shape[::-1]

        databytes = instance_bitmask * np.uint8(255)
        contours, hierarchy = cv.findContours(
            databytes, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE
        )
        coco_instance_mask = cocomask.encode(
            np.asfortranarray(instance_bitmask)
        )

        bbox = cocomask.toBbox(coco_instance_mask).tolist()
        area = int(cocomask.area(coco_instance_mask))
        segmentation = [
            contour.flatten().tolist()
            for contour in contours if len(contour.flatten().tolist()) >= 5
        ]

        annotations_per_image.append(
            make_annotation(
                category_id, image_info['id'], bbox, segmentation, area, anno_id
            )
        )
    return (image_info, annotations_per_image)


def sa_pixel_to_coco_panoptic_segmentation(image_commons, id_generator):

    sa_ann_json = image_commons.sa_ann_json
    flat_mask = image_commons.flat_mask
    ann_mask = image_commons.ann_mask

    segments_info = []

    for instance in sa_ann_json:

        if 'parts' not in instance:
            continue

        parts = [int(part['color'][1:], 16) for part in instance['parts']]
        category_id = instance['classId']
        instance_bitmask = np.isin(flat_mask, parts)
        segment_id = next(id_generator)
        ann_mask[instance_bitmask] = segment_id
        coco_instance_mask = cocomask.encode(
            np.asfortranarray(instance_bitmask)
        )
        bbox = cocomask.toBbox(coco_instance_mask).tolist()
        area = int(cocomask.area(coco_instance_mask))

        segment_info = {
            'id': segment_id,
            'category_id': category_id,
            'area': area,
            'bbox': bbox,
            'iscrowd': 0
        }

        segments_info.append(segment_info)

    return (image_commons.image_info, segments_info, image_commons.ann_mask)
