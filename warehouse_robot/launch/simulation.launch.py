#!/usr/bin/env python3
"""Launch file for warehouse robot simulation with Gazebo Sim and RViz2.

Starts modern Gazebo Sim (Harmonic / Garden), spawns the 4-wheel differential
drive robot from Xacro, runs the ros_gz_bridge, executes robot_state_publisher,
spawns the obstacle avoidance reactive controller, and opens RViz2.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('warehouse_robot')

    # Paths to files
    world_path = PathJoinSubstitution([pkg_share, 'worlds', 'empty_world.sdf'])
    urdf_path = PathJoinSubstitution([pkg_share, 'urdf', 'robot.urdf.xacro'])
    rviz_config_path = PathJoinSubstitution([pkg_share, 'rviz', 'robot_view.rviz'])
    robot_config_path = PathJoinSubstitution([pkg_share, 'config', 'robot.yaml'])

    # Declare arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock from Gazebo'
    )
    rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Start RViz2 visualization'
    )
    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Run Gazebo in headless mode without GUI (-s)'
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('use_rviz')

    # Convert Xacro to URDF text description
    robot_description_content = ParameterValue(
        Command([
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            urdf_path
        ]),
        value_type=str
    )

    # 1. Start Gazebo Sim (gz sim)
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ),
        launch_arguments={
            'gz_args': ['-r ', world_path]
        }.items()
    )

    # 2. Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': use_sim_time
        }]
    )

    # 3. Spawn Robot in Gazebo Sim
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_warehouse_robot',
        arguments=[
            '-name', 'warehouse_robot',
            '-topic', 'robot_description',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.15',
        ],
        output='screen'
    )

    # 4. ros_gz_bridge (Gazebo Sim <-> ROS 2 topic translation)
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        arguments=[
            # cmd_vel (ROS 2 -> Gazebo)
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            # scan (Gazebo -> ROS 2)
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            # imu (Gazebo -> ROS 2)
            '/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            # odom (Gazebo -> ROS 2)
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            # sim clock (Gazebo -> ROS 2)
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # TF (Gazebo -> ROS 2)
            '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            # Joint states (Gazebo -> ROS 2)
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    # 5. Obstacle Avoidance Reactive Controller Node
    obstacle_avoidance_node = Node(
        package='warehouse_robot',
        executable='obstacle_avoidance',
        name='obstacle_avoidance',
        parameters=[
            robot_config_path,
            {'use_sim_time': use_sim_time}
        ],
        output='screen'
    )

    # 6. RViz2 Visualizer
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config_path],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
        output='screen'
    )

    return LaunchDescription([
        use_sim_time_arg,
        rviz_arg,
        headless_arg,
        gz_sim,
        robot_state_publisher,
        spawn_robot,
        bridge,
        obstacle_avoidance_node,
        rviz_node,
    ])
