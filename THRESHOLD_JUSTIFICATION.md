# VisionCheck AI — Threshold Justification

VisionCheck AI separates **mathematical measurements** from **decision thresholds**.

## Mathematical measurements

- **Sharpness:** variance of the Laplacian, `V = Var(Laplacian(Igray))`. The raw value is normalized from 25–300 to a 0–100 sharpness score.
- **Brightness:** mean grayscale intensity, `mu = (1/N) sum(Ii)`. A mean level of 75–190 receives a full brightness score; values outside this band are penalized.
- **Contrast:** grayscale standard deviation, `sigma = sqrt[(1/N) sum((Ii-mu)^2)]`, normalized from 15–65 to a 0–100 score.
- **Exposure:** percentage of very dark (`I < 20`) and very bright (`I > 235`) pixels. `Exposure = max(0, 100 - 3*pclip)`.
- **Resolution:** megapixels `MP = W*H/1e6`, mapped to 100 (>=2 MP), 80 (>=1 MP), 60 (>=0.5 MP), or 40 (<0.5 MP).

The overall score is:

`Q = 0.30*Sharpness + 0.20*Brightness + 0.20*Contrast + 0.20*Exposure + 0.10*Resolution`

## Default decision thresholds

| Parameter | Default | Meaning |
|---|---:|---|
| Sharpness score | 45 | Below this, flag possible blur/loss of detail |
| Dark level | 55 | Mean grayscale below this, flag TOO DARK |
| Bright level | 210 | Mean grayscale above this, flag TOO BRIGHT |
| Contrast score | 45 | Below this, flag LOW CONTRAST |
| Exposure score | 50 | Below this, flag POOR EXPOSURE |

These values are **empirical engineering defaults**, not universal theoretical constants. They are intentionally exposed through the Interactive Quality Control Web so users can adapt the decision logic to different cameras, subjects, lighting conditions, and use cases.

The 120-image labeled evaluation set should be used to calibrate and validate these defaults before reporting final performance.
