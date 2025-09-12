# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Andrew Carlos <acarlos@redhat.com>
# Python2/3 compatible version of process_facts module

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import pwd
import time
import sys
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: process_facts
short_description: Collect process information
description:
    - Gathers process details from /proc filesystem
    - Compatible with Python 2.7+ and Python 3.x
    - Pure Python implementation with container detection
version_added: "1.0.0"
author: Andrew Carlos (@andrewlinuxadmin)
options:
    exclude_kernel_threads:
        description: Exclude kernel threads from results
        type: bool
        default: true
    detect_containers:
        description: Detect containerized processes
        type: bool
        default: true
"""

EXAMPLES = """
- name: Collect process facts
  process_facts:

- name: Include kernel threads
  process_facts:
    exclude_kernel_threads: false
"""

RETURN = """
ansible_facts:
    description: Process information
    returned: always
    type: dict
    contains:
        processes:
            description: List of processes
            type: list
"""


class ProcessCollectorPure:
    """Process collector compatible with Python 2.7+ and 3.x."""

    def __init__(self, exclude_kernel_threads=True, detect_containers=True):
        self.exclude_kernel_threads = exclude_kernel_threads
        self.detect_containers = detect_containers
        self.boot_time = self._get_boot_time()
        self.clock_ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])

    def _get_boot_time(self):
        """Get system boot time."""
        try:
            with open("/proc/stat", "r") as f:
                for line in f:
                    if line.startswith("btime "):
                        return float(line.split()[1])
        except (OSError, ValueError):
            pass
        return time.time()

    def _get_user_info(self, uid):
        """Get username and home directory."""
        try:
            user_info = pwd.getpwuid(uid)
            return user_info.pw_name, user_info.pw_dir
        except KeyError:
            return str(uid), "unknown"

    def _is_kernel_thread(self, pid):
        """Check if process is kernel thread."""
        try:
            # Python2/3 compatible string formatting
            cmdline_file = "/proc/{0}/cmdline".format(pid)
            if not os.path.exists(cmdline_file):
                return True

            with open(cmdline_file, "rb") as f:
                cmdline_data = f.read()

            if not cmdline_data or cmdline_data == b"\x00":
                try:
                    stat_file = "/proc/{0}/stat".format(pid)
                    with open(stat_file, "r") as f:
                        stat_line = f.read()

                    if "[" in stat_line and "]" in stat_line:
                        return True
                except (OSError, IOError):
                    pass
                return True

            return False

        except (OSError, IOError):
            return False

    def _is_containerized(self, pid):
        """Check if process is containerized."""
        if not self.detect_containers:
            return False

        try:
            # Check cgroups
            cgroup_file = "/proc/{0}/cgroup".format(pid)
            if os.path.exists(cgroup_file):
                with open(cgroup_file, "r") as f:
                    cgroup_content = f.read()

                container_indicators = [
                    "/docker/",
                    "/containerd/",
                    "/podman/",
                    "/machine.slice/",
                    "/crio-",
                    "/k8s_",
                    "/kubelet",
                    ".scope",
                    "/lxc/",
                ]

                for indicator in container_indicators:
                    if indicator in cgroup_content:
                        return True

            # Check environment variables
            environ_file = "/proc/{0}/environ".format(pid)
            if os.path.exists(environ_file):
                with open(environ_file, "rb") as f:
                    environ_data = f.read()

                if environ_data:
                    # Python2/3 compatible decode
                    try:
                        environ_str = environ_data.decode("utf-8", errors="ignore")
                    except AttributeError:
                        environ_str = str(environ_data)

                    container_env_vars = [
                        "CONTAINER=",
                        "container=",
                        "KUBERNETES_SERVICE_HOST=",
                        "DOCKER_CONTAINER=",
                    ]

                    for env_var in container_env_vars:
                        if env_var in environ_str:
                            return True

            return False

        except (OSError, IOError):
            return False

    def _get_memory_usage(self, pid):
        """Get memory usage in KB."""
        try:
            status_file = "/proc/{0}/status".format(pid)
            with open(status_file, "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        parts = line.split()
                        if len(parts) >= 2:
                            return int(parts[1])
        except (OSError, ValueError):
            pass
        return 0

    def _get_cpu_usage(self, pid):
        """Calculate CPU usage percentage."""
        try:
            stat_file = "/proc/{0}/stat".format(pid)
            with open(stat_file, "r") as f:
                stat_data = f.read().split()

            if len(stat_data) < 22:
                return 0.0

            utime = int(stat_data[13])
            stime = int(stat_data[14])
            total_time = utime + stime
            starttime = int(stat_data[21])

            uptime_ticks = (time.time() - self.boot_time) * self.clock_ticks
            process_uptime = uptime_ticks - starttime

            if process_uptime > 0:
                cpu_percent = (total_time / process_uptime) * 100
                return round(cpu_percent, 2)

        except (OSError, ValueError, ZeroDivisionError):
            pass
        return 0.0

    def _parse_stat_file(self, pid):
        """Parse /proc/PID/stat file."""
        try:
            stat_file = "/proc/{0}/stat".format(pid)
            with open(stat_file, "r") as f:
                stat_line = f.read().strip()

            parts = stat_line.split()
            if len(parts) < 20:
                return None

            # Handle command names with spaces in parentheses
            comm_start = stat_line.find("(")
            comm_end = stat_line.rfind(")")

            if comm_start != -1 and comm_end != -1:
                comm = stat_line[comm_start + 1 : comm_end]
                after_comm = stat_line[comm_end + 1 :].strip().split()
                if len(after_comm) >= 18:
                    return {
                        "pid": int(parts[0]),
                        "comm": comm,
                        "state": after_comm[0],
                        "ppid": int(after_comm[1]),
                        "threads": int(after_comm[17]),
                    }

        except (OSError, ValueError, IndexError):
            return None

    def _get_cmdline(self, pid):
        """Get command line arguments."""
        try:
            cmdline_file = "/proc/{0}/cmdline".format(pid)
            with open(cmdline_file, "rb") as f:
                cmdline_data = f.read()

            if cmdline_data:
                # Python2/3 compatible decode
                if sys.version_info[0] == 3:
                    args = cmdline_data.decode("utf-8", errors="ignore")
                else:
                    args = cmdline_data.decode("utf-8", "ignore")
                return " ".join(args.split("\x00")).strip()

        except (OSError, IOError):
            pass
        return ""

    def _get_process_user(self, pid):
        """Get process owner."""
        try:
            status_file = "/proc/{0}/status".format(pid)
            with open(status_file, "r") as f:
                for line in f:
                    if line.startswith("Uid:"):
                        uid = int(line.split()[1])
                        return self._get_user_info(uid)
        except (OSError, ValueError):
            pass
        return "unknown", "unknown"

    def collect_processes(self):
        """Collect process information from /proc filesystem."""
        processes = []

        if not os.path.exists("/proc"):
            raise Exception("/proc filesystem not available")

        proc_dirs = []
        for item in os.listdir("/proc"):
            if item.isdigit():
                proc_dirs.append(int(item))

        proc_dirs.sort()

        for pid in proc_dirs:
            try:
                proc_dir = "/proc/{0}".format(pid)
                if not os.path.exists(proc_dir):
                    continue

                # Get basic process info
                stat_info = self._parse_stat_file(pid)
                if not stat_info:
                    continue

                # Skip kernel threads if requested
                if self.exclude_kernel_threads and self._is_kernel_thread(pid):
                    continue

                # Get additional info
                cmdline = self._get_cmdline(pid)
                if not cmdline:
                    cmdline = "[{0}]".format(stat_info["comm"])

                # Extract command name
                cmdline_parts = cmdline.split()
                if cmdline_parts:
                    command = cmdline_parts[0]
                else:
                    command = stat_info["comm"]

                if "/" in command:
                    command = os.path.basename(command)

                username, homedir = self._get_process_user(pid)
                containerized = self._is_containerized(pid)
                memory_kb = self._get_memory_usage(pid)
                cpu_percent = self._get_cpu_usage(pid)

                process_info = {
                    "pid": str(stat_info["pid"]),
                    "ppid": str(stat_info["ppid"]),
                    "user": username,
                    "command": command,
                    "args": cmdline,
                    "containerized": containerized,
                    "homedir": homedir,
                    "state": stat_info["state"],
                    "threads": stat_info["threads"],
                    "memory_kb": memory_kb,
                    "cpu_percent": cpu_percent,
                }

                processes.append(process_info)

            except (OSError, IOError, ValueError):
                continue

        return processes


def main():
    """Main function."""
    module = AnsibleModule(
        argument_spec=dict(
            exclude_kernel_threads=dict(type="bool", default=True),
            detect_containers=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
    )

    try:
        collector = ProcessCollectorPure(
            exclude_kernel_threads=module.params["exclude_kernel_threads"],
            detect_containers=module.params["detect_containers"],
        )

        processes = collector.collect_processes()

        module.exit_json(changed=False, ansible_facts={"processes": processes})

    except Exception as e:
        # Python2/3 compatible error message
        module.fail_json(msg="Error collecting processes: {0}".format(str(e)))


if __name__ == "__main__":
    main()
