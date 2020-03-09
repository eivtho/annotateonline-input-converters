import os
import json
import shutil
import argparse

from pprint import pprint

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

meta_data = {}
mapped_classes_data = {}
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

sa_template_loader = []
sa_classes_loader = []

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
            sa_template['pointLabels'][point_index + 1] = md['geometry_config']['nodes'][pn]['label']
        sa_template_loader.append(sa_template)

    else:
        classes_dict = {
            'name': md['title'],
            'id':  mapped_classes_data[md['title']][0] * (-1),
            'color': md['color'],
            'attribute_groups': []
        }

        sa_classes_loader.append(classes_dict)

with open(os.path.join(classes_dir, "classes.json"), "w") as classes_json:
    json.dump(sa_classes_loader, classes_json, indent=2)
