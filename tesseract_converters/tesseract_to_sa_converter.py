import os
import json
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input',
                        help='Path to input files or folder\
                        with tesseract dict format.',
                        required=True)
    parser.add_argument('--output', help='Path to output folder.')
    parser.add_argument('--verbose',
                        default='0',
                        choices=['0', '1', '2'],
                        help="0 -- Doesn't print anything,\
        1 -- Prints number of converted files,\
        2 -- Prints number of converted files and unconverted files.")
    args = parser.parse_args()

    input_files_list = get_input_list(args.input)
    file_name = [os.path.basename(file) for file in input_files_list]

    output_files_list = []
    if args.output == None:
        output_files_list = get_output_list(file_name)
    else:
        output_files_list = get_output_list(file_name, args.output)

    converter(input_files_list, output_files_list, args.verbose)


def get_input_list(path):
    input_files_list = []
    try:
        if os.path.isfile(path):
            input_files_list.append(os.path.abspath(path))
        else:
            list_files = os.listdir(path)
            abs_path = os.path.abspath(path)
            for file in list_files:
                input_files_list.append(os.path.join(abs_path, file))
    except IOError:
        print("ERROR: '%s' file or folder doesn't exist!" % (path))
    return input_files_list


def get_output_list(input_list, path='./output'):
    if os.path.exists(path):
        abs_path = os.path.abspath(path)
    else:
        os.makedirs(path)
        abs_path = os.path.abspath(path)

    output_files_list = []
    for file in input_list:
        output_files_list.append(os.path.join(abs_path, file))

    return output_files_list


def converter(input_files_list, output_files_list, verbose=0):
    converted = 0
    for file_in, file_out in zip(input_files_list, output_files_list):
        try:
            file_json = json.load(open(file_in))
            output = []
            for i in range(len(file_json['level'])):
                dd = {
                    "type": "bbox",
                    "points": {
                        "x1": file_json["left"][i],
                        "y1": file_json["top"][i],
                        "x2": file_json["left"][i] + file_json["width"][i],
                        "y2": file_json["top"][i] + file_json["height"][i]
                    },
                    "className": file_json["text"][i],
                    "classID": 0,
                    "pointLabels": {},
                    "attributes": [],
                    "probability": 100,
                    "locked": False,
                    "visible": True,
                    "groupId": 0,
                    "imageId": 0
                }
                output.append(dd)
            json.dump(output, open(file_out, "w"), indent=2)
            converted += 1
        except ValueError:
            if verbose == '2':
                print("WARNING: '%s' file is not json format!" % (file_in))

    if int(verbose) > 0:
        print("Converted to sa format: %d of %d" %
              (converted, len(input_files_list)))


if __name__ == '__main__':
    main()
