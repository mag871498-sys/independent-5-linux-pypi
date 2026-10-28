#!/bin/bash
set -euo pipefail
# Docker provides a cgroup2 mount scoped to this private cgroup namespace.
mount -o remount,rw /sys/fs/cgroup
# Device administration belongs to Docker's Linux VM, not this container.
mount -o remount,ro /sys
exec /sbin/init
