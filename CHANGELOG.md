# Changelog

## 0.1.1 (2026-10-05)
- Fix: `sim.launch.py` and `display.launch.py` failed when the workspace path contained a space (e.g. `~/Side project/`).
- `drive_test.py` times its moves with the simulator clock, so a slow PC no longer gives a false FAIL.
- Automated tests (`colcon test`): URDF and `controllers.yaml` agree on wheel size and spacing, drive test maths, and a headless Gazebo run of the drive test from a folder with spaces.
- GitHub Actions CI builds and tests every push.
- Demo GIF in the README.

## 0.1.0 (2026-10-05)
- Robot model (URDF/xacro) with configurable dimensions.
- Gazebo Harmonic arena world and `sim.launch.py` (GUI or headless).
- ros2_control with diff_drive_controller and joint_state_broadcaster.
- `drive_test.py` PASS/FAIL check.
- README, troubleshooting, beginner guide, customization guide.
