import argparse
import json
import os
import random
import requests
from collections import defaultdict

parser = argparse.ArgumentParser()
parser.add_argument(
    "--lb_json", type=str, required=True, help="Argument must be JSON file"
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

data = json.load(open(os.path.join(lb_json_folder, lb_json_file)))

image_names_list = []
classes = set()
class_names_list = []
images_link_list = []

def_dict = defaultdict(list)


def download_image(url, file_name):
    print("downloading: ", url)
    r = requests.get(url, stream=True)
    with open(os.path.join(main_dir, file_name), 'wb') as f:
        f.write(r.content)


def generate_colors(n):
    rgb_values = []
    hex_values = []
    r = int(random.random() * 256)
    g = int(random.random() * 256)
    b = int(random.random() * 256)
    step = 256 / n
    for _ in range(n):
        r += step
        g += step
        b += step
        r = int(r) % 256
        g = int(g) % 256
        b = int(b) % 256
        r_hex = hex(r)[2:]
        g_hex = hex(g)[2:]
        b_hex = hex(b)[2:]
        hex_values.append('#' + r_hex + g_hex + b_hex)
        rgb_values.append((r, g, b))
    return hex_values


for d in data:
    image_names_list.append(d['External ID'])
    images_link_list.append((d['Labeled Data'], d['External ID']))
    classes.update(d['Label'].keys())
    classes_set_list = list(classes)
    classes_loader = []

    for class_name in classes:
        classes_dict = {}
        colors = generate_colors(len(classes))
        print(len(colors))

        try:
            for color in colors:
                classes_dict['id'] = classes_set_list.index(class_name) + 1
                classes_dict['name'] = class_name
                classes_dict['color'] = color
                classes_dict['attribute_groups'] = []
            classes_loader.append(classes_dict)
            with open(
                os.path.join(classes_dir, "classes.json"), "w"
            ) as classes_json:
                json.dump(classes_loader, classes_json, indent=2)

            for i in range(len(d['Label'][class_name])):
                loader_dict = {}
                ex_loader = []

                loader_dict['probability'] = 100
                loader_dict['groupId'] = 0
                loader_dict['pointLabels'] = {}
                loader_dict['locked'] = False
                loader_dict['visible'] = True
                loader_dict['attributes'] = []
                loader_dict['className'] = class_name
                if loader_dict['className'] == class_name:
                    loader_dict['classId'
                               ] = classes_set_list.index(class_name) + 1
                for el in d['Label'][class_name][i].values():
                    polygon_points = []

                    if len(el) == 2:
                        loader_dict['type'] = 'point'
                        loader_dict['x'] = el['x']
                        loader_dict['y'] = el['y']

                    elif len(el) == 4 and isinstance(el, list):
                        loader_dict['type'] = 'bbox'
                        loader_dict['points'] = {
                            "x1": el[0]['x'],
                            "x2": el[2]['x'],
                            "y1": el[0]['y'],
                            "y2": el[2]['y']
                        }

                    for el_index in range(len(el)):
                        if len(el) > 4:
                            polygon_points.append(el[el_index]['x'])
                            polygon_points.append(el[el_index]['y'])
                            loader_dict['type'] = 'polygon'
                            loader_dict['points'] = polygon_points

                ex_loader.append((d['External ID'], loader_dict))

                for k, *v in ex_loader:
                    def_dict[k].append(*v)

                for image_name in image_names_list:
                    for key, value in def_dict.items():
                        if key == image_name:
                            with open(
                                os.path.join(
                                    main_dir, image_name + "___objects.json"
                                ), "w"
                            ) as new_json:
                                json.dump(value, new_json, indent=2)

        except KeyError:
            print("keyerror")

    for link, name in images_link_list:
        download_image(link, name)
