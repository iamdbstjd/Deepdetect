from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def draw_chart(labels: list[str], values: list[float], output: Path) -> None:
    width, height = 1100, 620
    margin_left, margin_right = 110, 56
    margin_top, margin_bottom = 112, 106
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    image = np.full((height, width, 3), 255, dtype=np.uint8)

    axis_color = (55, 65, 81)
    grid_color = (226, 232, 240)
    line_color = (114, 124, 12)
    point_color = (88, 95, 7)

    cv2.putText(
        image,
        "deepdetect sample QA metrics",
        (margin_left, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.95,
        (20, 32, 43),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        "Measured on the Akiyo 90-frame sample, not a training curve",
        (margin_left, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.43,
        (103, 116, 132),
        1,
        cv2.LINE_AA,
    )

    for tick in range(0, 101, 20):
        y = margin_top + plot_height - int(plot_height * tick / 100)
        cv2.line(image, (margin_left, y), (width - margin_right, y), grid_color, 1)
        cv2.putText(
            image,
            f"{tick}%",
            (35, y + 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            axis_color,
            1,
            cv2.LINE_AA,
        )

    cv2.line(
        image,
        (margin_left, margin_top),
        (margin_left, margin_top + plot_height),
        axis_color,
        2,
    )
    cv2.line(
        image,
        (margin_left, margin_top + plot_height),
        (width - margin_right, margin_top + plot_height),
        axis_color,
        2,
    )

    step = plot_width / max(1, len(labels) - 1)
    points: list[tuple[int, int]] = []
    for index, value in enumerate(values):
        x = margin_left + int(round(step * index))
        y = margin_top + plot_height - int(round(plot_height * value / 100))
        points.append((x, y))

    for left, right in zip(points, points[1:]):
        cv2.line(image, left, right, line_color, 4, cv2.LINE_AA)

    for (x, y), label, value in zip(points, labels, values):
        cv2.circle(image, (x, y), 9, point_color, -1, cv2.LINE_AA)
        cv2.circle(image, (x, y), 14, (213, 245, 239), 3, cv2.LINE_AA)
        value_y = y + 32 if value > 88 else y - 24
        cv2.putText(
            image,
            f"{value:.1f}%",
            (x - 34, value_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (20, 32, 43),
            1,
            cv2.LINE_AA,
        )
        for row, text in enumerate(label.split("\\n")):
            cv2.putText(
                image,
                text,
                (x - 54, margin_top + plot_height + 34 + row * 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.43,
                axis_color,
                1,
                cv2.LINE_AA,
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), image):
        raise RuntimeError(f"cannot write chart: {output}")


def main() -> int:
    blur = load_json(Path("samples/reports/akiyo_blur.json"))
    preserve = load_json(Path("samples/reports/akiyo_preserve.json"))
    character = load_json(Path("samples/reports/akiyo_character.json"))
    blur_quality = load_json(Path("samples/reports/akiyo_blur_quality.json"))

    frames = blur["stats"]["frames"]
    blur_coverage = (blur["stats"]["detections"] / frames) * 100
    preserve_success = (preserve["stats"]["preserved_faces"] / frames) * 100
    character_success = (character["stats"]["overlaid_faces"] / frames) * 100
    sharpness_reduction = blur_quality["average_sharpness_reduction"] * 100

    draw_chart(
        labels=[
            "No privacy\\nprocessing",
            "YOLO face\\ncoverage",
            "Blur strength\\nreduction",
            "Preserve\\nsuccess",
            "Character\\noverlay",
        ],
        values=[0.0, blur_coverage, sharpness_reduction, preserve_success, character_success],
        output=Path("samples/reports/performance_trend.png"),
    )
    print("samples/reports/performance_trend.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
