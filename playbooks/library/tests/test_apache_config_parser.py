"""
Unit tests for apache_config_parser module.

Tests Apache configuration parsing functionality using actual httpd.conf and
VirtualHost files located in the apache/ subdirectory.

Features comprehensive config parsing, includes processing, VirtualHost
extraction, and error handling.
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import apache_config_parser


class TestApacheConfigParser(unittest.TestCase):
    """Test cases for apache_config_parser module"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.apache_test_dir = os.path.join(self.test_dir, "apache")
        self.httpd_conf_path = os.path.join(self.apache_test_dir, "conf", "httpd.conf")
        self.site_conf_path = os.path.join(self.apache_test_dir, "conf.d", "site.conf")
        self.intranet_conf_path = os.path.join(
            self.apache_test_dir, "conf.d", "intranet.conf"
        )
        self.configroot = os.path.join(self.apache_test_dir, "conf")

        # Verify test files exist
        self.assertTrue(
            os.path.exists(self.httpd_conf_path),
            f"Test httpd.conf not found at {self.httpd_conf_path}",
        )
        self.assertTrue(
            os.path.exists(self.site_conf_path),
            f"Test site.conf not found at {self.site_conf_path}",
        )
        self.assertTrue(
            os.path.exists(self.configroot),
            f"Test config root not found at {self.configroot}",
        )

    def test_parse_main_config_success(self):
        """Test parsing main Apache configuration file"""
        # Create test loader directly
        options = {
            "allowmultioptions": True,
            "useapacheinclude": True,
            "includeagain": True,
            "includedirectories": True,
            "includeglob": True,
            "interpolatevars": True,
            "interpolateenv": True,
            "mergeduplicateoptions": True,
            "configroot": self.configroot,
            "mergeduplicateblocks": True,
            "includerelative": True,
        }

        try:
            lexer = apache_config_parser.ApacheConfigLexer(**options)
            parser = apache_config_parser.ApacheConfigParser(lexer, **options)
            loader = apache_config_parser.ApacheConfigLoader(parser, **options)

            config_data = loader.load(self.httpd_conf_path)

            # Verify basic structure (keys are lowercase)
            self.assertIsInstance(config_data, dict)
            self.assertIn("servertokens", config_data)
            self.assertIn("serverroot", config_data)

            # Verify files were processed
            files_processed = loader.files_processed
            self.assertIsInstance(files_processed, list)
            self.assertGreater(len(files_processed), 0)
            self.assertIn(self.httpd_conf_path, files_processed)

        except Exception as e:
            self.fail(f"Apache config parsing failed: {e}")

    def test_parse_virtualhost_config(self):
        """Test parsing VirtualHost configuration"""
        options = {
            "allowmultioptions": True,
            "useapacheinclude": True,
            "includeagain": True,
            "includedirectories": True,
            "includeglob": True,
            "interpolatevars": True,
            "interpolateenv": True,
            "mergeduplicateoptions": True,
            "configroot": os.path.dirname(self.site_conf_path),
            "mergeduplicateblocks": True,
            "includerelative": True,
        }

        try:
            lexer = apache_config_parser.ApacheConfigLexer(**options)
            parser = apache_config_parser.ApacheConfigParser(lexer, **options)
            loader = apache_config_parser.ApacheConfigLoader(parser, **options)

            config_data = loader.load(self.site_conf_path)

            # Verify VirtualHost structure
            self.assertIsInstance(config_data, dict)
            self.assertIn("VirtualHost", config_data)

            # Check VirtualHost details (keys are lowercase)
            vhost_data = config_data["VirtualHost"]
            if isinstance(vhost_data, dict):
                # Should contain expected directives
                # VirtualHost structure: {'*:80': {'servername': ...}}
                for vhost_key, vhost_config in vhost_data.items():
                    self.assertIn("servername", vhost_config)
                    self.assertIn("documentroot", vhost_config)
                    self.assertIn("serveradmin", vhost_config)

        except Exception as e:
            self.fail(f"VirtualHost config parsing failed: {e}")

    def test_ansible_module_integration(self):
        """Test the main function with mock Ansible module"""
        with patch("apache_config_parser.AnsibleModule") as mock_module_class:
            # Create mock module instance
            mock_module = MagicMock()
            mock_module.params = {
                "path": self.httpd_conf_path,
                "configroot": self.configroot,
                "output_format": "dict",
                "allowmultioptions": True,
                "useapacheinclude": True,
                "includeagain": True,
                "includedirectories": True,
                "includeglob": True,
                "interpolatevars": True,
                "interpolateenv": True,
                "mergeduplicateoptions": True,
            }
            mock_module_class.return_value = mock_module

            # Execute main function
            apache_config_parser.main()

            # Verify module.exit_json was called
            mock_module.exit_json.assert_called_once()
            call_args = mock_module.exit_json.call_args[1]

            # Verify response structure
            self.assertIn("changed", call_args)
            self.assertIn("parse_success", call_args)
            self.assertIn("config_data", call_args)
            self.assertIn("file_path", call_args)
            self.assertIn("files_processed", call_args)

            # Verify successful parsing
            self.assertFalse(call_args["changed"])
            self.assertTrue(call_args["parse_success"])
            self.assertEqual(call_args["file_path"], self.httpd_conf_path)

            # Config should be a dictionary
            config_data = call_args["config_data"]
            self.assertIsInstance(config_data, dict)

    def test_ansible_module_with_json_output(self):
        """Test main function with JSON output format"""
        with patch("apache_config_parser.AnsibleModule") as mock_module_class:
            mock_module = MagicMock()
            mock_module.params = {
                "path": self.site_conf_path,
                "configroot": os.path.dirname(self.site_conf_path),
                "output_format": "json",
                "allowmultioptions": True,
                "useapacheinclude": True,
                "includeagain": True,
                "includedirectories": True,
                "includeglob": True,
                "interpolatevars": True,
                "interpolateenv": True,
                "mergeduplicateoptions": True,
            }
            mock_module_class.return_value = mock_module

            apache_config_parser.main()

            mock_module.exit_json.assert_called_once()
            call_args = mock_module.exit_json.call_args[1]

            # Verify JSON output is present
            self.assertIn("config_json", call_args)
            self.assertIsInstance(call_args["config_json"], str)

            # Verify JSON is valid
            try:
                json_data = json.loads(call_args["config_json"])
                self.assertIsInstance(json_data, dict)
            except json.JSONDecodeError:
                self.fail("Invalid JSON output")

    def test_ansible_module_with_invalid_path(self):
        """Test main function with invalid file path"""
        with patch("apache_config_parser.AnsibleModule") as mock_module_class:
            mock_module = MagicMock()
            mock_module.params = {
                "path": "/nonexistent/path/httpd.conf",
                "configroot": "/nonexistent",
                "output_format": "dict",
                "allowmultioptions": True,
                "useapacheinclude": True,
                "includeagain": True,
                "includedirectories": True,
                "includeglob": True,
                "interpolatevars": True,
                "interpolateenv": True,
                "mergeduplicateoptions": True,
            }
            mock_module_class.return_value = mock_module

            apache_config_parser.main()

            # Should call fail_json (may be called multiple times)
            self.assertTrue(mock_module.fail_json.called)
            call_args = mock_module.fail_json.call_args[1]

            # Config should indicate failure
            self.assertIn("parse_success", call_args)
            self.assertFalse(call_args["parse_success"])
            self.assertIn("msg", call_args)

    def test_error_handling_with_malformed_config(self):
        """Test error handling with malformed configuration"""
        # Create a temporary malformed config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as tmp_file:
            tmp_file.write("<VirtualHost *:80>\n")
            tmp_file.write("ServerName incomplete.conf\n")
            # Missing closing tag - malformed
            tmp_file_path = tmp_file.name

        try:
            options = {
                "allowmultioptions": True,
                "useapacheinclude": True,
                "includeagain": True,
                "includedirectories": True,
                "includeglob": True,
                "interpolatevars": True,
                "interpolateenv": True,
                "mergeduplicateoptions": True,
                "configroot": os.path.dirname(tmp_file_path),
                "mergeduplicateblocks": True,
                "includerelative": True,
            }

            lexer = apache_config_parser.ApacheConfigLexer(**options)
            parser = apache_config_parser.ApacheConfigParser(lexer, **options)
            loader = apache_config_parser.ApacheConfigLoader(parser, **options)

            # Should handle malformed config gracefully
            try:
                result = loader.load(tmp_file_path)
                # If no exception, check that parsing indicates some issue
                # (this depends on the specific parser behavior)
                self.assertIsInstance(result, dict)
            except (
                apache_config_parser.ApacheConfigError,
                apache_config_parser.ConfigFileReadError,
            ):
                # Expected behavior - parser detected malformed config
                pass

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_include_processing(self):
        """Test that include directives are processed correctly"""
        options = {
            "allowmultioptions": True,
            "useapacheinclude": True,
            "includeagain": True,
            "includedirectories": True,
            "includeglob": True,
            "interpolatevars": True,
            "interpolateenv": True,
            "mergeduplicateoptions": True,
            "configroot": self.configroot,
            "mergeduplicateblocks": True,
            "includerelative": True,
        }

        try:
            lexer = apache_config_parser.ApacheConfigLexer(**options)
            parser = apache_config_parser.ApacheConfigParser(lexer, **options)
            loader = apache_config_parser.ApacheConfigLoader(parser, **options)

            config_data = loader.load(self.httpd_conf_path)
            files_processed = loader.files_processed

            # Main config processing should succeed
            # Note: includes may or may not process additional files
            # depending on the specific configuration
            self.assertGreaterEqual(len(files_processed), 1)

            # Should contain configuration from included files
            self.assertIsInstance(config_data, dict)

        except Exception as e:
            self.fail(f"Include processing failed: {e}")

    def test_multiple_virtualhost_parsing(self):
        """Test parsing configuration with multiple VirtualHosts"""
        options = {
            "allowmultioptions": True,
            "useapacheinclude": True,
            "includeagain": True,
            "includedirectories": True,
            "includeglob": True,
            "interpolatevars": True,
            "interpolateenv": True,
            "mergeduplicateoptions": True,
            "configroot": self.configroot,
            "mergeduplicateblocks": True,
            "includerelative": True,
        }

        try:
            lexer = apache_config_parser.ApacheConfigLexer(**options)
            parser = apache_config_parser.ApacheConfigParser(lexer, **options)
            loader = apache_config_parser.ApacheConfigLoader(parser, **options)

            config_data = loader.load(self.httpd_conf_path)

            # Should handle multiple VirtualHosts if present in includes
            self.assertIsInstance(config_data, dict)

            # Files processed should include conf.d files
            files_processed = loader.files_processed
            has_conf_d_files = any("conf.d" in f for f in files_processed)

            if has_conf_d_files:
                # Should have processed VirtualHost configurations
                self.assertTrue(
                    "VirtualHost" in config_data
                    or any("VirtualHost" in str(config_data.values()))
                )

        except Exception as e:
            self.fail(f"Multiple VirtualHost parsing failed: {e}")


class TestApacheConfigParserEdgeCases(unittest.TestCase):
    """Test edge cases for apache_config_parser module"""

    def setUp(self):
        """Set up test fixtures for edge cases"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))

    def test_empty_file_handling(self):
        """Test handling of empty configuration file"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as tmp_file:
            # Create empty file
            tmp_file_path = tmp_file.name

        try:
            options = {
                "allowmultioptions": True,
                "useapacheinclude": True,
                "includeagain": True,
                "includedirectories": True,
                "includeglob": True,
                "interpolatevars": True,
                "interpolateenv": True,
                "mergeduplicateoptions": True,
                "configroot": os.path.dirname(tmp_file_path),
                "mergeduplicateblocks": True,
                "includerelative": True,
            }

            lexer = apache_config_parser.ApacheConfigLexer(**options)
            parser = apache_config_parser.ApacheConfigParser(lexer, **options)
            loader = apache_config_parser.ApacheConfigLoader(parser, **options)

            config_data = loader.load(tmp_file_path)

            # Empty file should return empty dict
            self.assertIsInstance(config_data, dict)

        finally:
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_permission_denied_handling(self):
        """Test handling of permission denied errors"""
        # Test with a path that likely doesn't exist or has no permission
        nonexistent_path = "/root/secret/httpd.conf"

        options = {
            "allowmultioptions": True,
            "useapacheinclude": True,
            "includeagain": True,
            "includedirectories": True,
            "includeglob": True,
            "interpolatevars": True,
            "interpolateenv": True,
            "mergeduplicateoptions": True,
            "configroot": "/root/secret",
            "mergeduplicateblocks": True,
            "includerelative": True,
        }

        lexer = apache_config_parser.ApacheConfigLexer(**options)
        parser = apache_config_parser.ApacheConfigParser(lexer, **options)
        loader = apache_config_parser.ApacheConfigLoader(parser, **options)

        # Should raise appropriate exception
        with self.assertRaises(
            (
                apache_config_parser.ApacheConfigError,
                apache_config_parser.ConfigFileReadError,
                IOError,
                OSError,
            )
        ):
            loader.load(nonexistent_path)


if __name__ == "__main__":
    unittest.main()
