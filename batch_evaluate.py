import argparse
import csv
from pathlib import Path
import cv2
import numpy as np
import matplotlib.pyplot as plt

DEFAULTS = {"sharpness": 45, "bright": 210, "dark": 55, "contrast": 45, "exposure": 50}
VALID_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


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
    return cv2.resize(image, (target_width, int(h * scale)), interpolation=cv2.INTER_AREA)


def analyze(path, thresholds):
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError("Unreadable image")
    oh, ow = image.shape[:2]
    gray = cv2.cvtColor(resize_for_analysis(image), cv2.COLOR_BGR2GRAY)
    total = gray.size

    lap = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    sharpness = normalize_score(lap, 25, 300)
    raw_brightness = float(np.mean(gray))
    if 75 <= raw_brightness <= 190:
        brightness = 100.0
    elif raw_brightness < 75:
        brightness = max(0.0, raw_brightness / 75.0 * 100.0)
    else:
        brightness = max(0.0, 100.0 - ((raw_brightness - 190.0) / 65.0) * 100.0)
    raw_contrast = float(np.std(gray))
    contrast = normalize_score(raw_contrast, 15, 65)
    clipped = (float(np.sum(gray < 20)) + float(np.sum(gray > 235))) / total * 100.0
    exposure = max(0.0, 100.0 - clipped * 3.0)
    mp = (ow * oh) / 1_000_000.0
    resolution = 100.0 if mp >= 2 else 80.0 if mp >= 1 else 60.0 if mp >= 0.5 else 40.0
    overall = sharpness*0.30 + brightness*0.20 + contrast*0.20 + exposure*0.20 + resolution*0.10

    if sharpness < thresholds["sharpness"]:
        result = "BLURRED"
    elif raw_brightness < thresholds["dark"]:
        result = "TOO DARK"
    elif raw_brightness > thresholds["bright"]:
        result = "TOO BRIGHT"
    elif contrast < thresholds["contrast"]:
        result = "LOW CONTRAST"
    elif exposure < thresholds["exposure"]:
        result = "POOR EXPOSURE"
    elif resolution < 60:
        result = "LOW RESOLUTION"
    else:
        result = "CLEAR"

    return {
        "sharpness": sharpness, "brightness": brightness, "contrast": contrast,
        "exposure": exposure, "resolution": resolution, "overall": overall,
        "raw_brightness": raw_brightness, "raw_contrast": raw_contrast,
        "laplacian_variance": lap, "result": result,
        "predicted_binary": "Good" if result == "CLEAR" else "Bad"
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Dataset root with Category/Good and Category/Bad folders")
    parser.add_argument("--output", default="evaluation_results")
    args = parser.parse_args()

    root = Path(args.dataset)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for category_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        for actual in ("Good", "Bad"):
            label_dir = category_dir / actual
            if not label_dir.exists():
                continue
            for path in sorted(label_dir.rglob("*")):
                if path.suffix.lower() not in VALID_EXT:
                    continue
                try:
                    metrics = analyze(path, DEFAULTS)
                    rows.append({"category": category_dir.name, "actual": actual, "file": str(path), **metrics})
                except Exception as exc:
                    rows.append({"category": category_dir.name, "actual": actual, "file": str(path), "error": str(exc)})

    valid = [r for r in rows if "error" not in r]
    if not valid:
        raise SystemExit("No valid images were found.")

    fields = ["category","actual","file","result","predicted_binary","overall","sharpness","brightness","contrast","exposure","resolution","raw_brightness","raw_contrast","laplacian_variance","error"]
    with open(out / "predictions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})

    tp = sum(r["actual"] == "Good" and r["predicted_binary"] == "Good" for r in valid)
    tn = sum(r["actual"] == "Bad" and r["predicted_binary"] == "Bad" for r in valid)
    fp = sum(r["actual"] == "Bad" and r["predicted_binary"] == "Good" for r in valid)
    fn = sum(r["actual"] == "Good" and r["predicted_binary"] == "Bad" for r in valid)
    accuracy = (tp + tn) / len(valid)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    summary = (
        f"Images analyzed: {len(valid)}\n"
        f"TP={tp}, TN={tn}, FP={fp}, FN={fn}\n"
        f"Accuracy={accuracy:.4f}\nPrecision={precision:.4f}\nRecall={recall:.4f}\nF1={f1:.4f}\n"
        f"Defaults={DEFAULTS}\n"
    )
    (out / "summary.txt").write_text(summary, encoding="utf-8")
    print(summary)

    cm = np.array([[tp, fn], [fp, tn]])
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    im = ax.imshow(cm)
    ax.set_xticks([0,1], ["Pred Good", "Pred Bad"])
    ax.set_yticks([0,1], ["Actual Good", "Actual Bad"])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i,j]), ha="center", va="center")
    ax.set_title("VisionCheck AI Confusion Matrix")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out / "confusion_matrix.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    good = [r["overall"] for r in valid if r["actual"] == "Good"]
    bad = [r["overall"] for r in valid if r["actual"] == "Bad"]
    ax.hist(good, bins=12, alpha=0.6, label="Good")
    ax.hist(bad, bins=12, alpha=0.6, label="Bad")
    ax.set_xlabel("VisionCheck Score")
    ax.set_ylabel("Count")
    ax.set_title("Score Distributions")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "metric_distributions.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
