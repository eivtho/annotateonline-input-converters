# Python conversion scripts between annotate.online format and other common formats.

## Installation

Run `bash install.sh`. This adds python virtualenv `venv_sa_conv` and
installs required packages.

## Usage

You need to activate python virtualenv with `source venv_sa_conv/bin/activate` beforehand.

### *From* COCO output *to* annotate.online input format

    python3 coco_to_sa.py --coco-json <input_coco_json>

### *From* LabelBox output *to* annotate.online input format

    python3 labelbox_to_sa.py --lb_json <input_labelbox_json>

### *From* annotate.online output *to* COCO input format
There are 5 dataset formats that coco dataset supports, they are accessible [here](http://cocodataset.org/#format-data). We support several conversions from annotate.online formats to coco dataset formats. The command to do so is as follows:
```
usage: sa_to_coco.py [-h] [-is INPUT_IMAGES_SOURCE]
                     [-sr TRAIN_VAL_SPLIT_RATIO] [-ptype PROJECT_TYPE]
                     [-t TASK] [-dn DATASET_NAME] [-od OUTPUT_DIR] [-cp COPYQ]
```
```
optional arguments:
  -h, --help            show this help message and exit
  -is INPUT_IMAGES_SOURCE, --input_images_source INPUT_IMAGES_SOURCE
                        The folder where images and thei corresponding
                        annotation json files are located
  -sr TRAIN_VAL_SPLIT_RATIO, --train_val_split_ratio TRAIN_VAL_SPLIT_RATIO
                        What percentage of input images should be in train set
  -ptype PROJECT_TYPE, --project_type PROJECT_TYPE
                        The type of the annotate.online project can be vector
                        or pixel
  -t TASK, --task TASK  The output format of the converted file, this
                        corresponds to one of 5 coco tasks
  -dn DATASET_NAME, --dataset_name DATASET_NAME
                        The name of the dataset
  -od OUTPUT_DIR, --output_dir OUTPUT_DIR
                        The output folder for the coco json files test/train
                        images
  -cp COPYQ, --copyQ COPYQ
                        Move or copy source images to corresponding test and
                        train folders possible values are True or False. True copies the files
``````

**IMPORTANT:** Running this command will move or copy images from source folder. It will create two folders with names "test_set" and "train_set" and move images correspondingly.

#### Panoptic segmentation
```
python3 sa_to_coco.py -is [path_to_images] -sr [ratio] -ptype pixel -t panoptic_segmentation -dn [dataset_name] -od [output_directory] -cp [copyQ]
```

*please note*: conversion to coco dataset format for panoptic segmentation task is only supported for projects of type pixel in annotate.online

**Note**: You should have all your images their corresponding `save.png`, `pixel.json` and `lores.jpg` files in one folder as well as the `classes.json` file in the same folder.


*Example*
```
python sa_to_coco.py -is ./Tests/fromAnnotateOnline/cats_dogs -sr 80 -ptype pixel -t instance_segmentation -dn test_instance -od output -cp True

```

#### Instance segmentation

```
python3 sa_to_coco.py -is [path_to_images] -sr [ratio] -ptype [vector or pixel] -t instance_segmentation -dn [dataset_name] -od [output_directory] -cp [copyQ]
```

**Note**: if your project is of type 'pixel' you should have all your images their corresponding `save.png`, `pixel.json` and `lores.jpg` files in one folder as well as the `classes.json` file in the same folder. 
If your project is of type  'vector' then you will need all your images their corresponding `lores.jpg`, `objects.json` and `classes.json` files in the same folder

*Example*

```
python sa_to_coco.py -is ./Tests/fromAnnotateOnline/cats_dogs_pan -sr 80 -ptype pixel -t panoptic_segmentation -dn test_panoptic -od output_pan -cp True

```

#### Keypoint detection

```
python3 sa_to_coco.py -is [path_to_images] -sr [ratio] -ptype vector -t keypoint_detection -dn [dataset_name] -od [output_directory] -cp [copyQ] -od [output_directory] -cp [copyQ]
```

*please note*: conversion to coco dataset format for keypoint detection task is only supported for projects of type 'vector' in annotate.online. Furthermore each template should fully describe an object. 

**Note**: You should have all your images their corresponding `objects.json` files in one folder as well as the `classes.json` file in the same folder. 



