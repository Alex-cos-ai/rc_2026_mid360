# RC2026 Mid360 仿真

这个工作区把 ROS 2 Humble/Gazebo Classic 的 TurtleBot3 Waffle 放入
`rc2026_field` 场地，并在底盘中心增加一根细长圆柱立杆。
Mid360 倒装在立杆顶端，传感器绕 X 轴旋转 180 度，雷达中心距车轮接触地面
约 0.80 m。立杆和雷达都位于车体中心线上，立杆质量保持较低，以降低附加
倾覆力矩。
模拟输出为 3D `sensor_msgs/PointCloud2` 和 IMU。

## 构建

先确保 `rc2026_field` 已经构建并 source，然后：

```bash
cd ~/rc_2026_mid360
source /opt/ros/humble/setup.bash
source ~/projects/rc_2026/install/setup.bash
source ~/plufin/rc2026_field/install/setup.bash
colcon build --symlink-install --merge-install --install-base install_final
source setup_sim.bash
```

当前已验证的构建产物位于 `install_final/`；直接运行下面的环境脚本会加载它。

## 启动

只启动场地、机器人和传感器：

```bash
ros2 launch rc2026_mid360_sim sim.launch.py
```

启动场地、机器人、FAST-LIO 和 RViz：

```bash
ros2 launch rc2026_mid360_sim mapping.launch.py
```

也可以直接使用工作区提供的环境脚本：

```bash
source ~/rc_2026_mid360/setup_sim.bash
```

点云话题为 `/livox/lidar`，IMU 话题为 `/livox/imu`，坐标系为
`mid360_link`。可以用 `rviz:=false` 或 `start_fast_lio:=false` 关闭对应组件。
