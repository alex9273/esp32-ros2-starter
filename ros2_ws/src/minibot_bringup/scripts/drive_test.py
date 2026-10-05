#!/usr/bin/env python3
"""Drive the robot forward for 2 s, then turn for 2 s, and check odometry moved.

    ros2 run minibot_bringup drive_test.py

Prints PASS/FAIL. Works the same in simulation and on the real robot.
"""
import math
import sys
import time

import rclpy
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node


class DriveTest(Node):
    def __init__(self):
        super().__init__('drive_test')
        self.pub = self.create_publisher(TwistStamped, '/diff_drive_controller/cmd_vel', 10)
        self.create_subscription(Odometry, '/diff_drive_controller/odom', self.on_odom, 10)
        self.odom = None

    def on_odom(self, msg):
        self.odom = msg

    def pose(self):
        p = self.odom.pose.pose
        yaw = 2 * math.atan2(p.orientation.z, p.orientation.w)
        return p.position.x, p.position.y, yaw

    def drive(self, vx, wz, seconds):
        end = time.time() + seconds
        while time.time() < end:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist.linear.x = vx
            msg.twist.angular.z = wz
            self.pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.05)

    def wait_for_odom(self, timeout):
        end = time.time() + timeout
        while self.odom is None and time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.odom is not None


def main():
    rclpy.init()
    node = DriveTest()
    if not node.wait_for_odom(30.0):
        print('FAIL: no odometry on /diff_drive_controller/odom. Is diff_drive_controller active?')
        sys.exit(1)
    x0, y0, _ = node.pose()
    node.drive(0.2, 0.0, 2.0)
    node.drive(0.0, 0.0, 0.5)
    x1, y1, yaw1 = node.pose()
    node.drive(0.0, 1.0, 2.0)
    node.drive(0.0, 0.0, 0.5)
    _, _, yaw2 = node.pose()
    dist = math.hypot(x1 - x0, y1 - y0)
    turn = abs(math.atan2(math.sin(yaw2 - yaw1), math.cos(yaw2 - yaw1)))
    print(f'Forward: {dist:.2f} m (expected ~0.4)   Turn: {math.degrees(turn):.0f} deg (expected ~115)')
    ok = dist > 0.2 and turn > math.radians(45)
    print('PASS' if ok else 'FAIL: the robot did not move as commanded. See TROUBLESHOOTING.md')
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
