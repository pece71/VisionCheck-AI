## Inspiration

Images are central to research, photography, field documentation, datasets, and everyday communication. Blur, poor brightness, low contrast, clipped exposure, and insufficient resolution can reduce their usefulness before a user notices the problem. VisionCheck AI was created as a transparent way to check image quality before an image is accepted into a workflow.

## What it does

VisionCheck AI uses OpenCV 5 to evaluate **sharpness, brightness, contrast, exposure, and resolution**. It produces percentage scores, an overall VisionCheck Score, a descriptive quality status, and a plain-language recommendation.

The system is useful for researchers screening dataset images, photographers reviewing captures, field users working under variable conditions, and general users who want a quick technical quality check.

## Interactive Quality Control Web

A custom five-point spider-web control exposes the decision thresholds for Sharpness, Bright Level, Dark Level, Contrast, and Exposure. Dragging a point immediately re-evaluates the loaded image. This makes the same mathematical measurements adaptable to different cameras, scenes, and user goals.

The metrics are mathematically derived, while the default decision thresholds are practical empirical starting values that remain under human control.

## How we built it

VisionCheck AI was developed in Python with OpenCV 5, NumPy, Tkinter, and Pillow. Sharpness uses variance of the Laplacian, brightness uses mean grayscale intensity, contrast uses grayscale standard deviation, exposure uses clipped dark/bright pixel percentages, and resolution uses megapixel count.

The normalized overall score is:

`Q = 0.30S + 0.20B + 0.20C + 0.20E + 0.10R`

Default decision values are Sharpness 45, Dark Level 55, Bright Level 210, Contrast 45, and Exposure 50. These are not universal constants; they are visible and adjustable through the Quality Control Web.

## Dataset and evaluation

The prototype evaluation set contains **120 labeled images** across Human, Flora & Fauna, and Scenery. Each category contains 20 good-quality and 20 poor-quality images. Final reporting should include actual accuracy, precision, recall, F1 score, a confusion matrix, and representative failure cases from the batch evaluation.

## Challenges and learning

The main challenge is that image quality is context-dependent. A sunset can naturally contain bright regions, while a research image may place greater importance on fine detail. Rather than hiding one fixed threshold, VisionCheck AI exposes the decision logic and allows real-time tuning.

We learned that image quality is better explained as a combination of transparent measurements than as a single black-box number.

## Responsible use and limitations

VisionCheck AI is decision support. It does not establish scientific validity, authenticity, aesthetic merit, or suitability for every professional use. Users remain in control of the thresholds and final decision.

## What's next

Next steps include measured threshold calibration using the labeled dataset, larger and more diverse evaluation sets, verified AWS deployment, batch cloud analysis, and additional quality metrics.
