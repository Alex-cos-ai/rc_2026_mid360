#!/usr/bin/env python3

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory('rc2026_mid360_sim')
    fast_lio_share = get_package_share_directory('fast_lio')
    sim_launch = os.path.join(package_share, 'launch', 'sim.launch.py')
    config = os.path.join(package_share, 'config', 'mid360_sim.yaml')
    rviz_config = os.path.join(fast_lio_share, 'rviz', 'fastlio.rviz')
    library_path = os.pathsep.join(
        path for path in (
            '/lib/x86_64-linux-gnu',
            '/usr/lib/x86_64-linux-gnu',
            *os.environ.get('LD_LIBRARY_PATH', '').split(os.pathsep),
        ) if path
    )

    start_fast_lio = LaunchConfiguration('start_fast_lio')
    start_rviz = LaunchConfiguration('rviz')
    return LaunchDescription([
        DeclareLaunchArgument('start_fast_lio', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='true'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(sim_launch)),
        TimerAction(period=5.0, actions=[Node(
            package='fast_lio',
            executable='fastlio_mapping',
            parameters=[config],
            additional_env={'LD_LIBRARY_PATH': library_path},
            output='screen',
            condition=IfCondition(start_fast_lio),
        )]),
        TimerAction(period=7.0, actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            condition=IfCondition(start_rviz),
            output='screen',
        )]),
    ])
