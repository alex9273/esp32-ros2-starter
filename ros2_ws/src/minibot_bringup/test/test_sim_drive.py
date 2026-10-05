"""End-to-end: start the headless simulator and check the robot drives (drive_test.py prints PASS).

The model and world are copied into a folder whose name has a space, so this also checks that
sim.launch.py works from paths like "~/Side project/".
"""
import os
import shutil
import signal
import sys
import tempfile
import unittest

import launch
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch.actions import ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource

TEST_DIR = tempfile.mkdtemp(prefix='minibot_test_')


@pytest.mark.launch_test
def generate_test_description():
    desc = get_package_share_directory('minibot_description')
    bringup = get_package_share_directory('minibot_bringup')
    spaced = os.path.join(TEST_DIR, 'folder with spaces')
    os.makedirs(spaced)
    model = shutil.copy(os.path.join(desc, 'urdf', 'minibot.urdf.xacro'), spaced)
    world = shutil.copy(os.path.join(bringup, 'worlds', 'arena.sdf'), spaced)

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', 'sim.launch.py')),
        launch_arguments={'headless': 'true', 'rviz': 'false', 'model': model, 'world': world}.items())
    drive_test = ExecuteProcess(
        cmd=[sys.executable, os.path.join(get_package_prefix('minibot_bringup'),
                                          'lib', 'minibot_bringup', 'drive_test.py')],
        output='screen')
    return launch.LaunchDescription([
        # Keep this Gazebo separate from any other simulation running on the machine
        launch.actions.SetEnvironmentVariable('GZ_PARTITION', os.path.basename(TEST_DIR)),
        sim,
        # drive_test.py waits up to 30 s for the controllers; give Gazebo a head start
        TimerAction(period=5.0, actions=[drive_test]),
        launch_testing.actions.ReadyToTest(),
    ]), {'drive_test': drive_test}


class TestDrive(unittest.TestCase):
    def test_drive_test_finishes(self, proc_info, drive_test):
        proc_info.assertWaitForShutdown(process=drive_test, timeout=120)


def kill_leftover_gazebo(test_dir):
    """The Gazebo server can outlive the launch (it runs under a ruby wrapper); stop the one we started."""
    for pid in filter(str.isdigit, os.listdir('/proc')):
        try:
            with open(f'/proc/{pid}/cmdline', 'rb') as f:
                if test_dir.encode() in f.read():
                    os.kill(int(pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass


@launch_testing.post_shutdown_test()
class TestDriveResult(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        kill_leftover_gazebo(TEST_DIR)

    def test_drive_test_passed(self, proc_info, proc_output, drive_test):
        launch_testing.asserts.assertExitCodes(proc_info, process=drive_test)
        launch_testing.asserts.assertInStdout(proc_output, 'PASS', drive_test)
