# Project 2: Obstacle Avoidance Warehouse Robot (`warehouse_robot`)

An autonomous four-wheel differential-drive mobile robot simulated in **Gazebo Sim** (Harmonic / Garden era) and visualized in **RViz2** for **ROS 2 Lyrical Luth** (Ubuntu 26.04). The robot utilizes a planar LiDAR sensor to detect obstacles and reactive steering algorithms to safely navigate around obstacles in a warehouse environment.

---

## 1. System Overview & Architecture

```
+---------------------------------------------------------------------------------------+
|                                    Gazebo Sim (gz sim)                                |
|                                                                                       |
|   +-------------------+       +--------------------+       +----------------------+   |
|   |  DiffDrive Plugin |       |    LiDAR Sensor    |       |      IMU Sensor      |   |
|   |  (4-Wheel Drive)  |       |     (gpu_lidar)    |       |                      |   |
|   +---------+---------+       +---------+----------+       +----------+-----------+   |
+-------------|---------------------------|-----------------------------|---------------+
              | /odom, /tf, /cmd_vel      | /scan                       | /imu
              v                           v                             v
+---------------------------------------------------------------------------------------+
|                                ros_gz_bridge (Topic Bridge)                           |
+-------------+---------------------------+-----------------------------+---------------+
              |                           |                             |
              v                           v                             v
+---------------------------------------------------------------------------------------+
|                                     ROS 2 Ecosystem                                   |
|                                                                                       |
|   +-----------------------+     +------------------------+    +-------------------+   |
|   |  obstacle_avoidance   |<----+      LaserScan         |    |       RViz2       |   |
|   |  (Reactive Node)      |     |     (/scan topic)      |    |  (Visualization)  |   |
|   +-----------+-----------+     +------------------------+    +-------------------+   |
|               |                                                         ^             |
|               +----------> /cmd_vel (geometry_msgs/Twist) ------------->+             |
+---------------------------------------------------------------------------------------+
```

### Key Technical Specifications
- **Locomotion**: 4-wheel differential drive (`front_left`, `front_right`, `rear_left`, `rear_right`) actuated via the modern `gz-sim-diff-drive-system` plugin.
- **Perception**: 360-degree LiDAR sensor (`gpu_lidar`) publishing to `/scan` (10 Hz, 12m range).
- **Inertial Measurement**: IMU sensor publishing to `/imu` (100 Hz).
- **Odometry & TF**: Dead-reckoning odometry and TF broadcasted from `odom` -> `base_footprint`.
- **Bridge**: `ros_gz_bridge` translating messages between Gazebo Sim protobuf channels and ROS 2 standard topics.
- **Reactive Navigation**: Proximity-based obstacle detection inspecting the forward 60-degree sector (`ranges[:30]` and `ranges[-30:]`).

---

## 2. Directory Layout

```
project2_obstacle_avoidance/
└── warehouse_robot/
    ├── package.xml
    ├── CMakeLists.txt
    ├── setup.py
    ├── resource/
    │   └── warehouse_robot
    ├── config/
    │   └── robot.yaml
    ├── launch/
    │   └── simulation.launch.py
    ├── rviz/
    │   └── robot_view.rviz
    ├── urdf/
    │   └── robot.urdf.xacro
    ├── worlds/
    │   └── empty_world.sdf
    └── warehouse_robot/
        ├── __init__.py
        └── obstacle_avoidance.py
```

---

## 3. Build & Installation Instructions

### Workspace Setup
Create a workspace named `warehouse_ws`:

```bash
mkdir -p ~/warehouse_ws/src
cd ~/warehouse_ws/src

# Copy or symlink the warehouse_robot package:
cp -r /path/to/ros2_projects/project2_obstacle_avoidance/warehouse_robot .
```

### Dependencies
Ensure the following packages are installed on your ROS 2 Lyrical Luth system:
```bash
sudo apt update
sudo apt install -y \
  ros-lyrical-ros-gz \
  ros-lyrical-ros-gz-sim \
  ros-lyrical-ros-gz-bridge \
  ros-lyrical-robot-state-publisher \
  ros-lyrical-joint-state-publisher \
  ros-lyrical-xacro \
  ros-lyrical-rviz2
```

### Build Package
```bash
cd ~/warehouse_ws
source /opt/ros/lyrical/setup.bash

colcon build --symlink-install
```

### Source Workspace
```bash
source ~/warehouse_ws/install/setup.bash
```

---

## 4. Running the Simulation

### Full System Launch
Execute the unified launch file:

```bash
ros2 launch warehouse_robot simulation.launch.py
```

This single command triggers:
1. **Gazebo Sim** (`gz sim -r empty_world.sdf`) with the ground plane and obstacles.
2. Robot state publishing with converted Xacro URDF.
3. Spawning the 4-wheel robot into Gazebo at `(x=0, y=0, z=0.15)`.
4. Bidirectional `ros_gz_bridge` for `/cmd_vel`, `/scan`, `/imu`, `/odom`, `/tf`, and `/clock`.
5. Obstacle avoidance controller node (`obstacle_avoidance`).
6. **RViz2** pre-configured to display the 3D Robot Model, TF frames, LiDAR scan points, and odometry trajectory.

### Headless Mode (Without Gazebo GUI)
For running on remote servers or CI:
```bash
ros2 launch warehouse_robot simulation.launch.py headless:=true
```

---

## 5. Topic Introspection & Manual Control

### Verify Active Topics
```bash
ros2 topic list
```
Expected topics:
- `/cmd_vel` (`geometry_msgs/msg/Twist`)
- `/scan` (`sensor_msgs/msg/LaserScan`)
- `/imu` (`sensor_msgs/msg/Imu`)
- `/odom` (`nav_msgs/msg/Odometry`)
- `/joint_states` (`sensor_msgs/msg/JointState`)
- `/robot_description` (`std_msgs/msg/String`)
- `/tf` (`tf2_msgs/msg/TFMessage`)

### Echo Sensor Readings
LiDAR scan data:
```bash
ros2 topic echo /scan --once
```

Odometry updates:
```bash
ros2 topic echo /odom --once
```

### Manual Teleoperation (Optional)
If you wish to steer manually, stop the `obstacle_avoidance` node and run:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
