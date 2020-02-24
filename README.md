# Python conversion scripts between annotate.online format and other common formats.

## Usage

### *From* COCO output *to* annotate.online input format

    python3 coco_to_sa.py --coco-json <input_coco_json>

### *From* annotate.online output *to* COCO input format

#### Panoptic annotation:

    python3 sa_to_coco.py --sa_pixel_dataset <input_sa_json> --thing_ids < e.g., "1 2 5"> --export_root <export_path>

#### Vector annotation:

    python3 sa_to_coco.py --sa_vector_dataset <input_sa_json> --export_root <export_path>

### *From* LabelBox output *to* annotate.online input format

    python3 labelbox_to_sa.py --lb_json <input_labelbox_json>


## Installation

Run `bash install.sh`. This adds python virtualenv "sa_input_converters" and
installs required packages.
