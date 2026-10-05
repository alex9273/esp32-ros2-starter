"""Start Gazebo with the Minibot, its controllers, and (optionally) RViz.

    ros2 launch minibot_bringup sim.launch.py            # Gazebo GUI + RViz
    ros2 launch minibot_bringup sim.launch.py headless:=true rviz:=false
"""
import os
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    desc_pkg = get_package_share_directory('minibot_description')
    bringup_pkg = get_package_share_directory('minibot_bringup')
    xacro_file = os.path.join(desc_pkg, 'urdf', 'minibot.urdf.xacro')
    controllers = os.path.join(bringup_pkg, 'config', 'controllers.yaml')

    headless = LaunchConfiguration('headless')
    world = LaunchConfiguration('world')

    robot_description = ParameterValue(
        # Quoted so paths with spaces (e.g. "~/My Projects/") still work
        Command(['xacro "', LaunchConfiguration('model'), '" use_sim:=true controllers_file:="', controllers, '"']),
        value_type=str)

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': PythonExpression([
            "'-r -v 2 ' + ('-s ' if '", headless, "' == 'true' else '') + '\"", world, "\"'"])}.items())

    robot_state_publisher = Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}])

    spawn = Node(
        package='ros_gz_sim', executable='create', output='screen',
        arguments=['-topic', 'robot_description', '-name', 'minibot', '-z', '0.04'])

    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'])

    joint_state_broadcaster = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster'])
    diff_drive = Node(
        package='controller_manager', executable='spawner',
        arguments=['diff_drive_controller'])

    rviz = Node(
        package='rviz2', executable='rviz2', condition=IfCondition(LaunchConfiguration('rviz')),
        arguments=['-d', os.path.join(desc_pkg, 'rviz', 'minibot.rviz')],
        parameters=[{'use_sim_time': True}])

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false', description='Run Gazebo without its GUI'),
        DeclareLaunchArgument('rviz', default_value='true', description='Open RViz'),
        DeclareLaunchArgument('model', default_value=xacro_file,
                              description='Robot model (xacro) to load, e.g. one with extra sensors'),
        DeclareLaunchArgument('world', default_value=os.path.join(bringup_pkg, 'worlds', 'arena.sdf')),
        # Make sure Gazebo can find the ros2_control plugin, whichever way ROS was installed
        AppendEnvironmentVariable('GZ_SIM_SYSTEM_PLUGIN_PATH',
                                  os.path.join(get_package_prefix('gz_ros2_control'), 'lib')),
        gazebo, clock_bridge, robot_state_publisher, spawn,
        # Controllers can only load once the robot (and its ros2_control plugin) exists in Gazebo
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[joint_state_broadcaster])),
        RegisterEventHandler(OnProcessExit(target_action=joint_state_broadcaster, on_exit=[diff_drive])),
        rviz,
    ])
