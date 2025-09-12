"""
Unit tests for php_config_parser module.

Tests PHP configuration parsing functionality using actual php.ini and
extension files located in the php/ subdirectory.

Features comprehensive config parsing, multi-version discovery, extension
detection, and error handling.
"""

import unittest
import sys
import os
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import php_config_parser


class TestPHPConfigParser(unittest.TestCase):
    """Test cases for php_config_parser module"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.php_test_dir = os.path.join(self.test_dir, "php")
        self.php_ini_path = os.path.join(self.php_test_dir, "php.ini")
        self.php_d_dir = os.path.join(self.php_test_dir, "php.d")

        # Verify test files exist
        self.assertTrue(
            os.path.exists(self.php_ini_path),
            f"Test php.ini not found at {self.php_ini_path}",
        )
        self.assertTrue(
            os.path.exists(self.php_d_dir),
            f"Test php.d dir not found at {self.php_d_dir}",
        )

    def test_parse_specific_config_success(self):
        """Test parsing specific PHP configuration file"""
        # Create mock module for testing
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [self.php_ini_path],
            "php_version": None,
            "include_additional_ini": True,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Verify basic structure
        self.assertIsInstance(result, dict)
        self.assertIn("config_files", result)
        self.assertIn("php_summary", result)
        self.assertIn("errors", result)
        self.assertFalse(result["changed"])

        # Check config files
        config_files = result["config_files"]
        self.assertIsInstance(config_files, list)
        self.assertGreater(len(config_files), 0)

        # Find main config file result
        main_config = None
        for config in config_files:
            if config["path"] == self.php_ini_path:
                main_config = config
                break

        self.assertIsNotNone(main_config)
        self.assertTrue(main_config["exists"])
        self.assertIn("sections", main_config)
        self.assertIn("extensions", main_config)

    def test_auto_discovery_with_include_additional(self):
        """Test auto-discovery functionality with additional ini files"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [],
            "php_version": None,
            "include_additional_ini": True,
        }

        # Mock get_default_php_paths to return our test path
        parser = php_config_parser.PHPConfigParser(mock_module)

        with patch.object(parser, "get_default_php_paths") as mock_get_paths:
            mock_get_paths.return_value = [self.php_ini_path]

            result = parser.run()

            # Should include main config and potentially additional files
            config_files = result["config_files"]
            self.assertGreaterEqual(len(config_files), 1)  # At least main file

            # Check if additional files were found
            if len(config_files) > 1:
                additional_files = [
                    cf
                    for cf in config_files
                    if cf["path"] != self.php_ini_path
                ]
                self.assertGreater(len(additional_files), 0)

    def test_php_version_specific_parsing(self):
        """Test parsing with specific PHP version"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [self.php_ini_path],
            "php_version": "8.1",
            "include_additional_ini": False,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Should parse successfully even with version specified
        self.assertIsInstance(result, dict)
        self.assertIn("config_files", result)

        config_files = result["config_files"]
        self.assertEqual(len(config_files), 1)
        self.assertEqual(config_files[0]["path"], self.php_ini_path)

    def test_ansible_module_integration(self):
        """Test the main function with mock Ansible module"""
        with patch("php_config_parser.AnsibleModule") as mock_module_class:
            # Create mock module instance
            mock_module = MagicMock()
            mock_module.params = {
                "paths": [self.php_ini_path],
                "php_version": None,
                "include_additional_ini": True,
            }
            mock_module_class.return_value = mock_module

            # Mock exit_json to capture the result
            exit_json_result = {}

            def capture_exit_json(**kwargs):
                exit_json_result.update(kwargs)

            mock_module.exit_json.side_effect = capture_exit_json

            # Execute main function
            php_config_parser.main()

            # Verify module.exit_json was called
            mock_module.exit_json.assert_called_once()

            # Verify response structure
            self.assertIn("changed", exit_json_result)
            self.assertIn("config_files", exit_json_result)
            self.assertIn("php_summary", exit_json_result)
            self.assertIn("errors", exit_json_result)

            # Verify successful parsing
            self.assertFalse(exit_json_result["changed"])
            self.assertIsInstance(exit_json_result["config_files"], list)

    def test_ansible_module_with_invalid_path(self):
        """Test main function with invalid file path"""
        with patch("php_config_parser.AnsibleModule") as mock_module_class:
            mock_module = MagicMock()
            mock_module.params = {
                "paths": ["/nonexistent/path/php.ini"],
                "php_version": None,
                "include_additional_ini": False,
            }
            mock_module_class.return_value = mock_module

            # Execute main function
            php_config_parser.main()

            # Should not call fail_json for non-existent files
            # (parser handles them gracefully)
            mock_module.exit_json.assert_called_once()
            call_args = mock_module.exit_json.call_args[1]

            # Should still return valid structure with non-existent file info
            self.assertIn("config_files", call_args)
            config_files = call_args["config_files"]
            self.assertEqual(len(config_files), 1)
            self.assertFalse(config_files[0]["exists"])

    def test_settings_parsing(self):
        """Test that PHP settings are parsed correctly"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [self.php_ini_path],
            "php_version": None,
            "include_additional_ini": False,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        config_files = result["config_files"]
        main_config = config_files[0]

        # Check that sections were parsed
        sections = main_config["sections"]
        self.assertIsInstance(sections, list)

        # PHP ini files should have common sections
        self.assertGreater(len(sections), 0)

    def test_extensions_detection(self):
        """Test that PHP extensions are detected correctly"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [self.php_ini_path],
            "php_version": None,
            "include_additional_ini": True,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Check for extensions in config files
        config_files = result["config_files"]

        # Look for extension files or settings
        for cf in config_files:
            if cf["exists"] and len(cf.get("extensions", [])) > 0:
                # Found extensions in at least one file
                break

        # Extensions may be in the summary as well
        php_summary = result["php_summary"]
        if "all_extensions" in php_summary:
            # Extensions could be empty - this is acceptable
            self.assertIsInstance(php_summary["all_extensions"], list)

    def test_php_summary_generation(self):
        """Test PHP summary generation"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [self.php_ini_path],
            "php_version": None,
            "include_additional_ini": True,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Check PHP summary
        php_summary = result["php_summary"]
        self.assertIsInstance(php_summary, dict)

        # Should contain summary information
        expected_keys = ["total_files", "main_config", "php_version"]
        for key in expected_keys:
            self.assertIn(key, php_summary)

    def test_include_additional_ini_false(self):
        """Test parsing with include_additional_ini=False"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [self.php_ini_path],
            "php_version": None,
            "include_additional_ini": False,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Should only parse the main file
        config_files = result["config_files"]
        self.assertEqual(len(config_files), 1)
        self.assertEqual(config_files[0]["path"], self.php_ini_path)

    def test_multiple_paths_parsing(self):
        """Test parsing multiple specific paths"""
        # Create a simple test ini file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ini", delete=False
        ) as tmp_file:
            tmp_file.write("[PHP]\n")
            tmp_file.write("memory_limit = 128M\n")
            tmp_file.write("extension=test.so\n")
            tmp_file_path = tmp_file.name

        try:
            mock_module = MagicMock()
            mock_module.params = {
                "paths": [self.php_ini_path, tmp_file_path],
                "php_version": None,
                "include_additional_ini": False,
            }

            parser = php_config_parser.PHPConfigParser(mock_module)
            result = parser.run()

            # Should parse both files
            config_files = result["config_files"]
            self.assertEqual(len(config_files), 2)

            # Check that both files are represented
            parsed_paths = [cf["path"] for cf in config_files]
            self.assertIn(self.php_ini_path, parsed_paths)
            self.assertIn(tmp_file_path, parsed_paths)

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)


class TestPHPConfigParserEdgeCases(unittest.TestCase):
    """Test edge cases for php_config_parser module"""

    def setUp(self):
        """Set up test fixtures for edge cases"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))

    def test_empty_file_handling(self):
        """Test handling of empty configuration file"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ini", delete=False
        ) as tmp_file:
            # Create empty file
            tmp_file_path = tmp_file.name

        try:
            mock_module = MagicMock()
            mock_module.params = {
                "paths": [tmp_file_path],
                "php_version": None,
                "include_additional_ini": False,
            }

            parser = php_config_parser.PHPConfigParser(mock_module)
            result = parser.run()

            # Should handle empty file gracefully
            config_files = result["config_files"]
            self.assertEqual(len(config_files), 1)
            self.assertTrue(config_files[0]["exists"])
            self.assertIsInstance(config_files[0]["sections"], list)

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_nonexistent_file_handling(self):
        """Test handling of non-existent files"""
        nonexistent_path = "/tmp/nonexistent_php.ini"

        mock_module = MagicMock()
        mock_module.params = {
            "paths": [nonexistent_path],
            "php_version": None,
            "include_additional_ini": False,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Should handle non-existent file gracefully
        config_files = result["config_files"]
        self.assertEqual(len(config_files), 1)
        self.assertFalse(config_files[0]["exists"])
        self.assertEqual(config_files[0]["path"], nonexistent_path)

    def test_malformed_ini_handling(self):
        """Test handling of malformed INI file"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ini", delete=False
        ) as tmp_file:
            # Create malformed ini content
            tmp_file.write("[Invalid Section\n")  # Missing closing bracket
            tmp_file.write("invalid_syntax_here\n")
            tmp_file.write("key = value\n")
            tmp_file_path = tmp_file.name

        try:
            mock_module = MagicMock()
            mock_module.params = {
                "paths": [tmp_file_path],
                "php_version": None,
                "include_additional_ini": False,
            }

            parser = php_config_parser.PHPConfigParser(mock_module)
            result = parser.run()

            # Should handle malformed file without crashing
            config_files = result["config_files"]
            self.assertEqual(len(config_files), 1)
            self.assertTrue(config_files[0]["exists"])

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_auto_discovery_no_default_paths(self):
        """Test auto-discovery when no default paths exist"""
        mock_module = MagicMock()
        mock_module.params = {
            "paths": [],
            "php_version": None,
            "include_additional_ini": True,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)

        # Mock get_default_php_paths to return non-existent paths
        with patch.object(parser, "get_default_php_paths") as mock_get_paths:
            mock_get_paths.return_value = ["/nonexistent/php.ini"]

            result = parser.run()

            # Should handle gracefully with no valid files
            config_files = result["config_files"]
            self.assertEqual(len(config_files), 1)
            self.assertFalse(config_files[0]["exists"])

    def test_permission_denied_handling(self):
        """Test handling of permission denied errors"""
        # Use a path that likely has permission restrictions
        restricted_path = "/root/php.ini"

        mock_module = MagicMock()
        mock_module.params = {
            "paths": [restricted_path],
            "php_version": None,
            "include_additional_ini": False,
        }

        parser = php_config_parser.PHPConfigParser(mock_module)
        result = parser.run()

        # Should handle permission errors gracefully
        config_files = result["config_files"]
        self.assertEqual(len(config_files), 1)

        # File should be marked as non-existent or have error info
        config_file = config_files[0]
        self.assertEqual(config_file["path"], restricted_path)


if __name__ == "__main__":
    unittest.main()
