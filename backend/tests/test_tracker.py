import unittest

from backend.app.vision.detections import Detection
from backend.app.vision.tracker import DetectionTracker, iou


class DetectionTrackerTests(unittest.TestCase):
    def test_iou(self) -> None:
        left = Detection("face", 0, 0, 20, 20, 1.0)
        right = Detection("face", 10, 10, 30, 30, 1.0)
        self.assertAlmostEqual(iou(left, right), 100 / 700)

    def test_smooths_matching_detection(self) -> None:
        tracker = DetectionTracker(iou_threshold=0.1, smoothing_alpha=0.5, max_missing=1)

        first = tracker.update([Detection("face", 10, 10, 30, 30, 1.0)])
        second = tracker.update([Detection("face", 14, 10, 34, 30, 1.0)])

        self.assertEqual(first[0].track_id, second[0].track_id)
        self.assertEqual(second[0].x1, 12)
        self.assertTrue(second[0].observed)

    def test_retains_missing_track_briefly(self) -> None:
        tracker = DetectionTracker(iou_threshold=0.1, smoothing_alpha=0.5, max_missing=1)

        first = tracker.update([Detection("face", 10, 10, 30, 30, 1.0)])
        missing = tracker.update([])
        gone = tracker.update([])

        self.assertEqual(first[0].track_id, missing[0].track_id)
        self.assertFalse(missing[0].observed)
        self.assertEqual(missing[0].missed, 1)
        self.assertEqual(gone, [])


if __name__ == "__main__":
    unittest.main()
