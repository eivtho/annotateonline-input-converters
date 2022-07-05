from datetime import datetime
from collections import namedtuple
import json
import glob
import os
import numpy as np
from panopticapi.utils import id2rgb
from PIL import Image


class CoCoConverter(object):
    def __init__(self, dataset_name_, export_root_, project_type_, output_dir_, task_ = None):
        self.project_type = project_type_
        self.dataset_name = dataset_name_
        self.export_root = export_root_
        self.output_dir = output_dir_
        self.task = task_
        self.failed_conversion_cnt = 0
    def _create_single_category(self, item):
        category = {
            'id': item.id,
            'name': item.class_name['name'],
            'supercategory': item.class_name['name'],
            'isthing': 1,
            'color': id2rgb(item.id)
        }
        return category

    def set_output_dir(self, output_dir_):
        self.output_dir = output_dir_

    def set_export_root(self, export_dir):
        self.export_root = export_dir

    def set_dataset_name(self, dname):
        self.dataset_name = dname

    def increase_converted_count(self):
        self.failed_conversion_cnt = self.failed_conversion_cnt + 1
    def set_num_converted(self, num_converted_):
        self.num_converted = num_converted_

    def _create_categories(self, path_to_classes):

        classes = None
        s_class = namedtuple('Class', ['class_name', 'id'])

        with open(path_to_classes, 'r') as fp:
            classes = json.load(fp)
        categories = [
            self._create_single_category(s_class(item, item['id']))
            for item in classes
        ]
        return categories

    def _make_id_generator(self):
        cur_id = 0
        while True:
            cur_id += 1
            yield cur_id

    def _create_skeleton(self):
        out_json = {
            'info':
                {
                    'description': 'This is dataset.'.format(self.dataset_name),
                    'url': 'https://superannotate.ai',
                    'version': '1.0',
                    'year': 2020,
                    'contributor': 'Superannotate AI',
                    'date_created': datetime.now().strftime("%d/%m/%Y")
                },
            'licenses':
                [
                    {
                        'url': 'https://superannotate.ai',
                        'id': 1,
                        'name': 'Superannotate AI'
                    }
                ],
            'images': [],
            'annotations': [],
            'categories': []
        }
        return out_json

    def _load_sa_jsons(self):
        jsons = []
        if self.project_type == 'pixel':
            jsons = glob.glob(os.path.join(self.export_root, '*pixel.json'))
        elif self.project_type == 'vector':
            jsons = glob.glob(os.path.join(self.export_root, '*objects.json'))

        self.set_num_converted(len(jsons))
        return jsons

    def _prepare_single_image_commons_pixel(self, id_, json_path):
        ImgCommons = namedtuple(
            'ImgCommons', [
                'image_info', 'sa_ann_json', 'ann_mask', 'sa_bluemask_rgb',
                'flat_mask'
            ]
        )
        rm_len = len('___pixel.json')
        image_path = json_path[:-rm_len
                              ] + '___lores.jpg'  # maybe not use low res files?

        sa_ann_json = json.load(open(os.path.join(json_path)))
        sa_bluemask_path = os.path.join(json_path[:-rm_len] + '___save.png')

        image_info = self.__make_image_info(json_path, id_, self.project_type)

        sa_bluemask_rgb = np.asarray(
            Image.open(sa_bluemask_path).convert('RGB'), dtype=np.uint32
        )

        ann_mask = np.zeros(
            (image_info['height'], image_info['width']), dtype=np.uint32
        )
        flat_mask = (sa_bluemask_rgb[:, :, 0] <<
                     16) | (sa_bluemask_rgb[:, :, 1] <<
                            8) | (sa_bluemask_rgb[:, :, 2])

        res = ImgCommons(
            image_info, sa_ann_json, ann_mask, sa_bluemask_rgb, flat_mask
        )

        return res

    def __make_image_info(self, json_path, id_, source_type):
        if source_type == 'pixel':
            rm_len = len('___pixel.json')
        elif source_type == 'vector':
            rm_len = len('___objects.json')

        image_path = json_path[:-rm_len]

        # img_width, img_height = Image.open(image_path).size
        metadata = json.load(open(json_path))['metadata']
        img_width, img_height = metadata['width'], metadata['height']
        image_info = {
            'id': id_,
            # 'file_name': image_path[len(self.output_dir) + 1:],
            'file_name': f'https://media.digitalarkivet.no/image/{image_path.split("/")[-1]}',
            'height': img_height,
            'width': img_width,
            'license': 1
        }

        return image_info

    def _prepare_single_image_commons_vector(self, id_, json_path):
        ImgCommons = namedtuple('ImgCommons', ['image_info', 'sa_ann_json'])

        image_info = self.__make_image_info(json_path, id_, self.project_type)
        sa_ann_json = json.load(open(json_path))

        res = ImgCommons(image_info, sa_ann_json['instances'])

        return res

    def _prepare_single_image_commons(self, id_, json_path):
        res = None
        if self.project_type == 'pixel':
            res = self._prepare_single_image_commons_pixel(id_, json_path)
        elif self.project_type == 'vector':
            res = self._prepare_single_image_commons_vector(id_, json_path)
        return res
