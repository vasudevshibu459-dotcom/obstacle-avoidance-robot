#!/usr/bin/env python3
"""Obstacle avoidance reactive controller node for warehouse robot."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class ObstacleAvoidance(Node):
    """Reactive obstacle avoidance controller using planar LiDAR scan readings."""

    def __init__(self):
        super().__init__('obstacle_avoidance')

        # Declare parameters with configurable defaults
        self.declare_parameter('safe_distance', 0.5)
        self.declare_parameter('linear_speed', 0.15)
        self.declare_parameter('angular_speed', 0.5)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('scan_topic', '/scan')

        self.safe_distance = self.get_parameter('safe_distance').get_parameter_value().double_value
        self.linear_speed = self.get_parameter('linear_speed').get_parameter_value().double_value
        self.angular_speed = self.get_parameter('angular_speed').get_parameter_value().double_value

        cmd_topic = self.get_parameter('cmd_vel_topic').get_parameter_value().string_value
        scan_topic = self.get_parameter('scan_topic').get_parameter_value().string_value

        self.publisher_ = self.create_publisher(Twist, cmd_topic, 10)
        self.subscription = self.create_subscription(
            LaserScan, scan_topic, self.scan_callback, 10
        )

        self.get_logger().info(
            f"ObstacleAvoidance started: safe_dist={self.safe_distance}m, "
            f"linear_speed={self.linear_speed}m/s, angular_speed={self.angular_speed}rad/s"
        )

    def scan_callback(self, msg: LaserScan):
        """Evaluate forward obstacle proximity and issue reactive steering commands."""
        sample_count = len(msg.ranges)
        slice_size = min(30, sample_count // 4) if sample_count >= 4 else sample_count

        if slice_size > 0:
            front_ranges = list(msg.ranges[:slice_size]) + list(msg.ranges[-slice_size:])
        else:
            front_ranges = list(msg.ranges)

        valid_ranges = [
            d for d in front_ranges
            if msg.range_min < d < msg.range_max and not (d != d)
        ]

        twist = Twist()
        if valid_ranges:
            minimum_distance = min(valid_ranges)
            if minimum_distance < self.safe_distance:
                # Obstacle within safety distance: halt forward motion and rotate
                twist.linear.x = 0.0
                twist.angular.z = self.angular_speed
            else:
                # Path is clear: drive forward
                twist.linear.x = self.linear_speed
                twist.angular.z = 0.0
        else:
            twist.linear.x = 0.0
            twist.angular.z = 0.0

        self.publisher_.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publisher_.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
