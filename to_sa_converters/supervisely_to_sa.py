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

sa_classes_loader = []

for md in meta_data['classes']:
    if md['geometry_config'] == {}:
        classes_dict = {
            'name': md['title'],
            'id': mapped_classes_data[md['title']][0],
            'color': md['color'],
            'attribute_groups': []
        }

        sa_classes_loader.append(classes_dict)
with open(os.path.join(classes_dir, "classes.json"), "w") as classes_json:
    json.dump(sa_classes_loader, classes_json, indent=2)
