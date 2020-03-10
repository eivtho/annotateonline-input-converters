import os
import cv2
import json
import zlib
import base64
import shutil
import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument(
    "--sv-export-dir",
    type=str,
    required=True,
    help="Path of the directory, which contains all exported data"
)
p = parser.parse_args()

sv_folder = p.sv_export_dir

sa_folder = os.path.join(os.path.abspath(sv_folder) + "__converted")
if not os.path.exists(sa_folder):
    os.mkdir(sa_folder)

classes_dir = os.path.join(sa_folder, "classes")
if not os.path.exists(classes_dir):
    os.mkdir(classes_dir)


# Converts bitmaps to polygon
def base64_to_polygon(bitmap):
    z = zlib.decompress(base64.b64decode(bitmap))
    n = np.frombuffer(z, np.uint8)
    mask = cv2.imdecode(n, cv2.IMREAD_UNCHANGED)[:, :, 3].astype(bool)
    contours, hierarchy = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    segmentation = []

    for contour in contours:
        contour = contour.flatten().tolist()
        if len(contour) > 4:
            segmentation.append(contour)
        if len(segmentation) == 0:
            continue
    return segmentation


meta_data = {}
mapped_classes_data = {}
jsons_dir = ''
for root, dirs, files in os.walk(sv_folder, topdown=True):
    for file_name in files:

        if file_name.endswith('.jpg'):
            shutil.copyfile(
                os.path.join(root, file_name),
                os.path.join(sa_folder, file_name)
            )

        if file_name == 'obj_class_to_machine_color.json':
            mapped_classes_data = json.load(open(os.path.join(root, file_name)))

        if file_name == 'meta.json':
            meta_data = json.load(open(os.path.join(root, file_name)))

        if file_name.endswith('.json') and file_name != 'meta.json' and file_name != 'obj_class_to_machine_color.json':
            jsons_dir = root

sa_template_loader = []
sa_classes_loader = []
classes_data = []

for md in meta_data['classes']:
    point_names = []
    if md['geometry_config'] != {}:
        sa_template = {
                    'type': 'template',
                    'classId': mapped_classes_data[md['title']][0] * (-1),
                    'probability': 100,
                    'points': [],
                    'connections': [],
                    'attributes': [],
                    'attributeNames': [],
                    'groupId': 0,
                    'pointLabels': {},
                    'locked': False,
                    'visible': True,
                    'templateId': (mapped_classes_data[md['title']][0] * (-1)) - 1,
                    'className': md['title'],
                    'templateName': md['title']
                }

        for point_name in md['geometry_config']['nodes'].keys():
            point_names.append(point_name)

        for connection in md['geometry_config']['edges']:
            index = md['geometry_config']['edges'].index(connection)
            if connection['dst'] in point_names and connection['src'] in point_names:
                sa_template['connections'].append(
                    {
                        'id': index + 1,
                        'from': point_names.index(connection['src']) + 1,
                        'to': point_names.index(connection['dst']) + 1
                    }
                )

        for pn in point_names:
            point_index = point_names.index(pn)
            sa_template['points'].append(
                {
                    'id': point_index + 1,
                    'x': md['geometry_config']['nodes'][pn]['loc'][0],
                    'y': md['geometry_config']['nodes'][pn]['loc'][1]
                }
            )
            sa_template['pointLabels'][point_index] = md['geometry_config']['nodes'][pn]['label']
        sa_template_loader.append(sa_template)

    else:
        classes_dict = {
            'name': md['title'],
            'id':  mapped_classes_data[md['title']][0] * (-1),
            'color': md['color'],
            'attribute_groups': []
        }

        sa_classes_loader.append(classes_dict)
    classes_data.append((md['title'], mapped_classes_data[md['title']][0] * (-1), md['shape']))

with open(os.path.join(classes_dir, "classes.json"), "w") as classes_json:
    json.dump(sa_classes_loader, classes_json, indent=2)

for json_file in os.listdir(jsons_dir):
    json_data = json.load(open(os.path.join(jsons_dir, json_file)))

    sa_loader = []

    for obj in json_data['objects']:
        for name, id, type in classes_data:
            if obj['classTitle'] == name:

                sa_obj = {
                    'type': '',
                    'points': [],
                    'className': name,
                    'classId': id,
                    'pointLabels': {},
                    'attributes': [],
                    'probability': 100,
                    'locked': False,
                    'visible': True,
                    'groupId': 0
                }

                if type == 'point':
                    del sa_obj['points']
                    sa_obj['type'] = type
                    sa_obj['x'] = obj['points']['exterior'][0][0]
                    sa_obj['y'] = obj['points']['exterior'][0][1]

                elif type == 'line':
                    sa_obj['type'] = 'polyline'
                    sa_obj['points'] = [item for el in obj['points']['exterior'] for item in el]

                elif type == 'rectangle':
                    sa_obj['type'] = 'bbox'
                    sa_obj['points'] = {
                        'x1': obj['points']['exterior'][0][0],
                        'y1': obj['points']['exterior'][0][1],
                        'x2': obj['points']['exterior'][1][0],
                        'y2': obj['points']['exterior'][1][1]}

                elif type == 'polygon':
                    sa_obj['type'] = 'polygon'
                    sa_obj['points'] = [item for el in obj['points']['exterior'] for item in el]

                elif type == 'graph':
                    for temp in sa_template_loader:
                        if temp['className'] == name:
                            sa_obj = temp

                elif type == 'bitmap':
                    for ppoints in base64_to_polygon(obj['bitmap']['data']):
                        sa_ppoints = [x + obj['bitmap']['origin'][0] if i % 2 == 0 else x + obj['bitmap']['origin'][1]
                                      for i, x in enumerate(ppoints)]
                        sa_obj['type'] = 'polygon'
                        sa_obj['points'] = sa_ppoints

                sa_loader.append(sa_obj)

    with open(os.path.join(sa_folder, json_file.replace('.json', '___objects.json')), "w") as sa_json:
        json.dump(sa_loader, sa_json, indent=2)
