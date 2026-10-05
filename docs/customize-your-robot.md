# Make it match your robot

The default Minibot has 65 mm wheels, 17 cm between the wheel centres, and a 20 x 15 cm chassis. To use your own dimensions:

## 1. Measure
- **Wheel radius:** wheel diameter / 2, in metres (65 mm wheel → 0.0325).
- **Wheel separation:** distance between the **centres** of the two wheels, in metres.
- Chassis length, width and height (only affect how it looks and collides).

## 2. Edit two files (they must agree)
`minibot_description/urdf/minibot.urdf.xacro`, at the top:
```xml
<xacro:property name="wheel_radius" value="0.0325"/>
<xacro:property name="wheel_separation" value="0.17"/>
```
`minibot_bringup/config/controllers.yaml`:
```yaml
wheel_separation: 0.17
wheel_radius: 0.0325
```

## 3. Rebuild and test
```bash
colcon build --symlink-install && source install/setup.bash
ros2 launch minibot_bringup sim.launch.py
ros2 run minibot_bringup drive_test.py   # in a second terminal
```
The test commands 0.4 m forward and about 115° of turning. Readings within roughly 10% mean the numbers are consistent.

## 4. Speed limits
In `controllers.yaml`, `linear.x.max_velocity` (m/s) and `angular.z.max_velocity` (rad/s) cap how fast the robot can go. They start low on purpose. Raise them once the robot behaves.

## 5. Other changes
- **Different world:** `ros2 launch minibot_bringup sim.launch.py world:=/path/to/your.sdf`
- **Caster position or size:** `caster_radius` and the caster joint in the URDF.
- **Mass:** `chassis_mass` and `wheel_mass`. Keep them realistic or the simulation behaves oddly.
