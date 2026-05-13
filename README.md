# Machine Learning Image Annotation Tool

A Python desktop application for annotating images for machine learning datasets.

## Features

- Draw bounding boxes on images
- Assign labels/classes
- Navigate through image datasets
- Save annotations in JSON format
- Export annotations in YOLO format
- Simple desktop GUI using Tkinter



## Installation

Clone the repository:

```bash
git clone https://github.com/bugtechz/ml-image-annotation-tool.git
cd ml-image-annotation-tool
```

Install dependencies:

```bash
pip install pillow
```

Run the application:

```bash
python annotation_tool.py
```

## Export Formats

### JSON
Custom annotation format.

### YOLO
Exports:
- .txt annotation files
- classes.txt

Compatible with YOLOv5, YOLOv8, and Ultralytics.

## Technologies Used

- Python
- Tkinter
- Pillow (PIL)

## Future Improvements

- Polygon segmentation
- COCO export support
- Auto-save
- Zoom and pan
- Keyboard shortcuts
- Dark mode
- Multi-class color coding

## License

MIT License
