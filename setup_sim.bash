#!/usr/bin/env bash
set -e

source /opt/ros/humble/setup.bash
source "$HOME/projects/rc_2026/install/setup.bash"
if [ -f "$HOME/plufin/rc2026_field/install/setup.bash" ]; then
  source "$HOME/plufin/rc2026_field/install/setup.bash"
fi
source "$HOME/mid360/install/setup.bash"
source "$HOME/rc_2026_mid360/install_final/setup.bash"

# Add the project overlay explicitly so ROS 2 resolves this package first.
export AMENT_PREFIX_PATH="$HOME/rc_2026_mid360/install_final:${AMENT_PREFIX_PATH:-}"

# The ros2 CLI daemon may keep stale DDS graph endpoints alive between runs.
# It is not needed by ros2 launch and can make /clock appear to have a second
# publisher.  Stop it quietly when this simulation environment is sourced.
if command -v ros2 >/dev/null 2>&1; then
  ros2 daemon stop >/dev/null 2>&1 || true
fi

# Remove only Fast DDS shared-memory files that no process still has open.
# They are left behind by a forced Gazebo exit and can corrupt the next run.
# Active ROS 2 applications keep their files untouched.
if command -v fuser >/dev/null 2>&1; then
  for shm_file in /dev/shm/fastrtps* /dev/shm/sem.fastrtps*; do
    [ -e "$shm_file" ] || continue
    if ! fuser "$shm_file" >/dev/null 2>&1; then
      rm -f -- "$shm_file"
    fi
  done
fi
