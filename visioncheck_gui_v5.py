import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import math

# =========================================================
# VisionCheck AI v5
# Interactive Image Quality Assessment
# for Researchers and Photographers
# =========================================================

DEFAULTS = {
    "sharpness": 45,
    "bright": 210,
    "dark": 55,
    "contrast": 45,
    "exposure": 50
}

PARAMETERS = {
    "sharpness": {"label": "Sharpness", "min": 0, "max": 100},
    "bright": {"label": "Bright Level", "min": 150, "max": 255},
    "dark": {"label": "Dark Level", "min": 0, "max": 120},
    "contrast": {"label": "Contrast", "min": 0, "max": 100},
    "exposure": {"label": "Exposure", "min": 0, "max": 100}
}


def normalize_score(value, minimum, maximum):
    if value <= minimum:
        return 0.0
    if value >= maximum:
        return 100.0
    return 100.0 * (value - minimum) / (maximum - minimum)


def resize_for_analysis(image, target_width=1000):
    h, w = image.shape[:2]
    if w <= target_width:
        return image.copy()

    scale = target_width / w
    new_height = int(h * scale)

    return cv2.resize(
        image,
        (target_width, new_height),
        interpolation=cv2.INTER_AREA
    )


def analyze_image(
    image_path,
    sharpness_threshold,
    dark_threshold,
    bright_threshold,
    contrast_threshold,
    exposure_threshold
):
    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError("Image could not be opened.")

    original_height, original_width = image.shape[:2]
    original_pixels = original_height * original_width

    analysis_image = resize_for_analysis(image)
    gray = cv2.cvtColor(analysis_image, cv2.COLOR_BGR2GRAY)

    height, width = gray.shape[:2]
    total_pixels = height * width

    # Sharpness: Variance of Laplacian
    laplacian_variance = cv2.Laplacian(
        gray, cv2.CV_64F
    ).var()

    sharpness_score = normalize_score(
        laplacian_variance, 25, 300
    )

    # Brightness: mean grayscale intensity
    brightness_raw = float(np.mean(gray))

    if 75 <= brightness_raw <= 190:
        brightness_score = 100.0
    elif brightness_raw < 75:
        brightness_score = max(
            0.0, brightness_raw / 75.0 * 100.0
        )
    else:
        brightness_score = max(
            0.0,
            100.0 - ((brightness_raw - 190.0) / 65.0) * 100.0
        )

    # Contrast: grayscale standard deviation
    contrast_raw = float(np.std(gray))
    contrast_score = normalize_score(
        contrast_raw, 15, 65
    )

    # Exposure: percentage of clipped dark/bright pixels
    dark_pixels = np.sum(gray < 20)
    bright_pixels = np.sum(gray > 235)

    dark_percentage = dark_pixels / total_pixels * 100.0
    bright_percentage = bright_pixels / total_pixels * 100.0
    clipped_percentage = dark_percentage + bright_percentage

    exposure_score = max(
        0.0,
        100.0 - clipped_percentage * 3.0
    )

    # Resolution
    megapixels = original_pixels / 1_000_000

    if megapixels >= 2:
        resolution_score = 100.0
    elif megapixels >= 1:
        resolution_score = 80.0
    elif megapixels >= 0.5:
        resolution_score = 60.0
    else:
        resolution_score = 40.0

    # Overall quality score
    overall_score = (
        sharpness_score * 0.30 +
        brightness_score * 0.20 +
        contrast_score * 0.20 +
        exposure_score * 0.20 +
        resolution_score * 0.10
    )

    # Descriptive final quality status
    if sharpness_score < sharpness_threshold:
        final_result = "BLURRED"
    elif brightness_raw < dark_threshold:
        final_result = "TOO DARK"
    elif brightness_raw > bright_threshold:
        final_result = "TOO BRIGHT"
    elif contrast_score < contrast_threshold:
        final_result = "LOW CONTRAST"
    elif exposure_score < exposure_threshold:
        final_result = "POOR EXPOSURE"
    elif resolution_score < 60:
        final_result = "LOW RESOLUTION"
    else:
        final_result = "CLEAR"

    findings = []

    if sharpness_score < sharpness_threshold:
        findings.append("Possible blur or loss of fine image detail.")

    if brightness_raw < dark_threshold:
        findings.append("Image appears too dark.")

    if brightness_raw > bright_threshold:
        findings.append("Image appears too bright.")

    if contrast_score < contrast_threshold:
        findings.append("Image has low tonal separation or contrast.")

    if exposure_score < exposure_threshold:
        findings.append("Image contains strongly clipped dark or bright regions.")

    if resolution_score < 60:
        findings.append("Image resolution may be insufficient for fine-detail use.")

    if final_result == "CLEAR":
        findings.append("Image is visually clear and adequately exposed.")
        findings.append("Quality is acceptable for further visual use.")

    recommendations = {
        "BLURRED":
            "Improve focus or reduce camera movement before recapturing.",
        "TOO DARK":
            "Increase lighting or exposure before recapturing.",
        "TOO BRIGHT":
            "Reduce lighting or exposure before recapturing.",
        "LOW CONTRAST":
            "Improve lighting, tonal separation, or background contrast.",
        "POOR EXPOSURE":
            "Adjust exposure to reduce excessively dark or bright regions.",
        "LOW RESOLUTION":
            "Use a higher-resolution image when fine visual detail is required.",
        "CLEAR":
            "Suitable for research documentation, dataset use, or general photographic screening."
    }

    return {
        "filename": Path(image_path).name,
        "width": original_width,
        "height": original_height,
        "sharpness": sharpness_score,
        "brightness": brightness_score,
        "contrast": contrast_score,
        "exposure": exposure_score,
        "resolution": resolution_score,
        "overall": overall_score,
        "final_result": final_result,
        "findings": findings,
        "recommendation": recommendations[final_result]
    }


class ThresholdWeb(tk.Canvas):
    def __init__(
        self,
        parent,
        values,
        command=None,
        width=560,
        height=300
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg="white",
            highlightthickness=0
        )

        self.canvas_width = width
        self.canvas_height = height
        self.cx = width / 2
        self.cy = height / 2 + 5
        self.radius = 105

        self.values = values.copy()
        self.command = command
        self.active_parameter = None

        self.parameter_order = [
            "sharpness",
            "bright",
            "dark",
            "contrast",
            "exposure"
        ]

        self.angles = {
            "sharpness": -90,
            "bright": -18,
            "dark": 54,
            "contrast": 126,
            "exposure": 198
        }

        self.bind("<Button-1>", self.mouse_down)
        self.bind("<B1-Motion>", self.mouse_drag)
        self.bind("<ButtonRelease-1>", self.mouse_up)

        self.draw()

    def value_to_ratio(self, parameter):
        info = PARAMETERS[parameter]
        minimum = info["min"]
        maximum = info["max"]
        value = self.values[parameter]

        ratio = (value - minimum) / (maximum - minimum)
        return max(0, min(1, ratio))

    def ratio_to_value(self, parameter, ratio):
        info = PARAMETERS[parameter]
        minimum = info["min"]
        maximum = info["max"]

        value = minimum + ratio * (maximum - minimum)
        return int(round(value))

    def get_axis_point(self, parameter, ratio=1.0):
        angle = math.radians(self.angles[parameter])
        r = self.radius * ratio

        x = self.cx + r * math.cos(angle)
        y = self.cy + r * math.sin(angle)

        return x, y

    def draw(self):
        self.delete("all")

        # Background web rings
        for level in [0.25, 0.50, 0.75, 1.00]:
            points = []

            for parameter in self.parameter_order:
                x, y = self.get_axis_point(parameter, level)
                points.extend([x, y])

            self.create_polygon(
                points,
                fill="",
                outline="#d7dce1",
                width=1
            )

        # Axis lines
        for parameter in self.parameter_order:
            x, y = self.get_axis_point(parameter, 1.0)

            self.create_line(
                self.cx,
                self.cy,
                x,
                y,
                fill="#c5cbd1",
                width=1
            )

        # Current threshold polygon
        current_points = []

        for parameter in self.parameter_order:
            ratio = self.value_to_ratio(parameter)
            x, y = self.get_axis_point(parameter, ratio)
            current_points.extend([x, y])

        self.create_polygon(
            current_points,
            fill="#dbeeff",
            outline="#2e86de",
            width=3
        )

        # Draggable nodes
        for parameter in self.parameter_order:
            ratio = self.value_to_ratio(parameter)
            x, y = self.get_axis_point(parameter, ratio)

            node_radius = 7

            self.create_oval(
                x - node_radius,
                y - node_radius,
                x + node_radius,
                y + node_radius,
                fill="#2e86de",
                outline="white",
                width=2
            )

        # Labels
        label_radius = self.radius + 38

        for parameter in self.parameter_order:
            angle = math.radians(self.angles[parameter])

            x = self.cx + label_radius * math.cos(angle)
            y = self.cy + label_radius * math.sin(angle)

            info = PARAMETERS[parameter]

            self.create_text(
                x,
                y,
                text=f"{info['label']}\n{self.values[parameter]}",
                font=("Arial", 10, "bold"),
                fill="#1f2d3d",
                justify="center"
            )

        # Center point
        self.create_oval(
            self.cx - 4,
            self.cy - 4,
            self.cx + 4,
            self.cy + 4,
            fill="#1f2d3d",
            outline=""
        )

        self.create_text(
            self.cx,
            self.canvas_height - 12,
            text="Drag a blue point inward or outward to tune the threshold",
            font=("Arial", 9),
            fill="#667788"
        )

    def closest_parameter(self, mouse_x, mouse_y):
        closest = None
        minimum_distance = 99999

        for parameter in self.parameter_order:
            ratio = self.value_to_ratio(parameter)
            x, y = self.get_axis_point(parameter, ratio)

            distance = math.sqrt(
                (mouse_x - x) ** 2 +
                (mouse_y - y) ** 2
            )

            if distance < minimum_distance:
                minimum_distance = distance
                closest = parameter

        if minimum_distance <= 25:
            return closest

        return None

    def mouse_down(self, event):
        self.active_parameter = self.closest_parameter(
            event.x,
            event.y
        )

    def mouse_drag(self, event):
        if self.active_parameter is None:
            return

        parameter = self.active_parameter
        angle = math.radians(self.angles[parameter])

        axis_x = math.cos(angle)
        axis_y = math.sin(angle)

        mouse_dx = event.x - self.cx
        mouse_dy = event.y - self.cy

        projected_distance = (
            mouse_dx * axis_x +
            mouse_dy * axis_y
        )

        ratio = projected_distance / self.radius
        ratio = max(0, min(1, ratio))

        self.values[parameter] = self.ratio_to_value(
            parameter,
            ratio
        )

        self.draw()

        if self.command:
            self.command()

    def mouse_up(self, event):
        self.active_parameter = None

    def get_values(self):
        return self.values.copy()

    def reset_values(self):
        self.values = DEFAULTS.copy()
        self.draw()

        if self.command:
            self.command()


class VisionCheckGUI:
    def __init__(self, root):
        self.root = root

        root.title("VisionCheck AI")
        root.geometry("1280x900")
        root.minsize(1100, 800)
        root.configure(bg="#f4f6f8")

        self.current_image_path = None
        self.tk_image = None

        # Header
        tk.Label(
            root,
            text="VisionCheck AI",
            font=("Arial", 25, "bold"),
            bg="#f4f6f8",
            fg="#1f2d3d"
        ).pack(pady=(12, 2))

        tk.Label(
            root,
            text="Interactive Image Quality Assessment for Researchers and Photographers",
            font=("Arial", 11),
            bg="#f4f6f8",
            fg="#566573"
        ).pack(pady=(0, 10))

        main_frame = tk.Frame(root, bg="#f4f6f8")
        main_frame.pack(fill="both", expand=True, padx=15)

        # Image panel
        image_frame = tk.Frame(
            main_frame,
            bg="white",
            bd=2,
            relief="groove"
        )

        image_frame.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10)
        )

        self.image_label = tk.Label(
            image_frame,
            text="No image selected",
            font=("Arial", 14),
            bg="white",
            fg="gray"
        )

        self.image_label.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        # Result panel
        self.result_frame = tk.Frame(
            main_frame,
            bg="white",
            bd=2,
            relief="groove",
            width=390
        )

        self.result_frame.pack(
            side="right",
            fill="y"
        )

        self.result_frame.pack_propagate(False)

        self.file_var = tk.StringVar(value="File: None")
        self.res_var = tk.StringVar(value="Resolution: -")
        self.sharp_var = tk.StringVar(value="Sharpness: -")
        self.bright_var = tk.StringVar(value="Brightness: -")
        self.contrast_var = tk.StringVar(value="Contrast: -")
        self.exposure_var = tk.StringVar(value="Exposure: -")
        self.resolution_var = tk.StringVar(value="Resolution Score: -")
        self.overall_var = tk.StringVar(value="VisionCheck Score: -")
        self.final_var = tk.StringVar(value="FINAL QUALITY STATUS: -")

        self.heading("Image Quality Results")

        self.dynamic(self.file_var)
        self.dynamic(self.res_var)

        self.heading("Scores")

        self.dynamic(self.sharp_var)
        self.dynamic(self.bright_var)
        self.dynamic(self.contrast_var)
        self.dynamic(self.exposure_var)
        self.dynamic(self.resolution_var)

        self.dynamic(
            self.overall_var,
            size=13,
            bold=True
        )

        self.final_label = tk.Label(
            self.result_frame,
            textvariable=self.final_var,
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#1f2d3d",
            wraplength=350,
            justify="left"
        )

        self.final_label.pack(
            anchor="w",
            padx=15,
            pady=(10, 8)
        )

        self.heading("Quality Findings & Recommendation")

        self.findings_text = tk.Text(
            self.result_frame,
            height=12,
            font=("Arial", 10),
            wrap="word",
            bg="#f9fafb"
        )

        self.findings_text.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 12)
        )

        self.findings_text.insert(
            "1.0",
            "No analysis yet."
        )

        self.findings_text.config(state="disabled")

        # Interactive quality-control web
        web_frame = tk.LabelFrame(
            root,
            text="Interactive Quality Control Web",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#1f2d3d"
        )

        web_frame.pack(
            fill="x",
            padx=15,
            pady=(8, 4)
        )

        web_inner = tk.Frame(
            web_frame,
            bg="white"
        )

        web_inner.pack()

        self.threshold_web = ThresholdWeb(
            web_inner,
            DEFAULTS,
            command=self.threshold_changed,
            width=560,
            height=300
        )

        self.threshold_web.pack(
            side="left",
            padx=20
        )

        tk.Button(
            web_inner,
            text="Reset Defaults",
            font=("Arial", 10, "bold"),
            width=15,
            command=self.threshold_web.reset_values
        ).pack(
            side="left",
            padx=25
        )

        # Bottom buttons
        button_frame = tk.Frame(
            root,
            bg="#f4f6f8"
        )

        button_frame.pack(pady=8)

        tk.Button(
            button_frame,
            text="Select Image",
            width=16,
            font=("Arial", 11, "bold"),
            bg="#2e86de",
            fg="white",
            command=self.select_image
        ).pack(
            side="left",
            padx=8
        )

        tk.Button(
            button_frame,
            text="Clear",
            width=16,
            font=("Arial", 11, "bold"),
            command=self.clear_all
        ).pack(
            side="left",
            padx=8
        )

        tk.Button(
            button_frame,
            text="Exit",
            width=16,
            font=("Arial", 11, "bold"),
            bg="#c0392b",
            fg="white",
            command=root.destroy
        ).pack(
            side="left",
            padx=8
        )

    def heading(self, text):
        tk.Label(
            self.result_frame,
            text=text,
            font=("Arial", 14, "bold"),
            bg="white",
            fg="#1f2d3d"
        ).pack(
            anchor="w",
            padx=15,
            pady=(12, 6)
        )

    def dynamic(
        self,
        variable,
        size=11,
        bold=False
    ):
        tk.Label(
            self.result_frame,
            textvariable=variable,
            font=(
                "Arial",
                size,
                "bold" if bold else "normal"
            ),
            bg="white",
            fg="#2f3640"
        ).pack(
            anchor="w",
            padx=15,
            pady=2
        )

    def select_image(self):
        path = filedialog.askopenfilename(
            title="Select Image for VisionCheck AI",
            filetypes=[
                (
                    "Image Files",
                    "*.jpg *.jpeg *.png *.bmp *.tif *.tiff"
                ),
                (
                    "All Files",
                    "*.*"
                )
            ]
        )

        if not path:
            return

        self.current_image_path = path
        self.display_image(path)
        self.run_analysis()

    def display_image(self, path):
        img = Image.open(path)
        img.thumbnail((720, 480))

        self.tk_image = ImageTk.PhotoImage(img)

        self.image_label.config(
            image=self.tk_image,
            text=""
        )

    def run_analysis(self):
        if not self.current_image_path:
            return

        thresholds = self.threshold_web.get_values()

        try:
            results = analyze_image(
                self.current_image_path,
                thresholds["sharpness"],
                thresholds["dark"],
                thresholds["bright"],
                thresholds["contrast"],
                thresholds["exposure"]
            )

            self.update_results(results)

        except Exception as error:
            messagebox.showerror(
                "VisionCheck AI",
                str(error)
            )

    def threshold_changed(self):
        if self.current_image_path:
            self.run_analysis()

    def update_results(self, r):
        self.file_var.set(
            f"File: {r['filename']}"
        )

        self.res_var.set(
            f"Resolution: {r['width']} x {r['height']}"
        )

        self.sharp_var.set(
            f"Sharpness: {r['sharpness']:.1f}%"
        )

        self.bright_var.set(
            f"Brightness: {r['brightness']:.1f}%"
        )

        self.contrast_var.set(
            f"Contrast: {r['contrast']:.1f}%"
        )

        self.exposure_var.set(
            f"Exposure: {r['exposure']:.1f}%"
        )

        self.resolution_var.set(
            f"Resolution Score: {r['resolution']:.1f}%"
        )

        self.overall_var.set(
            f"VisionCheck Score: {r['overall']:.1f}%"
        )

        self.final_var.set(
            f"FINAL QUALITY STATUS: {r['final_result']}"
        )

        if r["final_result"] == "CLEAR":
            self.final_label.config(fg="green")

        elif r["final_result"] in [
            "TOO DARK",
            "TOO BRIGHT",
            "LOW CONTRAST",
            "POOR EXPOSURE"
        ]:
            self.final_label.config(fg="#d68910")

        else:
            self.final_label.config(fg="red")

        self.findings_text.config(state="normal")
        self.findings_text.delete("1.0", tk.END)

        for finding in r["findings"]:
            self.findings_text.insert(
                tk.END,
                "• " + finding + "\n"
            )

        self.findings_text.insert(
            tk.END,
            "\nRecommendation:\n"
        )

        self.findings_text.insert(
            tk.END,
            r["recommendation"]
        )

        self.findings_text.config(state="disabled")

    def clear_all(self):
        self.current_image_path = None
        self.tk_image = None

        self.image_label.config(
            image="",
            text="No image selected"
        )

        self.file_var.set("File: None")
        self.res_var.set("Resolution: -")
        self.sharp_var.set("Sharpness: -")
        self.bright_var.set("Brightness: -")
        self.contrast_var.set("Contrast: -")
        self.exposure_var.set("Exposure: -")
        self.resolution_var.set("Resolution Score: -")
        self.overall_var.set("VisionCheck Score: -")
        self.final_var.set("FINAL QUALITY STATUS: -")

        self.final_label.config(
            fg="#1f2d3d"
        )

        self.findings_text.config(state="normal")
        self.findings_text.delete("1.0", tk.END)
        self.findings_text.insert(
            "1.0",
            "No analysis yet."
        )
        self.findings_text.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = VisionCheckGUI(root)
    root.mainloop()
