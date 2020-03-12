import os
import json
import argparse
import xmltodict

from pprint import pprint

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
            pvoc_json = json.dumps(xmltodict.parse(open(os.path.join(root, file_name)).read()))
            pvoc_jsons.append(pvoc_json)
print(pvoc_jsons)
