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
classes = set()
for root, dirs, files in os.walk(pvoc_folder, topdown=True):
    for file_name in files:
        if file_name.endswith('xml'):
            xml = file_name
            pvoc_json = eval(json.dumps(xmltodict.parse(open(os.path.join(root, file_name)).read())))
            pvoc_jsons.append(pvoc_json)

            if isinstance(pvoc_json['annotation']['object'], list):
                for obj in pvoc_json['annotation']['object']:
                    classes.add(obj['name'])
            else:
                classes.add(pvoc_json['annotation']['object']['name'])

        if file_name.endswith('.jpg') or file_name.endswith('.jpeg'):
            shutil.copyfile(
                os.path.join(root, file_name),
                os.path.join(sa_folder, file_name)
            )

sa_classes = []
for c in list(classes):
    sa_class = {
        "id": list(classes).index(c) + 1,
        "name": c,
        "color": "#000000",  # ?
        "attribute_groups": []
      }
    sa_classes.append(sa_class)
with open(os.path.join(classes_dir, "classes.json"), "w") as classes_json:
    json.dump(sa_classes, classes_json, indent=2)

for pv_json in pvoc_jsons:
    sa_loader = []
    if isinstance(pv_json['annotation']['object'], list):
        for obj in pv_json['annotation']['object']:
            try:
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
                        'classId': '?',
                        'attributes': [{'pose': obj['pose'],
                                        'truncated': obj['truncated'],
                                        'difficult': obj['difficult']}],
                        'probability': 100,
                        'locked': False,
                        'visible': True,
                        'groupId': 0
                    }
                sa_loader.append(sa_bbox)
            except KeyError:
                print('KeyError')
    else:
        try:
            sa_bbox = {
                        'type': 'bbox',
                        'points':
                                {
                                    'x1': pv_json['annotation']['object']['bndbox']['xmin'],
                                    'y1': pv_json['annotation']['object']['bndbox']['ymin'],
                                    'x2': pv_json['annotation']['object']['bndbox']['xmax'],
                                    'y2': pv_json['annotation']['object']['bndbox']['ymax']
                                },
                        'className': pv_json['annotation']['object']['name'],
                        'classId': '?',
                        'attributes': [{'pose': pv_json['annotation']['object']['pose'],
                                        'truncated': pv_json['annotation']['object']['truncated'],
                                        'difficult': pv_json['annotation']['object']['difficult']}],
                        'probability': 100,
                        'locked': False,
                        'visible': True,
                        'groupId': 0
                    }
            sa_loader.append(sa_bbox)
        except KeyError:
            print("KeyError")

    with open(os.path.join(sa_folder, pv_json['annotation']['filename'] + "___objects.json"), "w") as new_json:
        json.dump(sa_loader, new_json, indent=2)
