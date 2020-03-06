import os
import json
import argparse
import requests
import numpy as np

from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument(
    "--lb-json", type=str, required=True, help="Argument must be JSON file"
)
p = parser.parse_args()

lb_json = p.lb_json
lb_json_folder, lb_json_file = os.path.split(lb_json)

main_dir = os.path.join(os.path.abspath(lb_json) + "__formated")
if not os.path.exists(main_dir):
    os.mkdir(main_dir)

classes_dir = os.path.join(main_dir, "classes")
if not os.path.exists(classes_dir):
    os.mkdir(classes_dir)


# For downloading images from LabelBox's storage
def download_image(url, file_name):
    print("downloading: ", url)
    r = requests.get(url, stream=True)
    with open(os.path.join(main_dir, file_name), 'wb') as f:
        f.write(r.content)


# Returns unique values of list. Values can be dicts or lists!
def dict_setter(list_of_dicts):
    return [
        d for n, d in enumerate(list_of_dicts) if d not in list_of_dicts[n + 1:]
    ]


# Converts HEX values to RGB values
def hex_to_rgb(hex_string):
    h = hex_string.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# Generates blue colors in range(n)
def blue_color_generator(n, hex_values=True):
    hex_colors = []
    for i in range(n):
        int_color = i * 15
        bgr_color = np.array(
            [
                int_color & 255, (int_color >> 8) & 255,
                (int_color >> 16) & 255, 255
            ],
            dtype=np.uint8
        )
        hex_color = '#' + "{:02x}".format(
            bgr_color[2]
        ) + "{:02x}".format(bgr_color[1], ) + "{:02x}".format(bgr_color[0])
        if hex_values:
            hex_colors.append(hex_color)
        else:
            hex_colors.append(hex_to_rgb(hex_color))
    return hex_colors


json_data = json.load(open(os.path.join(lb_json_folder, lb_json_file)))

classes = set()
sa_classes_loader = []
def_dict = defaultdict(list)

for d in json_data:
    classes.update(d['Label'].keys())

    # download images from Labelbox's storage
    download_image(d['Labeled Data'], d['External ID'])

    # Classes

    for class_name in classes:
        colors = blue_color_generator(len(classes))
        c_index = list(classes).index(class_name)

        sa_classes = {
            'id': c_index + 1,
            'name': class_name,
            'color': colors[c_index],
            'attribute_groups': []
        }
        sa_classes_loader.append(sa_classes)
        try:
            for i in range(len(d['Label'][class_name])):
                sa_loader = []

                sa_obj = {
                    'probability': 100,
                    'groupId': 0,
                    'pointLabels': {},
                    'locked': False,
                    'visible': True,
                    'attributes': [],
                    'className': class_name
                }

                if sa_obj['className'] == class_name:
                    sa_obj['classId'] = c_index + 1

                for el in d['Label'][class_name][i].values():
                    polygon_points = []

                    if len(el) == 2:
                        sa_obj['type'] = 'point'
                        sa_obj['x'] = el['x']
                        sa_obj['y'] = el['y']

                    elif len(el) == 4 and isinstance(el, list):
                        sa_obj['type'] = 'bbox'
                        sa_obj['points'] = {
                            "x1": el[0]['x'],
                            "x2": el[2]['x'],
                            "y1": el[0]['y'],
                            "y2": el[2]['y']
                        }

                    for el_index in range(len(el)):
                        if len(el) > 4:
                            polygon_points.append(el[el_index]['x'])
                            polygon_points.append(el[el_index]['y'])
                            sa_obj['type'] = 'polygon'
                            sa_obj['points'] = polygon_points

                sa_loader.append((d['External ID'], sa_obj))

                for k, *v in sa_loader:
                    def_dict[k].append(*v)

                for key, value in def_dict.items():
                    if key == d['External ID']:
                        with open(
                            os.path.join(
                                main_dir, d['External ID'] + "___objects.json"
                            ), "w"
                        ) as new_json:
                            json.dump(value, new_json, indent=2)

        except KeyError:
            print("keyerror")

with open(os.path.join(classes_dir, "classes.json"), "w") as classes_json:
    json.dump(list(sa_classes_loader), classes_json, indent=2)
