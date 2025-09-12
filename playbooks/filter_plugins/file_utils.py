#!/usr/bin/env python3
"""
Custom Ansible filter plugins for file and path operations.

This module provides filters for checking file and path existence
and accessibility in Ansible playbooks.
"""

import os


class FilterModule:
    """Custom Ansible filters for file operations."""

    def filters(self):
        """
        Return the dictionary of available filters.

        Returns:
            dict: Dictionary mapping filter names to their functions
        """
        return {
            "file_exists": self.file_exists,
            "path_exists": self.path_exists,
            "file_readable": self.file_readable,
        }

    def file_exists(self, path):
        """
        Check if a file exists and is a regular file

        Args:
            path (str): Path to check

        Returns:
            bool: True if file exists and is a regular file, False otherwise
        """
        try:
            return os.path.isfile(path)
        except (TypeError, AttributeError):
            return False

    def path_exists(self, path):
        """
        Check if a path exists (file, directory, or other)

        Args:
            path (str): Path to check

        Returns:
            bool: True if path exists, False otherwise
        """
        try:
            return os.path.exists(path)
        except (TypeError, AttributeError):
            return False

    def file_readable(self, path):
        """
        Check if a file exists and is readable

        Args:
            path (str): Path to check

        Returns:
            bool: True if file exists and is readable, False otherwise
        """
        try:
            return os.path.isfile(path) and os.access(path, os.R_OK)
        except (TypeError, AttributeError, OSError):
            return False
