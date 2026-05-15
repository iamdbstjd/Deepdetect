# Akiyo Sample QA

Source: Xiph.org Derf test media `akiyo` CIF, 300 frames.

Generated artifacts:
- Input clip: `samples/videos/akiyo_short.mp4`
- Reference image: `samples/references/akiyo_reference.jpg`
- Blur output: `samples/outputs/akiyo_blur.mp4`
- Preserve output: `samples/outputs/akiyo_preserve.mp4`
- Character output: `samples/outputs/akiyo_character.mp4`
- Contact sheet: `samples/reports/akiyo_contact_sheet.jpg`

Preparation result:
- Frames prepared: 90
- Resolution: 352 x 288
- FPS: 29.970
- Detector: `YoloRegionDetector`
- Face detection frames: 90 / 90
- Reference selection: YOLO face crop

Blur mode result:
- Frames processed: 90
- Raw detections: 90
- Tracked detections: 90
- Retained missing detections: 0
- Effective processing speed: 37.81 FPS on this machine
- Average face-region sharpness reduction: 98.05%
- Minimum face-region sharpness reduction: 95.35%

Preserve mode result:
- Frames processed: 90
- Raw detections: 90
- Tracked detections: 90
- Preserved reference faces: 90
- Retained missing detections: 0
- Effective processing speed: 3.59 FPS on this machine

Character mode result:
- Frames processed: 90
- Raw detections: 90
- Tracked detections: 90
- Character overlays: 90
- Retained missing detections: 0
- Effective processing speed: 3.50 FPS on this machine

Identity score diagnostics:
- Threshold: 0.35
- Sampled face detections: 30
- Matches at threshold: 30 / 30
- Min score: 0.540
- Median score: 0.632
- Max score: 0.730

Manual visual check:
- Blur mode makes the visible face non-identifiable in the sampled frames.
- Preserve mode keeps the reference face unblurred across the sampled frames.
- Character mode places the default glossy emoji consistently on the face position without stretching it to the face box.
- No number plate is present in this sample, so plate blur still needs a separate traffic/car sample.

Next tuning target:
- Add a second sample with non-reference bystanders and a visible license plate.
- Use the current Akiyo run as the single-reference stability baseline.
