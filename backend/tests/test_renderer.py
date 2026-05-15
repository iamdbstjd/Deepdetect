import unittest

import numpy as np

from backend.app.vision.detections import Detection
from backend.app.vision.renderer import OverlayInstruction, PrivacyRenderer


class PrivacyRendererTests(unittest.TestCase):
    def test_blurs_detected_region(self) -> None:
        frame = np.zeros((80, 80, 3), dtype=np.uint8)
        frame[:, :40] = (0, 0, 0)
        frame[:, 40:] = (255, 255, 255)
        detection = Detection(
            kind="face",
            x1=30,
            y1=10,
            x2=50,
            y2=70,
            confidence=1.0,
        )

        output = PrivacyRenderer(face_padding=0.0).render(frame, [detection])

        self.assertFalse(np.array_equal(frame[10:70, 30:50], output[10:70, 30:50]))
        self.assertTrue(np.array_equal(frame[0:5, 0:5], output[0:5, 0:5]))

    def test_overlays_character_region(self) -> None:
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        overlay = np.zeros((32, 32, 4), dtype=np.uint8)
        overlay[:, :, :3] = (0, 255, 255)
        overlay[:, :, 3] = 255
        detection = Detection(
            kind="face",
            x1=16,
            y1=16,
            x2=48,
            y2=48,
            confidence=1.0,
        )

        output = PrivacyRenderer(face_padding=0.0).render(
            frame,
            [],
            [OverlayInstruction(detection=detection, image=overlay)],
        )

        self.assertTrue(np.all(output[20:44, 20:44] == (0, 255, 255)))
        self.assertTrue(np.all(output[0:8, 0:8] == 0))

    def test_overlays_character_without_stretching_aspect_ratio(self) -> None:
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        overlay = np.zeros((20, 20, 4), dtype=np.uint8)
        overlay[:, :, :3] = (0, 255, 255)
        overlay[:, :, 3] = 255
        detection = Detection(
            kind="face",
            x1=45,
            y1=30,
            x2=55,
            y2=70,
            confidence=1.0,
        )

        output = PrivacyRenderer(face_padding=0.0).render(
            frame,
            [],
            [OverlayInstruction(detection=detection, image=overlay)],
        )
        colored_pixels = np.argwhere(np.any(output != 0, axis=2))
        y1, x1 = colored_pixels.min(axis=0)
        y2, x2 = colored_pixels.max(axis=0) + 1

        self.assertEqual((x1, y1, x2, y2), (30, 30, 70, 70))
        self.assertEqual(x2 - x1, y2 - y1)


if __name__ == "__main__":
    unittest.main()
