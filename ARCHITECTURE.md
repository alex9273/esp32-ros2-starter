# Minibot architecture

This is the architecture plan for Kit 1. It covers what the kit is made of, how the parts talk to each other, what is built today and what comes later, and why it is built this way.

## 1. Goal

A two-wheel robot that runs the **same ROS 2 stack** in three places:

| Stage | Where it runs | What drives the wheels | Status |
|---|---|---|---|
| 1 | Gazebo simulation | Gazebo physics | Built, tested |
| 2 | Gazebo simulation + lidar, mapping, navigation | Gazebo physics | Planned next |
| 3 | Real robot | ESP32 + motor driver + encoder motors | When Alex has hardware |

The key rule is that only the bottom layer changes between simulation and the real robot. Controllers, launch files, odometry, mapping and navigation stay identical. That is what makes the kit worth paying for: you can develop in sim and move to hardware without rewriting anything.

## 2. Layers

```
 ┌──────────────────────────────────────────────────────────────┐
 │  YOU / APPS        teleop keyboard · drive_test.py · Nav2 (2) │
 └───────────────▲───────────────────────────┬──────────────────┘
                 │ /diff_drive_controller/odom│ /diff_drive_controller/cmd_vel
                 │ /tf  (odom → base_link)    ▼ (TwistStamped)
 ┌──────────────────────────────────────────────────────────────┐
 │  CONTROL        controller_manager (ros2_control)            │
 │                 ├─ diff_drive_controller   cmd_vel → wheel   │
 │                 │                          speeds; odometry  │
 │                 └─ joint_state_broadcaster → /joint_states   │
 └───────────────▲───────────────────────────┬──────────────────┘
                 │ wheel position/velocity    │ wheel velocity commands
                 │ (state interfaces)         ▼ (command interfaces)
 ┌──────────────────────────────────────────────────────────────┐
 │  HARDWARE LAYER (the only part that changes)                 │
 │   sim:  gz_ros2_control/GazeboSimSystem   (Stage 1-2)        │
 │   real: minibot_hardware/ESP32System      (Stage 3)          │
 └───────────────▲───────────────────────────┬──────────────────┘
                 │                            │
          Gazebo physics               micro-ROS over USB serial
                                              ▼
                                ┌───────────────────────────────┐
                                │ ESP32 firmware (Stage 3)      │
                                │  PWM motors · read encoders   │
                                │  per-wheel PID · watchdog     │
                                └───────────────────────────────┘
```

Alongside these, `robot_state_publisher` turns the robot model (URDF) plus `/joint_states` into the `/tf` tree, and RViz shows it.

## 3. Packages

| Package | Contains | Stage |
|---|---|---|
| `minibot_description` | URDF/xacro robot model, inertia helpers, ros2_control block, RViz config, model viewer launch | 1 |
| `minibot_bringup` | Controller config, Gazebo world, `sim.launch.py`, `drive_test.py` | 1 |
| `minibot_navigation` | Lidar in the model, slam_toolbox config, Nav2 params, map/nav launch files | 2 |
| `minibot_hardware` | C++ ros2_control `SystemInterface` that talks to the ESP32 | 3 |
| `firmware/` (PlatformIO, not a ROS package) | ESP32 micro-ROS firmware | 3 |

## 4. Interfaces (the contract between layers)

**Topics (public, same in sim and hardware)**

| Topic | Type | Direction |
|---|---|---|
| `/diff_drive_controller/cmd_vel` | `geometry_msgs/TwistStamped` | in |
| `/diff_drive_controller/odom` | `nav_msgs/Odometry` | out |
| `/joint_states` | `sensor_msgs/JointState` | out |
| `/tf` | `odom → base_link → wheels, chassis, caster` | out |
| `/scan` (Stage 2) | `sensor_msgs/LaserScan` | out |

**ros2_control joints:** `left_wheel_joint`, `right_wheel_joint`, each with a `velocity` command interface (rad/s, limited to ±15) and `position` + `velocity` state interfaces.

**Frames:** `odom` (from wheel odometry) → `base_link` (midpoint between the wheels, at axle height) → `base_footprint` (on the ground, for Nav2). Stage 2 adds `map → odom` from slam_toolbox.

**ESP32 link (Stage 3, planned):** micro-ROS over USB serial at 115200 baud via the micro-ROS agent.
- ESP32 subscribes `/minibot/wheel_cmd` (`std_msgs/Float32MultiArray`, `[left, right]` rad/s).
- ESP32 publishes `/minibot/wheel_state` (`sensor_msgs/JointState`, position + velocity, 50 Hz).
- Watchdog: if no command arrives for 300 ms, the ESP32 stops the motors on its own.

## 5. Key design decisions

1. **ros2_control instead of a hand-written cmd_vel node.** It is the standard in ROS 2, gives odometry, velocity limits and timeouts for free, and is what lets sim and hardware share everything above the hardware layer.
2. **ESP32 does low-level only (PWM, encoders, wheel PID).** Odometry and kinematics stay on the computer in diff_drive_controller. This keeps the firmware small and robot dimensions in one place (the config), not compiled into the microcontroller.
3. **micro-ROS rather than a custom serial protocol.** It is the thing people struggle with and search for, so it is the selling point. The cost is the extra agent process; the kit ships a one-command way to start it.
4. **Robot dimensions as named parameters at the top of the URDF and in `controllers.yaml`.** Users edit two places, both documented. (Possible later improvement: generate one from the other.)
5. **Jazzy + Gazebo Harmonic only.** These are the current LTS versions. Supporting older ROS versions would multiply testing work for little gain.
6. **A PASS/FAIL drive test that works in sim and on hardware.** It gives buyers a quick way to know their setup works and is the first thing support asks for.

## 6. Free vs paid split

| | Free (public GitHub repo) | Paid kit |
|---|---|---|
| Stage 1 sim robot + drive test | ✓ | ✓ |
| README, troubleshooting | ✓ | ✓ (extended) |
| Stage 2 lidar, mapping, navigation | | ✓ |
| Stage 3 ESP32 firmware + hardware interface, wiring, parts list | | ✓ |

The free repo is the marketing: it solves a real problem on its own and its README links to the paid kit.

## 7. Testing

- **Every change:** build with colcon, launch headless, run `drive_test.py` (must print PASS).
- **Stage 2:** scripted Nav2 goal in the arena must succeed.
- **Stage 3:** same drive test on the real robot, plus a bench test of the firmware watchdog.
- **Later (optional):** a GitHub Actions job that runs the headless test on every push to the public repo, so buyers see a green badge.

## 8. Known limits today

- Tested headless only. The Gazebo window and RViz have not been tried on a desktop yet.
- Tested with ROS installed from RoboStack (conda), not yet with the standard apt install the README describes.
- The `use_sim:=false` path uses a mock placeholder until `minibot_hardware` exists.
