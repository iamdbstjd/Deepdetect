from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def draw_target_chart(output: Path) -> None:
    width, height = 1100, 620
    margin_left, margin_right = 110, 56
    margin_top, margin_bottom = 112, 112
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    image = np.full((height, width, 3), 255, dtype=np.uint8)

    labels = [
        "Pretrained\nbaseline",
        "Data\ncuration",
        "Fine-tune\nround 1",
        "Hard-case\nQA",
        "Target\nrelease",
    ]
    values = [70.0, 76.0, 83.0, 88.0, 91.0]

    axis_color = (55, 65, 81)
    grid_color = (226, 232, 240)
    line_color = (114, 124, 12)
    point_color = (88, 95, 7)
    fill_color = (231, 246, 242)

    cv2.putText(
        image,
        "YOLO fine-tuning target roadmap",
        (margin_left, 42),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (20, 32, 43),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        "Planned target curve: baseline 70% to release target 91% (not completed training results)",
        (margin_left, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.44,
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

    step = plot_width / (len(values) - 1)
    points: list[tuple[int, int]] = []
    for index, value in enumerate(values):
        x = margin_left + int(round(step * index))
        y = margin_top + plot_height - int(round(plot_height * value / 100))
        points.append((x, y))

    polygon = np.array(
        points
        + [
            (points[-1][0], margin_top + plot_height),
            (points[0][0], margin_top + plot_height),
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(image, [polygon], fill_color)

    for left, right in zip(points, points[1:]):
        cv2.line(image, left, right, line_color, 4, cv2.LINE_AA)

    for (x, y), label, value in zip(points, labels, values):
        cv2.circle(image, (x, y), 9, point_color, -1, cv2.LINE_AA)
        cv2.circle(image, (x, y), 14, (213, 245, 239), 3, cv2.LINE_AA)
        cv2.putText(
            image,
            f"{value:.0f}%",
            (x - 28, y - 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.54,
            (20, 32, 43),
            1,
            cv2.LINE_AA,
        )
        for row, text in enumerate(label.split("\n")):
            cv2.putText(
                image,
                text,
                (x - 52, margin_top + plot_height + 36 + row * 20),
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
    output = Path("samples/reports/fine_tuning_target_roadmap.png")
    draw_target_chart(output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
