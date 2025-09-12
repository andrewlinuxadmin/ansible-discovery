#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for process_facts module.
"""

import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add parent directory to path for importing the module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from process_facts import ProcessCollectorPure, main  # noqa: E402


class TestProcessCollectorPure(unittest.TestCase):
    """Test cases for ProcessCollectorPure class."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = ProcessCollectorPure(
            exclude_kernel_threads=True, detect_containers=True
        )

    def test_init(self):
        """Test ProcessCollectorPure initialization."""
        self.assertTrue(self.collector.exclude_kernel_threads)
        self.assertTrue(self.collector.detect_containers)
        self.assertIsInstance(self.collector.boot_time, float)
        self.assertIsInstance(self.collector.clock_ticks, int)

    def test_init_with_false_params(self):
        """Test initialization with false parameters."""
        collector = ProcessCollectorPure(
            exclude_kernel_threads=False, detect_containers=False
        )
        self.assertFalse(collector.exclude_kernel_threads)
        self.assertFalse(collector.detect_containers)

    @patch("builtins.open", new_callable=mock_open,
           read_data="btime 1629123456\n")
    def test_get_boot_time_success(self, mock_file):
        """Test successful boot time extraction."""
        boot_time = self.collector._get_boot_time()
        self.assertEqual(boot_time, 1629123456.0)
        mock_file.assert_called_once_with("/proc/stat", "r")

    @patch("builtins.open", side_effect=OSError("File not found"))
    @patch("time.time", return_value=1629123456.0)
    def test_get_boot_time_failure(self, mock_time, mock_file):
        """Test boot time fallback on file error."""
        boot_time = self.collector._get_boot_time()
        self.assertEqual(boot_time, 1629123456.0)
        mock_time.assert_called_once()

    @patch("pwd.getpwuid")
    def test_get_user_info_success(self, mock_getpwuid):
        """Test successful user info retrieval."""
        mock_user = MagicMock()
        mock_user.pw_name = "testuser"
        mock_user.pw_dir = "/home/testuser"
        mock_getpwuid.return_value = mock_user

        username, homedir = self.collector._get_user_info(1000)

        self.assertEqual(username, "testuser")
        self.assertEqual(homedir, "/home/testuser")
        mock_getpwuid.assert_called_once_with(1000)

    @patch("pwd.getpwuid", side_effect=KeyError("User not found"))
    def test_get_user_info_failure(self, mock_getpwuid):
        """Test user info fallback on KeyError."""
        username, homedir = self.collector._get_user_info(9999)

        self.assertEqual(username, "9999")
        self.assertEqual(homedir, "unknown")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data=b"")
    def test_is_kernel_thread_empty_cmdline(self, mock_file, mock_exists):
        """Test kernel thread detection with empty cmdline."""
        # Mock the stat file read for the fallback check
        mock_file.return_value.read.side_effect = [b"", "1 (test) S 1 1"]
        result = self.collector._is_kernel_thread(1)
        self.assertTrue(result)

    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open", new_callable=mock_open,
        read_data=b"/usr/bin/bash\x00arg1\x00"
    )
    def test_is_kernel_thread_normal_process(self, mock_file, mock_exists):
        """Test normal process detection."""
        result = self.collector._is_kernel_thread(1000)
        self.assertFalse(result)

    @patch("os.path.exists", return_value=False)
    def test_is_kernel_thread_no_cmdline_file(self, mock_exists):
        """Test kernel thread detection when cmdline file doesn't exist."""
        result = self.collector._is_kernel_thread(1)
        self.assertTrue(result)

    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="1:name=systemd:/docker/container123\n",
    )
    def test_is_containerized_docker(self, mock_file, mock_exists):
        """Test container detection for Docker."""
        result = self.collector._is_containerized(1000)
        self.assertTrue(result)

    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="1:name=systemd:/system.slice/sshd.service\n",
    )
    def test_is_containerized_normal_process(self, mock_file, mock_exists):
        """Test non-containerized process detection."""
        # Mock both cgroup and environ file reads
        mock_file.return_value.read.side_effect = [
            "1:name=systemd:/system.slice/sshd.service\n",  # cgroup
            b"PATH=/usr/bin\x00HOME=/home/user\x00"  # environ
        ]
        result = self.collector._is_containerized(1000)
        self.assertFalse(result)

    def test_is_containerized_disabled(self):
        """Test container detection when disabled."""
        collector = ProcessCollectorPure(detect_containers=False)
        result = collector._is_containerized(1000)
        self.assertFalse(result)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="VmRSS:\t1024 kB\nVmSize:\t4096 kB\n",
    )
    def test_get_memory_usage_success(self, mock_file):
        """Test successful memory usage extraction."""
        memory = self.collector._get_memory_usage(1000)
        self.assertEqual(memory, 1024)

    @patch("builtins.open", new_callable=mock_open,
           read_data="VmSize:\t4096 kB\n")
    def test_get_memory_usage_no_rss(self, mock_file):
        """Test memory usage when VmRSS is not found."""
        memory = self.collector._get_memory_usage(1000)
        self.assertEqual(memory, 0)

    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_get_memory_usage_file_error(self, mock_file):
        """Test memory usage on file error."""
        memory = self.collector._get_memory_usage(1000)
        self.assertEqual(memory, 0)

    @patch("time.time", return_value=1629123500.0)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="1000 (test) S 1 1000 1000 0 -1 4194304 0 0 0 0 10 5 0 0 "
                  "20 0 1 0 100 4096 256 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 "
                  "0 0 0 0 0",
    )
    def test_get_cpu_usage_success(self, mock_file, mock_time):
        """Test successful CPU usage calculation."""
        self.collector.boot_time = 1629123456.0
        self.collector.clock_ticks = 100

        cpu_percent = self.collector._get_cpu_usage(1000)
        self.assertIsInstance(cpu_percent, float)
        self.assertGreaterEqual(cpu_percent, 0.0)

    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_get_cpu_usage_file_error(self, mock_file):
        """Test CPU usage on file error."""
        cpu_percent = self.collector._get_cpu_usage(1000)
        self.assertEqual(cpu_percent, 0.0)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="1000 (testproc) S 1 1000 1000 0 -1 4194304 0 0 0 0 10 5 "
                  "0 0 20 0 2 0 100",
    )
    def test_parse_stat_file_success(self, mock_file):
        """Test successful stat file parsing."""
        stat_info = self.collector._parse_stat_file(1000)

        self.assertIsInstance(stat_info, dict)
        self.assertEqual(stat_info["pid"], 1000)
        self.assertEqual(stat_info["comm"], "testproc")
        self.assertEqual(stat_info["ppid"], 1)
        self.assertEqual(stat_info["state"], "S")
        self.assertEqual(stat_info["threads"], 2)

    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_parse_stat_file_error(self, mock_file):
        """Test stat file parsing on error."""
        stat_info = self.collector._parse_stat_file(1000)
        self.assertIsNone(stat_info)

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=b"/usr/bin/python3\x00script.py\x00--arg\x00",
    )
    def test_get_cmdline_success(self, mock_file):
        """Test successful cmdline extraction."""
        cmdline = self.collector._get_cmdline(1000)
        self.assertEqual(cmdline, "/usr/bin/python3 script.py --arg")

    @patch("builtins.open", new_callable=mock_open, read_data=b"")
    def test_get_cmdline_empty(self, mock_file):
        """Test cmdline extraction with empty file."""
        cmdline = self.collector._get_cmdline(1000)
        self.assertEqual(cmdline, "")

    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_get_cmdline_error(self, mock_file):
        """Test cmdline extraction on file error."""
        cmdline = self.collector._get_cmdline(1000)
        self.assertEqual(cmdline, "")

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="Uid:\t1000\t1000\t1000\t1000\n",
    )
    @patch.object(
        ProcessCollectorPure,
        "_get_user_info",
        return_value=("testuser", "/home/testuser"),
    )
    def test_get_process_user_success(self, mock_user_info, mock_file):
        """Test successful process user extraction."""
        username, homedir = self.collector._get_process_user(1000)

        self.assertEqual(username, "testuser")
        self.assertEqual(homedir, "/home/testuser")
        mock_user_info.assert_called_once_with(1000)

    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_get_process_user_error(self, mock_file):
        """Test process user extraction on file error."""
        username, homedir = self.collector._get_process_user(1000)

        self.assertEqual(username, "unknown")
        self.assertEqual(homedir, "unknown")


class TestProcessFactsIntegration(unittest.TestCase):
    """Integration tests for process_facts module."""

    @patch("os.path.exists", return_value=False)
    def test_collect_processes_no_proc(self, mock_exists):
        """Test collect_processes when /proc doesn't exist."""
        collector = ProcessCollectorPure()

        with self.assertRaises(Exception) as context:
            collector.collect_processes()

        self.assertIn("/proc filesystem not available", str(context.exception))

    @patch("os.path.exists", return_value=True)
    @patch("os.listdir", return_value=["1", "2", "self", "version", "1000"])
    @patch.object(ProcessCollectorPure, "_parse_stat_file")
    @patch.object(ProcessCollectorPure, "_get_cmdline")
    @patch.object(ProcessCollectorPure, "_get_process_user")
    @patch.object(ProcessCollectorPure, "_is_kernel_thread")
    @patch.object(ProcessCollectorPure, "_is_containerized")
    @patch.object(ProcessCollectorPure, "_get_memory_usage")
    @patch.object(ProcessCollectorPure, "_get_cpu_usage")
    def test_collect_processes_success(
        self,
        mock_cpu,
        mock_memory,
        mock_container,
        mock_kernel,
        mock_user,
        mock_cmdline,
        mock_stat,
        mock_listdir,
        mock_exists,
    ):
        """Test successful process collection."""
        # Mock return values
        mock_stat.return_value = {
            "pid": 1000,
            "comm": "testproc",
            "ppid": 1,
            "state": "S",
            "threads": 1,
        }
        mock_cmdline.return_value = "/usr/bin/testproc --arg"
        mock_user.return_value = ("testuser", "/home/testuser")
        mock_kernel.return_value = False
        mock_container.return_value = False
        mock_memory.return_value = 1024
        mock_cpu.return_value = 5.5

        collector = ProcessCollectorPure()
        processes = collector.collect_processes()

        self.assertIsInstance(processes, list)
        self.assertGreater(len(processes), 0)

        # Check first process structure
        process = processes[0]
        self.assertIn("pid", process)
        self.assertIn("command", process)
        self.assertIn("user", process)
        self.assertIn("args", process)
        self.assertIn("containerized", process)


class TestMainFunction(unittest.TestCase):
    """Test cases for main function."""

    @patch("process_facts.AnsibleModule")
    def test_main_success(self, mock_ansible_module):
        """Test successful main function execution."""
        # Mock module instance
        mock_module = MagicMock()
        mock_module.params = {
            "exclude_kernel_threads": True,
            "detect_containers": True
        }
        mock_ansible_module.return_value = mock_module

        # Mock collector
        with patch.object(ProcessCollectorPure,
                          "collect_processes") as mock_collect:
            mock_collect.return_value = [
                {
                    "pid": "1000",
                    "ppid": "1",
                    "user": "testuser",
                    "command": "testproc",
                    "args": "/usr/bin/testproc",
                    "containerized": False,
                    "homedir": "/home/testuser",
                    "state": "S",
                    "threads": 1,
                    "memory_kb": 1024,
                    "cpu_percent": 5.5,
                }
            ]

            main()

            # Verify module was called correctly
            mock_ansible_module.assert_called_once()
            mock_module.exit_json.assert_called_once()

            # Check exit_json was called with correct structure
            call_args = mock_module.exit_json.call_args[1]
            self.assertIn("ansible_facts", call_args)
            self.assertIn("processes", call_args["ansible_facts"])

    @patch("process_facts.AnsibleModule")
    def test_main_exception(self, mock_ansible_module):
        """Test main function with exception handling."""
        mock_module = MagicMock()
        mock_module.params = {
            "exclude_kernel_threads": True,
            "detect_containers": True
        }
        mock_ansible_module.return_value = mock_module

        # Mock collector to raise exception
        with patch.object(ProcessCollectorPure,
                          "collect_processes") as mock_collect:
            mock_collect.side_effect = Exception("Test error")

            main()

            # Verify fail_json was called
            mock_module.fail_json.assert_called_once()
            call_args = mock_module.fail_json.call_args[1]
            self.assertIn("msg", call_args)
            self.assertIn("Test error", call_args["msg"])


if __name__ == "__main__":
    unittest.main()
