"""Unit tests for the maths in scripts/drive_test.py."""
import importlib.util
import math
import os

import pytest

spec = importlib.util.spec_from_file_location(
    'drive_test', os.path.join(os.path.dirname(__file__), '..', 'scripts', 'drive_test.py'))
drive_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drive_test)


@pytest.mark.parametrize('yaw', [0.0, 0.5, -1.2, 3.0, -3.0])
def test_yaw_from_quaternion(yaw):
    got = drive_test.yaw_from_quaternion(math.sin(yaw / 2), math.cos(yaw / 2))
    assert drive_test.angle_between(got, yaw) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize('a, b, expected', [
    (0.0, 2.0, 2.0),
    (2.0, 0.0, 2.0),
    (3.0, -3.0, 2 * math.pi - 6.0),   # crossing +-180 deg takes the short way round
    (-math.pi / 2, math.pi / 2, math.pi),
])
def test_angle_between(a, b, expected):
    assert drive_test.angle_between(a, b) == pytest.approx(expected)


def test_pass_thresholds():
    assert drive_test.passed(0.40, math.radians(115))
    assert not drive_test.passed(0.10, math.radians(115))
    assert not drive_test.passed(0.40, math.radians(10))
