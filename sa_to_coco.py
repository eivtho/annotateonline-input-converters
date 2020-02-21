import os
import glob
import json
import argparse

from tqdm import tqdm

import numpy as np

from PIL import Image
from pycocotools import mask as cocomask
from panopticapi.utils import IdGenerator, id2rgb

parser = argparse.ArgumentParser()
parser.add_argument(
    "--sa_pixel_dataset",
    type=str,
    required=False,
    help="Argument must be JSON file"
)
parser.add_argument(
    "--sa_vector_dataset",
    type=str,
    required=False,
    help="Argument must be JSON file"
)
parser.add_argument(
    '--thing_ids',
    nargs='+',
    help='Thing IDs for pixel (panoptic) segmentation.',
    required=False
)

parser.add_argument(
    '--export_root',
    type=str,
    help='Thing IDs for pixel (panoptic) segmentation.',
    required=False
)
args = parser.parse_args()

if args.sa_vector_dataset:
    sa_vector_to_coco_instances(args.sa_vector_dataset, args.export_root)
elif args.sa_pixel_dataset:
    thing_ids = map(int, args.thing_ids.split())
    sa_pixel_to_coco_panoptic(
        args.sa_pixel_dataset, thing_ids, args.export_root
    )


def sa_pixel_to_coco_panoptic(dataset_name, export_root, thing_ids):
    os.makedirs(os.path.join(dataset_name, "annotations"), exist_ok=True)

    info = {
        'description':
            'This is stable 1.0 version of the ' + dataset_name + ' dataset.',
        'url':
            'https://superannotate.ai',
        'version':
            '1.0',
        'year':
            2019,
        'contributor':
            'Annotator LLC',
        'date_created':
            '2019-11-15 11:47:32.67823'
    }

    licences = [
        {
            'url': 'https://superannotate.ai',
            'id': 1,
            'name': 'Superannotate License'
        }
    ]

    categories = []
    dbid_to_catid = {}
    classes = json.load(
        open(os.path.join(export_root, "classes", "classes.json"))
    )
    for idx, dbclass in enumerate(classes, 1):
        category = {
            "id": idx,
            "name": dbclass["name"],
            "supercategory": dbclass["name"],
            "isthing": dbclass["id"] in thing_ids,
            "color": id2rgb(int(dbclass["color"][1:], 16))
        }

        dbid_to_catid[dbclass["id"]] = category["id"]
        categories.append(category)

    print("Converting annotations for {} dataset ...".format(dataset_name))

    id_generator = IdGenerator({cat['id']: cat for cat in categories})
    panoptic_root = os.path.join(
        dataset_name, "panoptic_{}".format(dataset_name)
    )
    os.makedirs(panoptic_root, exist_ok=True)
    jsons = glob.glob(os.path.join(export_root, "*.json"))
    images = []
    annotations = []
    for idx, filepath in tqdm(enumerate(jsons, 1)):
        filename = os.path.basename(filepath)
        imagename = filename[:-len('___pixel.json')] + '___lores.jpg'

        width, height = Image.open(os.path.join(export_root, imagename)).size
        image_info = {
            "id": idx,
            "file_name": imagename,
            "height": height,
            "width": width,
            "license": 1
        }
        images.append(image_info)

        segments_info = []
        sa_ann_json = json.load(open(os.path.join(export_root, filename)))

        sa_bluemask_path = os.path.join(
            export_root, filename[:-len('___pixel.json')] + '___save.png'
        )
        sa_bluemask_rgb = np.asarray(
            Image.open(sa_bluemask_path).convert('RGB'), dtype=np.uint32
        )
        ann_mask = np.zeros((height, width), dtype=np.uint32)
        flat_mask = (sa_bluemask_rgb[:, :, 0] <<
                     16) | (sa_bluemask_rgb[:, :, 1] <<
                            8) | (sa_bluemask_rgb[:, :, 2])

        for instance in sa_ann_json:
            parts = [int(part["color"][1:], 16) for part in instance["parts"]]
            category_id = dbid_to_catid[instance["classId"]]
            instance_bitmask = np.isin(flat_mask, parts)
            segment_id = id_generator.get_id(category_id)
            ann_mask[instance_bitmask] = segment_id
            coco_instance_mask = cocomask.encode(
                np.asfortranarray(instance_bitmask)
            )
            bbox = cocomask.toBbox(coco_instance_mask).tolist()
            area = int(cocomask.area(coco_instance_mask))

            segment_info = {
                "id": segment_id,
                "category_id": category_id,
                "area": area,
                "bbox": bbox,
                "iscrowd": 0
            }
            segments_info.append(segment_info)
        panopticmask = imagename[:-len("jpg")] + "png"
        Image.fromarray(id2rgb(ann_mask)).save(
            os.path.join(panoptic_root, panopticmask)
        )

        annotation = {
            "image_id": idx,
            "file_name": panopticmask,
            "segments_info": segments_info
        }
        annotations.append(annotation)

    panoptic_data = {
        "info": info,
        "licences": licences,
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    json_data = json.dumps(panoptic_data, indent=4)
    with open(
        os.path.join(
            dataset_name, "annotations",
            "panoptic_{}.json".format(dataset_name)
        ), "w+"
    ) as coco_json:
        coco_json.write(json_data)


def sa_vector_to_coco_instances(dataset_name, export_root):
    os.makedirs(os.path.join(dataset_name, "annotations"), exist_ok=True)

    info = {
        'description':
            'This is stable 1.0 version of the ' + dataset_name + ' dataset.',
        'url':
            'https://superannotate.ai',
        'version':
            '1.0',
        'year':
            2019,
        'contributor':
            'Annotator LLC',
        'date_created':
            '2019-11-15 11:47:32.67823'
    }

    licences = [
        {
            'url': 'https://superannotate.ai',
            'id': 1,
            'name': 'Superannotate License'
        }
    ]

    cocotype = "instances"

    categories = []
    dbid_to_catid = {}
    classes = json.load(
        open(os.path.join(export_root, "classes", "classes.json"))
    )
    for idx, dbclass in enumerate(classes, 1):
        category = {
            "id": idx,
            "name": dbclass["name"],
            "supercategory": dbclass["name"],
        }

        dbid_to_catid[dbclass["id"]] = category["id"]
        categories.append(category)

    print("Converting annotations for {} dataset ...".format(dataset_name))

    jsons = glob.glob(os.path.join(export_root, "*.json"))
    images = []
    annotations = []
    for idx, filepath in tqdm(enumerate(jsons, 1)):
        filename = os.path.basename(filepath)
        imagename = filename[:-len('___objects.json')] + '___lores.jpg'

        width, height = Image.open(os.path.join(export_root, imagename)).size
        image_info = {
            "id": idx,
            "file_name": imagename,
            "height": height,
            "width": width,
            "license": 1
        }
        images.append(image_info)

        sa_ann_json = json.load(open(os.path.join(export_root, filename)))

        grouped_polygons = {}
        annotations_perimage = []
        for instance in sa_ann_json:
            if instance["type"] == "polygon":
                group_id = instance["groupId"]
                category_id = dbid_to_catid[instance["classId"]]
                points = [round(point, 2) for point in instance['points']]
                grouped_polygons.setdefault(group_id,
                                            {}).setdefault(category_id,
                                                           []).append(points)

        for ann_idx, polygon_group in enumerate(
            grouped_polygons.values(),
            len(annotations) + 1
        ):
            for category_id, polygons in polygon_group.items():
                try:
                    masks = cocomask.frPyObjects(polygons, height, width)
                    mask = cocomask.merge(masks)
                    area = int(cocomask.area(mask))
                    bbox = cocomask.toBbox(mask).tolist()
                    annotation = {
                        'segmentation': polygons,
                        'area': area,
                        'iscrowd': 0,
                        'image_id': idx,
                        'bbox': bbox,
                        'category_id': category_id,
                        'id': ann_idx
                    }
                    annotations_perimage.append(annotation)
                except Exception as bb_ex:
                    print(filename, bb_ex)
                    continue

        annotations += annotations_perimage

    instances_data = {
        "info": info,
        "type": cocotype,
        "licences": licences,
        "images": images,
        "annotations": annotations,
        "categories": categories
    }

    json_data = json.dumps(instances_data, indent=4)
    with open(
        os.path.join(
            dataset_name, "annotations",
            "instances_{}.json".format(dataset_name)
        ), "w+"
    ) as coco_json:
        coco_json.write(json_data)
