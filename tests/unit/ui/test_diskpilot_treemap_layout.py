"""Algorithme de treemap squarifié (section 11) : fonction pure, testable sans Qt."""

from __future__ import annotations

from nexusdesk.ui.pages.diskpilot.treemap_widget import squarify


def _rects_overlap(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return False
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def test_rectangle_areas_sum_to_the_container_area() -> None:
    values = [500.0, 300.0, 100.0, 80.0, 20.0]
    rects = squarify(values, 0.0, 0.0, 100.0, 50.0)

    total_area = sum(w * h for _x, _y, w, h in rects)
    assert abs(total_area - 100.0 * 50.0) < 1e-6


def test_rectangles_never_overlap() -> None:
    values = [800.0, 400.0, 200.0, 150.0, 90.0, 60.0, 40.0, 10.0]
    rects = squarify(values, 0.0, 0.0, 120.0, 80.0)

    for i, rect_a in enumerate(rects):
        for rect_b in rects[i + 1 :]:
            assert not _rects_overlap(rect_a, rect_b)


def test_rectangles_stay_within_the_container_bounds() -> None:
    values = [300.0, 200.0, 100.0]
    container_x, container_y, container_w, container_h = 10.0, 5.0, 90.0, 60.0
    rects = squarify(values, container_x, container_y, container_w, container_h)

    for x, y, w, h in rects:
        assert x >= container_x - 1e-6
        assert y >= container_y - 1e-6
        assert x + w <= container_x + container_w + 1e-6
        assert y + h <= container_y + container_h + 1e-6


def test_empty_values_returns_empty_list() -> None:
    assert squarify([], 0.0, 0.0, 100.0, 100.0) == []


def test_all_zero_values_returns_degenerate_rects_without_crashing() -> None:
    rects = squarify([0.0, 0.0, 0.0], 0.0, 0.0, 100.0, 100.0)

    assert len(rects) == 3
    assert all(w == 0.0 and h == 0.0 for _x, _y, w, h in rects)


def test_single_value_fills_the_whole_container() -> None:
    rects = squarify([42.0], 0.0, 0.0, 10.0, 20.0)

    assert len(rects) == 1
    x, y, w, h = rects[0]
    assert (x, y, w, h) == (0.0, 0.0, 10.0, 20.0)
