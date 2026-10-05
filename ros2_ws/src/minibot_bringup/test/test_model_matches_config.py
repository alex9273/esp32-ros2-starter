"""The robot model (URDF) and the controller config must describe the same robot."""
import os
import xml.etree.ElementTree as ET

import pytest
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory

DESC = get_package_share_directory('minibot_description')
BRINGUP = get_package_share_directory('minibot_bringup')
CONTROLLERS = os.path.join(BRINGUP, 'config', 'controllers.yaml')


def load_urdf(use_sim):
    doc = xacro.process_file(
        os.path.join(DESC, 'urdf', 'minibot.urdf.xacro'),
        mappings={'use_sim': use_sim, 'controllers_file': CONTROLLERS})
    return ET.fromstring(doc.toxml())


@pytest.fixture(scope='module')
def urdf():
    return load_urdf('true')


@pytest.fixture(scope='module')
def drive_params():
    with open(CONTROLLERS) as f:
        return yaml.safe_load(f)['diff_drive_controller']['ros__parameters']


def joint(urdf, name):
    found = urdf.find(f"joint[@name='{name}']")
    assert found is not None, f'joint {name} missing from the URDF'
    return found


def test_links_and_joints_exist(urdf):
    links = {link.get('name') for link in urdf.findall('link')}
    assert {'base_link', 'base_footprint', 'chassis', 'caster', 'left_wheel', 'right_wheel'} <= links
    for name in ('left_wheel_joint', 'right_wheel_joint'):
        assert joint(urdf, name).get('type') == 'continuous'


def test_wheel_radius_matches(urdf, drive_params):
    for side in ('left', 'right'):
        cyl = urdf.find(f"link[@name='{side}_wheel']/collision/geometry/cylinder")
        assert float(cyl.get('radius')) == pytest.approx(drive_params['wheel_radius'])


def test_wheel_separation_matches(urdf, drive_params):
    y = [float(joint(urdf, f'{s}_wheel_joint').find('origin').get('xyz').split()[1]) for s in ('left', 'right')]
    assert y[0] > 0 > y[1], 'left wheel must be on +y, right wheel on -y'
    assert y[0] - y[1] == pytest.approx(drive_params['wheel_separation'])


def test_controller_wheels_are_ros2_control_joints(urdf, drive_params):
    controlled = {j.get('name') for j in urdf.findall('ros2_control/joint')}
    assert set(drive_params['left_wheel_names'] + drive_params['right_wheel_names']) == controlled
    for j in urdf.findall('ros2_control/joint'):
        assert j.find("command_interface[@name='velocity']") is not None


def test_sim_uses_gazebo_plugin(urdf):
    assert urdf.find('ros2_control/hardware/plugin').text == 'gz_ros2_control/GazeboSimSystem'
    assert urdf.find('gazebo/plugin/parameters').text == CONTROLLERS


def test_real_robot_uses_placeholder():
    real = load_urdf('false')
    assert real.find('ros2_control/hardware/plugin').text == 'mock_components/GenericSystem'
    assert real.find('gazebo/plugin') is None


def test_masses_and_inertias_are_positive(urdf):
    for link in urdf.findall('link'):
        inertial = link.find('inertial')
        if inertial is None:
            continue
        assert float(inertial.find('mass').get('value')) > 0, link.get('name')
        inertia = inertial.find('inertia')
        for axis in ('ixx', 'iyy', 'izz'):
            assert float(inertia.get(axis)) > 0, f"{link.get('name')} {axis}"
