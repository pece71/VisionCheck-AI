# VisionCheck AI

**Interactive image-quality assessment for researchers, photographers, field users, and everyday users.**

VisionCheck AI is a Python/OpenCV 5 desktop application that measures sharpness, brightness, contrast, exposure, and resolution; produces an overall VisionCheck Score; and returns a descriptive status such as CLEAR, BLURRED, TOO DARK, TOO BRIGHT, LOW CONTRAST, POOR EXPOSURE, or LOW RESOLUTION.

## Why it is useful

- **Researchers:** screen images before annotation, dataset inclusion, reporting, or analysis.
- **Photographers:** quickly flag blur, poor exposure, and low contrast before editing or sharing.
- **Field/agricultural users:** check outdoor captures affected by motion, lighting, or distance.
- **General users:** receive plain-language image-quality feedback.

## Interactive Quality Control Web

The five-point web exposes the decision thresholds for Sharpness, Bright Level, Dark Level, Contrast, and Exposure. Dragging a blue point immediately re-runs the current image analysis. `Reset Defaults` restores the starting values.

The image-quality **metrics are mathematical**. The default **decision thresholds are empirical starting values** and are user-adjustable. See `THRESHOLD_JUSTIFICATION.md`.

## Run locally

```bash
pip install -r requirements.txt
python visioncheck_gui_v5.py
```

## Testing workflow

1. Click **Select Image**.
2. Review the five percentage scores and overall VisionCheck Score.
3. Review the descriptive quality status and recommendation.
4. Drag one node on the Interactive Quality Control Web and confirm the result updates immediately.
5. Click **Reset Defaults**.
6. Select another image with a different quality condition.

## Evaluation dataset

Prototype evaluation uses 120 labeled images:

- Human: 20 good + 20 poor
- Flora & Fauna: 20 good + 20 poor
- Scenery: 20 good + 20 poor

Run `batch_evaluate.py` to generate measured evaluation evidence. Do not report performance until the batch results are produced.

## AWS path

The package includes an AWS deployment scaffold for API Gateway -> Lambda container (OpenCV 5) -> optional S3/CloudWatch. The endpoint should be deployed and verified before being claimed as working.
