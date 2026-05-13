import json
import os
from dataclasses import dataclass, asdict
from typing import List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk


@dataclass
class BoundingBox:
    label: str
    x1: int
    y1: int
    x2: int
    y2: int


class ImageAnnotationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Machine Learning Image Annotation Tool")
        self.root.geometry("1400x900")

        self.image_paths: List[str] = []
        self.current_index = 0
        self.annotations = {}

        self.current_image = None
        self.tk_image = None
        self.canvas_image_id = None

        self.scale_x = 1
        self.scale_y = 1

        self.start_x = None
        self.start_y = None
        self.temp_rect = None

        self.selected_label = tk.StringVar(value="object")

        self.setup_ui()

    def setup_ui(self):
        toolbar = tk.Frame(self.root, bg="#e8e8e8", height=50)
        toolbar.pack(fill=tk.X)

        tk.Button(toolbar, text="Open Folder", command=self.load_folder).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="Previous", command=self.previous_image).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Next", command=self.next_image).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Save JSON", command=self.save_annotations_json).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Export YOLO", command=self.export_yolo).pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="Clear Boxes", command=self.clear_boxes).pack(side=tk.LEFT, padx=5)

        tk.Label(toolbar, text="Class Label:").pack(side=tk.LEFT, padx=(20, 5))
        tk.Entry(toolbar, textvariable=self.selected_label, width=20).pack(side=tk.LEFT)

        self.image_label = tk.Label(toolbar, text="No folder loaded")
        self.image_label.pack(side=tk.RIGHT, padx=10)

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, bg="black", cursor="cross")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(main_frame, width=300, bg="#f4f4f4")
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Label(sidebar, text="Annotations", font=("Arial", 14, "bold"), bg="#f4f4f4").pack(pady=10)

        self.annotation_list = tk.Listbox(sidebar)
        self.annotation_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Button(sidebar, text="Delete Selected", command=self.delete_selected_annotation).pack(pady=10)

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.root.bind("<Right>", lambda e: self.next_image())
        self.root.bind("<Left>", lambda e: self.previous_image())

    def load_folder(self):
        folder = filedialog.askdirectory(title="Select Image Folder")
        if not folder:
            return

        supported = (".jpg", ".jpeg", ".png", ".bmp")
        self.image_paths = [
            os.path.join(folder, f)
            for f in sorted(os.listdir(folder))
            if f.lower().endswith(supported)
        ]

        if not self.image_paths:
            messagebox.showerror("Error", "No images found in folder")
            return

        self.current_index = 0
        self.load_image()

    def load_image(self):
        if not self.image_paths:
            return

        image_path = self.image_paths[self.current_index]
        self.image_label.config(
            text=f"{os.path.basename(image_path)} ({self.current_index + 1}/{len(self.image_paths)})"
        )

        self.current_image = Image.open(image_path)

        canvas_width = self.canvas.winfo_width() or 1000
        canvas_height = self.canvas.winfo_height() or 800

        image_copy = self.current_image.copy()
        image_copy.thumbnail((canvas_width - 20, canvas_height - 20))

        self.scale_x = self.current_image.width / image_copy.width
        self.scale_y = self.current_image.height / image_copy.height

        self.tk_image = ImageTk.PhotoImage(image_copy)

        self.canvas.delete("all")
        self.canvas_image_id = self.canvas.create_image(
            10,
            10,
            anchor=tk.NW,
            image=self.tk_image,
        )

        self.draw_existing_annotations()
        self.refresh_annotation_list()

    def current_image_key(self):
        if not self.image_paths:
            return None
        return os.path.basename(self.image_paths[self.current_index])

    def on_mouse_down(self, event):
        self.start_x = event.x
        self.start_y = event.y

        if self.temp_rect:
            self.canvas.delete(self.temp_rect)

        self.temp_rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline="red",
            width=2,
        )

    def on_mouse_drag(self, event):
        if self.temp_rect:
            self.canvas.coords(
                self.temp_rect,
                self.start_x,
                self.start_y,
                event.x,
                event.y,
            )

    def on_mouse_up(self, event):
        if self.start_x is None or self.start_y is None:
            return

        x1 = int(min(self.start_x, event.x) * self.scale_x)
        y1 = int(min(self.start_y, event.y) * self.scale_y)
        x2 = int(max(self.start_x, event.x) * self.scale_x)
        y2 = int(max(self.start_y, event.y) * self.scale_y)

        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return

        label = self.selected_label.get().strip()
        if not label:
            label = "object"

        annotation = BoundingBox(label, x1, y1, x2, y2)

        image_key = self.current_image_key()
        self.annotations.setdefault(image_key, []).append(annotation)

        self.load_image()

    def draw_existing_annotations(self):
        image_key = self.current_image_key()
        if image_key not in self.annotations:
            return

        for annotation in self.annotations[image_key]:
            x1 = annotation.x1 / self.scale_x
            y1 = annotation.y1 / self.scale_y
            x2 = annotation.x2 / self.scale_x
            y2 = annotation.y2 / self.scale_y

            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline="lime",
                width=2,
            )

            self.canvas.create_text(
                x1 + 5,
                y1 + 15,
                anchor=tk.W,
                fill="yellow",
                text=annotation.label,
                font=("Arial", 12, "bold"),
            )

    def refresh_annotation_list(self):
        self.annotation_list.delete(0, tk.END)

        image_key = self.current_image_key()
        if image_key not in self.annotations:
            return

        for i, ann in enumerate(self.annotations[image_key]):
            self.annotation_list.insert(
                tk.END,
                f"{i + 1}. {ann.label} [{ann.x1}, {ann.y1}, {ann.x2}, {ann.y2}]",
            )

    def delete_selected_annotation(self):
        selection = self.annotation_list.curselection()
        if not selection:
            return

        index = selection[0]
        image_key = self.current_image_key()

        if image_key in self.annotations:
            del self.annotations[image_key][index]
            self.load_image()

    def clear_boxes(self):
        image_key = self.current_image_key()
        if image_key in self.annotations:
            self.annotations[image_key] = []
            self.load_image()

    def previous_image(self):
        if not self.image_paths:
            return

        self.current_index = max(0, self.current_index - 1)
        self.load_image()

    def next_image(self):
        if not self.image_paths:
            return

        self.current_index = min(len(self.image_paths) - 1, self.current_index + 1)
        self.load_image()

    def save_annotations_json(self):
        if not self.annotations:
            messagebox.showwarning("Warning", "No annotations to save")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
        )

        if not save_path:
            return

        export_data = {}

        for image_name, annotations in self.annotations.items():
            export_data[image_name] = [asdict(a) for a in annotations]

        with open(save_path, "w") as f:
            json.dump(export_data, f, indent=2)

        messagebox.showinfo("Saved", f"Annotations saved to:\n{save_path}")

    def export_yolo(self):
        if not self.annotations:
            messagebox.showwarning("Warning", "No annotations to export")
            return

        export_dir = filedialog.askdirectory(title="Select YOLO Export Folder")
        if not export_dir:
            return

        labels = self.collect_labels()
        label_map = {label: idx for idx, label in enumerate(labels)}

        with open(os.path.join(export_dir, "classes.txt"), "w") as f:
            for label in labels:
                f.write(label + "\n")

        for image_name, anns in self.annotations.items():
            image_path = next(
                (p for p in self.image_paths if os.path.basename(p) == image_name),
                None,
            )

            if not image_path:
                continue

            image = Image.open(image_path)
            width, height = image.size

            txt_name = os.path.splitext(image_name)[0] + ".txt"
            txt_path = os.path.join(export_dir, txt_name)

            with open(txt_path, "w") as f:
                for ann in anns:
                    class_id = label_map[ann.label]

                    x_center = ((ann.x1 + ann.x2) / 2) / width
                    y_center = ((ann.y1 + ann.y2) / 2) / height
                    box_width = (ann.x2 - ann.x1) / width
                    box_height = (ann.y2 - ann.y1) / height

                    f.write(
                        f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n"
                    )

        messagebox.showinfo("Export Complete", "YOLO annotations exported successfully")

    def collect_labels(self):
        labels = set()
        for anns in self.annotations.values():
            for ann in anns:
                labels.add(ann.label)
        return sorted(labels)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageAnnotationApp(root)
    root.mainloop()

