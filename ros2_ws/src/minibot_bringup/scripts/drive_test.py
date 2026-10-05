#!/usr/bin/env python3
"""Drive the robot forward for 2 s, then turn for 2 s, and check odometry moved.

    ros2 run minibot_bringup drive_test.py

Prints PASS/FAIL. Works the same in simulation and on the real robot.
In simulation it times the moves with the simulator's clock, so a slow PC still gives the same result.
"""
import math
import sys

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.parameter import Parameter

MIN_FORWARD_M = 0.2   # commanded 0.2 m/s for 2 s = 0.4 m
MIN_TURN_RAD = math.radians(45)   # commanded 1 rad/s for 2 s = about 115 deg


def yaw_from_quaternion(z, w):
    """Heading of a robot that only rotates around the vertical axis."""
    return 2 * math.atan2(z, w)


def angle_between(a, b):
    """Smallest absolute angle from a to b, in radians (0 to pi)."""
    return abs(math.atan2(math.sin(b - a), math.cos(b - a)))


def passed(dist, turn):
    return dist > MIN_FORWARD_M and turn > MIN_TURN_RAD


class DriveTest(Node):
    def __init__(self):
        super().__init__('drive_test')
        self.pub = self.create_publisher(TwistStamped, '/diff_drive_controller/cmd_vel', 10)
        self.create_subscription(Odometry, '/diff_drive_controller/odom', self.on_odom, 10)
        self.odom = None

    def on_odom(self, msg):
        self.odom = msg

    def use_sim_clock_if_simulated(self):
        """Follow /clock when a simulator publishes it; keep wall time on the real robot."""
        if self.count_publishers('/clock') == 0:
            return
        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        while self.get_clock().now().nanoseconds == 0:
            rclpy.spin_once(self, timeout_sec=0.1)

    def now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def pose(self):
        p = self.odom.pose.pose
        return p.position.x, p.position.y, yaw_from_quaternion(p.orientation.z, p.orientation.w)

    def drive(self, vx, wz, seconds):
        end = self.now() + seconds
        while self.now() < end:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist.linear.x = vx
            msg.twist.angular.z = wz
            self.pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.05)

    def wait_for_odom(self, timeout):
        end = self.now() + timeout
        while self.odom is None and self.now() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.odom is not None


def main():
    rclpy.init()
    node = DriveTest()
    if not node.wait_for_odom(30.0):
        print('FAIL: no odometry on /diff_drive_controller/odom. Is diff_drive_controller active?')
        sys.exit(1)
    node.use_sim_clock_if_simulated()
    x0, y0, _ = node.pose()
    node.drive(0.2, 0.0, 2.0)
    node.drive(0.0, 0.0, 0.5)
    x1, y1, yaw1 = node.pose()
    node.drive(0.0, 1.0, 2.0)
    node.drive(0.0, 0.0, 0.5)
    _, _, yaw2 = node.pose()
    dist = math.hypot(x1 - x0, y1 - y0)
    turn = angle_between(yaw1, yaw2)
    print(f'Forward: {dist:.2f} m (expected ~0.4)   Turn: {math.degrees(turn):.0f} deg (expected ~115)')
    ok = passed(dist, turn)
    print('PASS' if ok else 'FAIL: the robot did not move as commanded. See TROUBLESHOOTING.md')
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
