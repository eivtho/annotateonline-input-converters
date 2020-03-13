import os
import json
import shutil
import argparse
import xmltodict

parser = argparse.ArgumentParser()
parser.add_argument(
    "--pvoc-dir",
    type=str,
    required=True,
    help="Path of the directory, which contains all output data of Pascal VOC"
)
p = parser.parse_args()

pvoc_folder = p.pvoc_dir

sa_folder = os.path.join(os.path.abspath(pvoc_folder) + "__converted")
if not os.path.exists(sa_folder):
    os.mkdir(sa_folder)

classes_dir = os.path.join(sa_folder, "classes")
if not os.path.exists(classes_dir):
    os.mkdir(classes_dir)

pvoc_jsons = []
for root, dirs, files in os.walk(pvoc_folder, topdown=True):
    for file_name in files:
        if file_name.endswith('xml'):
            xml = file_name
            pvoc_json = eval(json.dumps(xmltodict.parse(open(os.path.join(root, file_name)).read())))
            pvoc_jsons.append(pvoc_json)

        if file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            shutil.copyfile(
                os.path.join(root, file_name),
                os.path.join(sa_folder, file_name)
            )

for pv_json in pvoc_jsons:
    sa_loader = []
    if isinstance(pv_json['annotation']['object'], list):
        for obj in pv_json['annotation']['object']:
            sa_bbox = {
                    'type': 'bbox',
                    'points':
                            {
                                'x1': obj['bndbox']['xmax'],
                                'y1': obj['bndbox']['ymax'],
                                'x2': obj['bndbox']['xmin'],
                                'y2': obj['bndbox']['ymin']
                            },
                    'className': obj['name'],
                    'classId': '?',
                    'attributes': [],
                    'probability': 100,
                    'locked': False,
                    'visible': True,
                    'groupId': 0
                }
            sa_loader.append(sa_bbox)
    else:
        sa_bbox = {
                    'type': 'bbox',
                    'points':
                            {
                                'x1': pv_json['annotation']['object']['bndbox']['xmax'],
                                'y1': pv_json['annotation']['object']['bndbox']['ymax'],
                                'x2': pv_json['annotation']['object']['bndbox']['xmin'],
                                'y2': pv_json['annotation']['object']['bndbox']['ymin']
                            },
                    'className': pv_json['annotation']['object']['name'],
                    'classId': '?',
                    'attributes': [],
                    'probability': 100,
                    'locked': False,
                    'visible': True,
                    'groupId': 0
                }
        sa_loader.append(sa_bbox)
    with open(os.path.join(sa_folder, pv_json['annotation']['filename'] + "___objects.json"), "w") as new_json:
        json.dump(sa_loader, new_json, indent=2)
    # print(sa_loader)
