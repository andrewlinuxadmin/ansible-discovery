#!/usr/bin/env python3
"""
Unit tests for nginx_config_parser module.

Tests the nginx configuration parsing functionality using actual nginx.conf and
mime.types files located in the nginx/ subdirectory.

This module is based on nginx parsing techniques:
Features comprehensive config parsing, includes processing, and error handling.
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nginx_config_parser


class TestNginxConfigParser(unittest.TestCase):
    """Test cases for nginx_config_parser module"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.nginx_test_dir = os.path.join(self.test_dir, "nginx")
        self.nginx_conf_path = os.path.join(self.nginx_test_dir, "nginx.conf")
        self.mime_types_path = os.path.join(self.nginx_test_dir, "mime.types")

        # Verify test files exist
        self.assertTrue(
            os.path.exists(self.nginx_conf_path),
            f"Test nginx.conf not found at {self.nginx_conf_path}",
        )
        self.assertTrue(
            os.path.exists(self.mime_types_path),
            f"Test mime.types not found at {self.mime_types_path}",
        )

    def test_parse_readable_format_default(self):
        """Test parsing with readable format (default)"""
        # Parse configuration using the module's parse function
        raw_result = nginx_config_parser.parse(
            filename=self.nginx_conf_path,
            comments=False,
            single=False,
            ignore=[],
            strict=False,
            combine=False,
        )

        # Convert to readable format (module default)
        if raw_result["status"] == "ok" and raw_result["config"]:
            result = nginx_config_parser.create_readable_nginx_config(raw_result)

            self.assertEqual(result["status"], "ok")
            self.assertIsInstance(result, dict)
            self.assertIn("nginx", result)

            # Check if basic directives are parsed
            nginx_config = result["nginx"]
            self.assertIn("worker_processes", nginx_config)
            self.assertIn("events", nginx_config)
            self.assertIn("http", nginx_config)

    def test_parse_with_comments(self):
        """Test parsing with comments included"""
        result = nginx_config_parser.parse(
            filename=self.nginx_conf_path,
            comments=True,
            single=False,
            ignore=[],
            strict=False,
            combine=False,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn("config", result)
        self.assertIsInstance(result["config"], list)

    def test_parse_single_file_mode(self):
        """Test parsing in single file mode (ignore includes)"""
        result = nginx_config_parser.parse(
            filename=self.nginx_conf_path,
            comments=False,
            single=True,
            ignore=[],
            strict=False,
            combine=False,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn("config", result)

        self.assertEqual(result["status"], "ok")
        self.assertIn("config", result)

    def test_parse_with_ignored_directives(self):
        """Test parsing with ignored directives (security filter)"""
        ignored_directives = ["error_log", "access_log"]
        result = nginx_config_parser.parse(
            filename=self.nginx_conf_path,
            comments=False,
            single=False,
            ignore=ignored_directives,
            strict=False,
            combine=False,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIsInstance(result, dict)
        self.assertIn("config", result)

        # Convert to readable format to check filtering
        if result["config"]:
            readable_result = nginx_config_parser.create_readable_nginx_config(result)
            config_str = json.dumps(readable_result)

            # Verify ignored directives are not present
            for directive in ignored_directives:
                self.assertNotIn(
                    directive,
                    config_str,
                    f"Ignored directive '{directive}' found in output",
                )

    def test_parse_nonexistent_file(self):
        """Test parsing with nonexistent file"""
        nonexistent_path = "/path/that/does/not/exist/nginx.conf"
        result = nginx_config_parser.parse(
            filename=nonexistent_path,
            comments=False,
            single=False,
            ignore=[],
            strict=False,
            combine=False,
        )

        self.assertNotEqual(result["status"], "ok")
        self.assertIn("errors", result)
        self.assertGreater(len(result["errors"]), 0)

    def test_create_readable_nginx_config(self):
        """Test conversion to readable format"""
        # First get raw crossplane data
        raw_result = nginx_config_parser.parse(
            filename=self.nginx_conf_path,
            comments=False,
            single=False,
            ignore=[],
            strict=False,
            combine=False,
        )

        if raw_result["status"] == "ok" and raw_result["config"]:
            readable_result = nginx_config_parser.create_readable_nginx_config(
                raw_result
            )

            self.assertEqual(readable_result["status"], "ok")
            self.assertIn("nginx", readable_result)

            # Readable format should be a dictionary
            config = readable_result["nginx"]
            self.assertIsInstance(config, dict)

    def test_ansible_module_integration(self):
        """Test the main function with mock Ansible module"""
        with patch("nginx_config_parser.AnsibleModule") as mock_module_class:
            # Create mock module instance
            mock_module = MagicMock()
            mock_module.params = {
                "path": self.nginx_conf_path,
                "include_comments": False,
                "single_file": False,
                "ignore_directives": [],
                "strict": False,
                "combine": False,
                "crossplane_format": False,
            }
            mock_module_class.return_value = mock_module

            # Call main function
            nginx_config_parser.main()

            # Verify module.exit_json was called
            mock_module.exit_json.assert_called_once()

            # Get the result from the call
            call_args = mock_module.exit_json.call_args[1]
            self.assertIn("changed", call_args)
            self.assertIn("config", call_args)
            self.assertEqual(call_args["changed"], False)

    def test_ansible_module_with_invalid_path(self):
        """Test main function with invalid path"""
        with patch("nginx_config_parser.AnsibleModule") as mock_module_class:
            mock_module = MagicMock()
            mock_module.params = {
                "path": "/invalid/path/nginx.conf",
                "include_comments": False,
                "single_file": False,
                "ignore_directives": [],
                "strict": False,
                "combine": False,
                "crossplane_format": False,
            }
            mock_module_class.return_value = mock_module

            # Call main function
            nginx_config_parser.main()

            # Should call exit_json with error status
            mock_module.exit_json.assert_called_once()
            call_args = mock_module.exit_json.call_args[1]
            self.assertIn("config", call_args)

            # Config should indicate failure
            config = call_args["config"]
            self.assertNotEqual(config.get("status"), "ok")

    def test_error_handling(self):
        """Test error handling with various invalid inputs"""
        test_cases = [
            "",  # Empty filename
            "/proc/invalid_permission",  # Permission denied
        ]

        for test_case in test_cases:
            with self.subTest(filename=test_case):
                result = nginx_config_parser.parse(
                    filename=test_case,
                    comments=False,
                    single=False,
                    ignore=[],
                    strict=False,
                    combine=False,
                )

                # Should handle error gracefully
                self.assertIsInstance(result, dict)
                self.assertIn("status", result)
                if result["status"] != "ok":
                    self.assertIn("errors", result)

        # Test None filename separately (causes TypeError)
        with self.assertRaises(TypeError):
            nginx_config_parser.parse(
                filename=None,
                comments=False,
                single=False,
                ignore=[],
                strict=False,
                combine=False,
            )


class TestNginxConfigParserEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""

    def test_empty_file_handling(self):
        """Test handling of empty configuration file"""
        # Create temporary empty file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as temp_file:
            temp_file.write("")
            temp_path = temp_file.name

        try:
            result = nginx_config_parser.parse(
                filename=temp_path,
                comments=False,
                single=False,
                ignore=[],
                strict=False,
                combine=False,
            )

            # Should handle empty file gracefully
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)

        finally:
            # Clean up
            os.unlink(temp_path)

    def test_malformed_config_handling(self):
        """Test handling of malformed configuration"""
        # Create temporary malformed file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as temp_file:
            temp_file.write("server {\n    incomplete block...\n")
            temp_path = temp_file.name

        try:
            result = nginx_config_parser.parse(
                filename=temp_path,
                comments=False,
                single=False,
                ignore=[],
                strict=True,  # Use strict mode to catch errors
                combine=False,
            )

            # Should handle malformed config
            self.assertIsInstance(result, dict)
            self.assertIn("status", result)

        finally:
            # Clean up
            os.unlink(temp_path)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
