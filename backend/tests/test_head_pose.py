import unittest

from backend.app.vision.head_pose import (
    POSE_FRONT,
    POSE_LEFT_45,
    POSE_LEFT_PROFILE,
    POSE_NO_FACE,
    POSE_RIGHT_45,
    POSE_RIGHT_PROFILE,
    PoseObservation,
    classify_pose_observations,
)


class HeadPoseClassifierTests(unittest.TestCase):
    def test_no_face_when_no_observations(self) -> None:
        estimate = classify_pose_observations(None, None, None, frame_width=640)

        self.assertFalse(estimate.detected)
        self.assertEqual(estimate.pose, POSE_NO_FACE)

    def test_frontal_face_classifies_as_front(self) -> None:
        estimate = classify_pose_observations(
            PoseObservation(240, 120, 160, 160),
            None,
            None,
            frame_width=640,
        )

        self.assertTrue(estimate.detected)
        self.assertEqual(estimate.pose, POSE_FRONT)

    def test_offset_frontal_face_classifies_as_oblique(self) -> None:
        left = classify_pose_observations(
            PoseObservation(70, 120, 150, 150),
            None,
            None,
            frame_width=640,
        )
        right = classify_pose_observations(
            PoseObservation(420, 120, 150, 150),
            None,
            None,
            frame_width=640,
        )

        self.assertEqual(left.pose, POSE_LEFT_45)
        self.assertEqual(right.pose, POSE_RIGHT_45)

    def test_profile_only_classifies_as_profile(self) -> None:
        left = classify_pose_observations(
            None,
            PoseObservation(120, 120, 120, 150),
            None,
            frame_width=640,
        )
        right = classify_pose_observations(
            None,
            None,
            PoseObservation(360, 120, 120, 150),
            frame_width=640,
        )

        self.assertEqual(left.pose, POSE_LEFT_PROFILE)
        self.assertEqual(right.pose, POSE_RIGHT_PROFILE)

    def test_frontal_plus_profile_classifies_as_45_degree(self) -> None:
        left = classify_pose_observations(
            PoseObservation(240, 120, 160, 160),
            PoseObservation(230, 120, 130, 150),
            None,
            frame_width=640,
        )
        right = classify_pose_observations(
            PoseObservation(240, 120, 160, 160),
            None,
            PoseObservation(280, 120, 130, 150),
            frame_width=640,
        )

        self.assertEqual(left.pose, POSE_LEFT_45)
        self.assertEqual(right.pose, POSE_RIGHT_45)


if __name__ == "__main__":
    unittest.main()
