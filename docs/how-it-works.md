# How it works (beginner guide)

This page explains what happens when you run `ros2 launch minibot_bringup sim.launch.py`, one piece at a time. For the full design, see `../ARCHITECTURE.md`.

## 1. The robot model
`minibot_description/urdf/minibot.urdf.xacro` describes the robot: a box chassis, two driven wheels and a caster ball at the back. Every size is a named value at the top of the file, so you change numbers, not geometry.

The model also has a `<ros2_control>` block. It tells ROS which joints can be driven (the two wheels), how (by velocity), and what can be read back (position and velocity).

## 2. Gazebo
Gazebo is the physics simulator. The launch file starts it with `worlds/arena.sdf`, a 3 m x 3 m room with walls, then spawns the robot into it. A Gazebo plugin (`gz_ros2_control`) runs the ROS controllers inside the simulation and applies wheel speeds to the simulated motors.

## 3. The controllers
Two controllers are loaded from `config/controllers.yaml`:
- **diff_drive_controller** takes a velocity command ("go forward 0.2 m/s, turn 1 rad/s"), works out each wheel's speed, and measures how far the robot actually moved (odometry).
- **joint_state_broadcaster** publishes the wheel angles on `/joint_states`.

They start in order: only after the robot exists in Gazebo, and the drive controller only after the broadcaster.

## 4. Where the robot is
`robot_state_publisher` combines the model with `/joint_states` to publish the position of every part on `/tf`. The drive controller adds where the robot is in the world (`odom → base_link`). RViz draws all of this.

## 5. Moving it
Anything that publishes a `TwistStamped` to `/diff_drive_controller/cmd_vel` drives the robot: the keyboard teleop, the drive test, and later Nav2. If commands stop for 0.5 s the robot stops, which is a safety feature.

## 6. On the real robot (coming in a later version)
Only step 2 changes: instead of Gazebo, an ESP32 microcontroller spins the real motors and reads the encoders, and talks to ROS through micro-ROS. Steps 1, 3, 4 and 5 stay exactly the same.
