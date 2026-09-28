#!/usr/bin/env python3

import math
import os
import re

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    SetEnvironmentVariable,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _mid360_robot_description():
    """Attach the inverted 3-D lidar directly to TurtleBot3 Waffle."""
    description_share = get_package_share_directory('turtlebot3_description')
    description_path = os.path.join(
        description_share,
        'urdf',
        'turtlebot3_waffle.urdf',
    )
    with open(description_path, encoding='utf-8') as urdf_file:
        description = urdf_file.read().replace('${namespace}', '')
    description = description.replace(
        'package://turtlebot3_description/',
        description_share + os.sep,
    )

    # The upstream Waffle description also adds a forward-mounted 2-D lidar.
    # Mid360 replaces it here; keeping both adds an unnecessary forward mass.
    for pattern in (
        r'\s*<link name="laser_link">.*?</link>',
        r'\s*<joint name="laser_joint" type="fixed">.*?</joint>',
        r'\s*<gazebo reference="laser_link">.*?</gazebo>',
    ):
        description, removed = re.subn(
            pattern, '', description, count=1, flags=re.DOTALL
        )
        if removed != 1:
            raise RuntimeError('Could not remove the default Waffle 2-D lidar')

    # Raise the chassis shell while leaving the wheel and sensor frames fixed.
    chassis_origins = (
        ('<origin xyz="-0.064 0 0.0" rpy="0 0 0"/>',
         '<origin xyz="-0.064 0 0.015" rpy="0 0 0"/>'),
        ('<origin xyz="-0.064 0 0.047" rpy="0 0 0"/>',
         '<origin xyz="-0.064 0 0.062" rpy="0 0 0"/>'),
    )
    for original, raised in chassis_origins:
        if description.count(original) != 1:
            raise RuntimeError('Could not locate the Waffle chassis geometry')
        description = description.replace(original, raised, 1)

    # Move the sensor 0.10 m toward the rear to counter forward tipping on
    # downhill runs. Its height stays 0.5 m above base_link. Roll=pi represents
    # the upside-down installation while keeping the scan plane level.
    accessories = f'''
  <link name="mid360_link">
    <visual name="mid360_visual">
      <geometry><box size="0.12 0.10 0.08"/></geometry>
      <material name="black"/>
    </visual>
    <collision name="mid360_collision">
      <geometry><box size="0.12 0.10 0.08"/></geometry>
    </collision>
    <inertial>
      <mass value="0.265"/>
      <inertia ixx="0.00060" ixy="0" ixz="0" iyy="0.00085" iyz="0" izz="0.00085"/>
    </inertial>
  </link>
  <joint name="mid360_joint" type="fixed">
    <parent link="base_link"/>
    <child link="mid360_link"/>
    <origin xyz="-0.10 0 0.45" rpy="{math.pi} 0 0"/>
  </joint>

  <gazebo reference="mid360_link">
    <sensor name="mid360_lidar" type="ray">
      <always_on>true</always_on>
      <update_rate>10.0</update_rate>
      <ray>
        <scan>
          <horizontal>
            <samples>360</samples>
            <resolution>1</resolution>
            <min_angle>-3.14159265</min_angle>
            <max_angle>3.14159265</max_angle>
          </horizontal>
          <vertical>
            <samples>32</samples>
            <resolution>1</resolution>
            <min_angle>-0.436332</min_angle>
            <max_angle>0.436332</max_angle>
          </vertical>
        </scan>
        <range><min>0.10</min><max>70.0</max><resolution>0.01</resolution></range>
      </ray>
      <plugin name="mid360_pointcloud" filename="libgazebo_ros_ray_sensor.so">
        <ros>
          <namespace>/mid360</namespace>
          <remapping>~/out:=/livox/lidar</remapping>
        </ros>
        <output_type>sensor_msgs/PointCloud2</output_type>
        <frame_name>mid360_link</frame_name>
      </plugin>
    </sensor>
    <sensor name="mid360_imu" type="imu">
      <always_on>true</always_on>
      <update_rate>200.0</update_rate>
      <imu>
        <angular_velocity><x/><y/><z/></angular_velocity>
        <linear_acceleration><x/><y/><z/></linear_acceleration>
      </imu>
      <plugin name="mid360_imu_plugin" filename="libgazebo_ros_imu_sensor.so">
        <ros><remapping>~/out:=/livox/imu</remapping></ros>
        <frame_name>mid360_link</frame_name>
      </plugin>
    </sensor>
  </gazebo>
'''
    return description.replace('</robot>', accessories + '\n</robot>')


def generate_launch_description():
    field_share = get_package_share_directory('rc2026_field')
    default_world = os.path.join(field_share, 'worlds', 'robocon2026_with_kfs.world')
    robot_description = _mid360_robot_description()

    # The MVS SDK ships an old libusb and can destabilize Gazebo Classic's
    # OGRE client when it is first in LD_LIBRARY_PATH. Keep MVS isolated from
    # the simulator and use the system Gazebo/OGRE resource directories.
    gazebo_library_path = os.pathsep.join(
        path for path in os.environ.get('LD_LIBRARY_PATH', '').split(os.pathsep)
        if path and not path.startswith('/opt/MVS/lib/')
    )

    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    gui_delay = LaunchConfiguration('gui_delay')
    gazebo_master_uri = LaunchConfiguration('gazebo_master_uri')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    yaw = LaunchConfiguration('yaw')
    use_sim_time = LaunchConfiguration('use_sim_time')

    field_models = os.path.join(field_share, 'models')
    gazebo = ExecuteProcess(
        cmd=[
            'gzserver',
            world,
            '-slibgazebo_ros_init.so',
            '-slibgazebo_ros_factory.so',
            '-slibgazebo_ros_force_system.so',
        ],
        additional_env={
            'GAZEBO_MODEL_PATH': field_models,
            'GAZEBO_MODEL_DATABASE_URI': '',
            'GAZEBO_PLUGIN_PATH': (
                '/opt/ros/humble/lib:'
                '/usr/lib/x86_64-linux-gnu/gazebo-11/plugins'
            ),
            'GAZEBO_RESOURCE_PATH': '/usr/share/gazebo-11',
        },
        output='both',
    )
    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': use_sim_time}],
        output='screen',
    )
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'turtlebot3_mid360', '-topic', 'robot_description',
            '-x', x, '-y', y, '-z', z, '-Y', yaw,
        ],
        output='screen',
    )
    spawn_robot = TimerAction(
        period=3.0,
        actions=[spawn_entity],
    )
    gzclient = ExecuteProcess(
        cmd=['gzclient', '--gui-client-plugin=libgazebo_ros_eol_gui.so'],
        output='screen',
        condition=IfCondition(gui),
    )
    # The RC2026 world contains many meshes and textures. Let gzserver finish
    # loading the world and spawning the robot before OGRE starts rendering it.
    delayed_gzclient = TimerAction(period=gui_delay, actions=[gzclient])

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=default_world),
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('gui_delay', default_value='15.0'),
        DeclareLaunchArgument('gazebo_master_uri', default_value='http://127.0.0.1:11346'),
        DeclareLaunchArgument('x', default_value='-5.5'),
        DeclareLaunchArgument('y', default_value='5.58'),
        DeclareLaunchArgument('z', default_value='0.45'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        SetEnvironmentVariable(name='LD_LIBRARY_PATH', value=gazebo_library_path),
        SetEnvironmentVariable(name='GAZEBO_MASTER_URI', value=gazebo_master_uri),
        SetEnvironmentVariable(name='GAZEBO_RESOURCE_PATH', value='/usr/share/gazebo-11'),
        SetEnvironmentVariable(name='GAZEBO_MODEL_DATABASE_URI', value=''),
        SetEnvironmentVariable(
            name='OGRE_RESOURCE_PATH',
            value='/usr/lib/x86_64-linux-gnu/OGRE-1.9.0',
        ),
        # Do not inherit the broad ROS model path. Gazebo's GUI scans every
        # directory there as a model directory, including unrelated packages.
        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=os.path.join(field_share, 'models'),
        ),
        gazebo,
        state_publisher,
        spawn_robot,
        delayed_gzclient,
    ])
