# Troubleshooting

### Spawners print "waiting for service /controller_manager/list_controllers" forever
Gazebo could not load the ros2_control plugin, so no controller manager exists. Look higher in the log for
`Failed to load system plugin [gz_ros2_control-system] : Could not find shared library`.
- Install it: `sudo apt install ros-jazzy-gz-ros2-control`.
- `sim.launch.py` already adds its `lib` folder to `GZ_SIM_SYSTEM_PLUGIN_PATH`. If you wrote your own launch file, do the same.

### Teleop runs but the robot doesn't move
In Jazzy, `diff_drive_controller` only accepts `TwistStamped`. Start teleop with `-p stamped:=true` and remap to
`/diff_drive_controller/cmd_vel` (see README). Check with `ros2 topic info /diff_drive_controller/cmd_vel -v`.

### Robot moves for half a second, then stops
`cmd_vel_timeout` (0.5 s) stops the robot when commands stop arriving. Your command source must publish continuously.

### Robot turns when it should go straight, or odometry drifts badly
Wheel radius or wheel separation differ between the URDF and `controllers.yaml`. They must match each other and the real robot.

### Odometry moves but the robot in Gazebo doesn't (or the reverse)
Check `ros2 control list_hardware_interfaces`: both wheel joints need a claimed `velocity` command interface.
Check `use_sim_time` is true for every node in simulation; otherwise TF timestamps don't match.

### `xacro` errors about `controllers_file`
Launch through `sim.launch.py`, which passes the path to the controller config. To inspect the URDF by hand:
`xacro minibot.urdf.xacro use_sim:=false`.

### Gazebo window is black or crashes in a VM
Use `headless:=true` (server only) and view the robot in RViz instead, or try `export LIBGL_ALWAYS_SOFTWARE=1`.
