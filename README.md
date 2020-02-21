# Python converstion scripts 'from' and 'to' annotate.online format to other common formats.


## 'From' COCO output 'To' annotate.online input format

    python3 coco_to_sa.py --coco_json <input_coco_json>

## 'From' annotate.online output 'To' COCO input format

### Panoptic annotation:

    python3 sa_to_coco.py --sa_pixel_dataset <input_sa_json> --thing_ids < e.g., "1 2 5"> --export_root <export_path>

### Vector annotation:

    python3 sa_to_coco.py --sa_vector_dataset <input_sa_json> --export_root <export_path>

## 'From' LabelBox output 'To' annotate.online input format

    python3 labelbox_to_sa.py --lb_json <input_labelbox_json>

