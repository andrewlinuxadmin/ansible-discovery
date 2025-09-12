# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ansible Discovery Project
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import re
import glob
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: php_config_parser

short_description: Parse PHP configuration files

version_added: "1.0.0"

description:
    - Parse PHP configuration files (php.ini and additional .ini files)
    - Discover PHP configuration directories and files automatically
    - Extract PHP settings, extensions, and configuration sections
    - Support for multiple PHP versions and installation paths

options:
    paths:
        description:
            - List of specific PHP configuration file paths to parse
            - If not provided, will auto-discover common PHP config locations
        required: false
        type: list
        elements: str
    php_version:
        description:
            - Specific PHP version to look for (e.g., "7.4", "8.1")
            - If not provided, will search for all versions
        required: false
        type: str
    include_additional_ini:
        description:
            - Whether to include additional .ini files from conf.d directories
        required: false
        type: bool
        default: true

author:
    - Ansible Discovery Project

requirements:
    - Python 2.7+ or Python 3.x

notes:
    - This module does not modify any files, only reads and parses them
    - Supports common PHP configuration file formats
    - Handles commented and uncommented settings
"""

EXAMPLES = r"""
# Parse all PHP configuration files automatically
- name: Parse PHP configuration
  php_config_parser:
  register: php_config

# Parse specific PHP configuration file
- name: Parse specific php.ini
  php_config_parser:
    paths:
      - /etc/php.ini
  register: php_config

# Parse PHP 8.1 configuration only
- name: Parse PHP 8.1 configuration
  php_config_parser:
    php_version: "8.1"
  register: php_config

# Parse main config only, skip additional .ini files
- name: Parse main php.ini only
  php_config_parser:
    include_additional_ini: false
  register: php_config
"""

RETURN = r"""
config_files:
    description: List of PHP configuration files found and parsed
    type: list
    returned: always
    elements: dict
    contains:
        path:
            description: Full path to the configuration file
            type: str
        exists:
            description: Whether the file exists and was readable
            type: bool
        size:
            description: File size in bytes
            type: int
        sections:
            description: List of INI sections found in the file
            type: list
            elements: dict
            contains:
                name:
                    description: Name of the INI section
                    type: str
                settings:
                    description: Dictionary of key-value pairs in this section
                    type: dict
        extensions:
            description: List of PHP extensions configured
            type: list
        errors:
            description: List of parsing errors encountered
            type: list

php_summary:
    description: Summary of PHP configuration across all files
    type: dict
    returned: always
    contains:
        total_files:
            description: Total number of config files processed
            type: int
        main_config:
            description: Path to main php.ini file
            type: str
        php_version:
            description: Detected PHP version from config
            type: str
        memory_limit:
            description: Configured memory limit
            type: str
        max_execution_time:
            description: Configured max execution time
            type: str
        all_extensions:
            description: All configured PHP extensions
            type: list
        config_directories:
            description: List of configuration directories found
            type: list
"""


class PHPConfigParser:
    """PHP Configuration Parser"""

    def __init__(self, module):
        self.module = module
        self.paths = module.params.get("paths", [])
        self.php_version = module.params.get("php_version")
        self.include_additional_ini = module.params.get("include_additional_ini", True)
        self.config_files = []
        self.errors = []

    def get_default_php_paths(self):
        """Get default PHP configuration file paths to search"""
        default_paths = []

        # RHEL/CentOS pattern: /etc/php.ini
        rhel_paths = [
            "/etc/php.ini",
            "/usr/local/etc/php/php.ini",
            "/opt/lampp/etc/php.ini",
        ]

        # Add RHEL variants with specific versions in /opt/rh/
        rhel_version_patterns = [
            "/opt/rh/rh-php{version_no_dot}/root/etc/php.ini",
        ]

        # Only check specific versions for RHEL if specified
        if self.php_version:
            version_no_dot = self.php_version.replace(".", "")
            for pattern in rhel_version_patterns:
                path = pattern.format(version_no_dot=version_no_dot)
                rhel_paths.append(path)

        default_paths.extend(rhel_paths)

        # Debian/Ubuntu pattern: discover existing directories first
        debian_paths = self._discover_debian_php_paths()
        default_paths.extend(debian_paths)

        return default_paths

    def _discover_debian_php_paths(self):
        """Discover PHP paths for Debian/Ubuntu by checking existing
        directories"""
        debian_paths = []

        # Check if /etc/php exists (Debian/Ubuntu pattern)
        php_base_dir = "/etc/php"
        if not os.path.isdir(php_base_dir):
            return debian_paths

        try:
            # Get all version directories in /etc/php/
            version_dirs = []
            for item in os.listdir(php_base_dir):
                version_path = os.path.join(php_base_dir, item)
                if os.path.isdir(version_path) and re.match(r"^\d+\.\d+$", item):
                    version_dirs.append(item)

            # If specific version requested, filter to that version
            if self.php_version and self.php_version in version_dirs:
                version_dirs = [self.php_version]

            # Build paths for discovered versions
            for version in version_dirs:
                debian_paths.extend(
                    [
                        "/etc/php/{}/apache2/php.ini".format(version),
                        "/etc/php/{}/cli/php.ini".format(version),
                        "/etc/php/{}/fpm/php.ini".format(version),
                    ]
                )

        except OSError:
            # If we can't read the directory, try to discover versions
            # dynamically from other common locations
            discovered_versions = self._discover_versions_from_system()

            # If no versions discovered and no specific version requested,
            # we'll just skip the fallback (return empty debian_paths)
            if not discovered_versions and not self.php_version:
                pass  # No versions found, return what we have
            elif self.php_version:
                # If specific version requested, use it regardless
                discovered_versions = [self.php_version]
            # else: use discovered_versions as-is

            for version in discovered_versions:
                debian_paths.extend(
                    [
                        "/etc/php/{}/apache2/php.ini".format(version),
                        "/etc/php/{}/cli/php.ini".format(version),
                        "/etc/php/{}/fpm/php.ini".format(version),
                    ]
                )

        return debian_paths

    def _discover_versions_from_system(self):
        """Discover PHP versions dynamically from system directories"""
        discovered_versions = []

        # Common locations where PHP versions might be found
        search_locations = [
            "/etc/php",  # Debian/Ubuntu
            "/usr/bin",  # Look for php binaries
            "/usr/local/bin",  # Alternative binary location
            "/opt/rh",  # RHEL Software Collections
        ]

        # Pattern to match version numbers (e.g., 7.4, 8.1, 8.2)
        version_pattern = re.compile(r"^\d+\.\d+$")

        for location in search_locations:
            if not os.path.isdir(location):
                continue

            try:
                if location == "/etc/php":
                    # Debian/Ubuntu style: /etc/php/7.4, /etc/php/8.1, etc.
                    for item in os.listdir(location):
                        if os.path.isdir(
                            os.path.join(location, item)
                        ) and version_pattern.match(item):
                            if item not in discovered_versions:
                                discovered_versions.append(item)

                elif location in ["/usr/bin", "/usr/local/bin"]:
                    # Look for php binaries like php7.4, php8.1, etc.
                    for item in os.listdir(location):
                        if item.startswith("php") and len(item) > 3:
                            version_part = item[3:]  # Remove 'php' prefix
                            if version_pattern.match(version_part):
                                if version_part not in discovered_versions:
                                    discovered_versions.append(version_part)

                elif location == "/opt/rh":
                    # RHEL Software Collections: /opt/rh/rh-php74, etc.
                    for item in os.listdir(location):
                        if item.startswith("rh-php") or item.startswith("php"):
                            # Extract version from rh-php74 -> 7.4
                            version_match = re.search(r"php(\d)(\d+)", item)
                            if version_match:
                                major, minor = version_match.groups()
                                version = "{}.{}".format(major, minor)
                                if version not in discovered_versions:
                                    discovered_versions.append(version)

            except OSError:
                # If we can't read a directory, just continue
                continue

        # Sort versions for consistent output
        discovered_versions.sort()

        # If no versions found, return empty list (caller should handle)
        return discovered_versions

    def get_additional_ini_paths(self, main_config_dir):
        """Get additional .ini files from conf.d directories"""
        if not self.include_additional_ini:
            return []

        additional_paths = []

        # RHEL/CentOS pattern: /etc/php.d/*.ini
        rhel_conf_dirs = [
            "/etc/php.d",
            os.path.join(main_config_dir, "conf.d"),
        ]

        # Debian/Ubuntu pattern: discover existing conf.d directories
        debian_conf_dirs = self._discover_debian_conf_dirs()

        # Combine all directories
        all_conf_dirs = rhel_conf_dirs + debian_conf_dirs

        # Find .ini files in all conf.d directories
        for conf_dir in all_conf_dirs:
            if os.path.isdir(conf_dir):
                ini_files = glob.glob(os.path.join(conf_dir, "*.ini"))
                additional_paths.extend(ini_files)

        return additional_paths

    def _discover_debian_conf_dirs(self):
        """Discover conf.d directories for Debian/Ubuntu"""
        conf_dirs = []

        # Check if /etc/php exists (Debian/Ubuntu pattern)
        php_base_dir = "/etc/php"
        if not os.path.isdir(php_base_dir):
            return conf_dirs

        try:
            # Get all version directories in /etc/php/
            for item in os.listdir(php_base_dir):
                version_path = os.path.join(php_base_dir, item)
                if os.path.isdir(version_path) and re.match(r"^\d+\.\d+$", item):
                    # Add conf.d directories for this version
                    conf_dirs.extend(
                        [
                            "/etc/php/{}/apache2/conf.d".format(item),
                            "/etc/php/{}/cli/conf.d".format(item),
                            "/etc/php/{}/fpm/conf.d".format(item),
                        ]
                    )

        except OSError:
            # If we can't read the directory, return empty list
            pass

        return conf_dirs

    def parse_ini_file(self, file_path):
        """Parse a single PHP INI file"""
        result = {
            "path": file_path,
            "exists": False,
            "size": 0,
            "sections": [],
            "extensions": [],
            "errors": [],
        }

        try:
            if not os.path.exists(file_path):
                return result

            result["exists"] = True
            result["size"] = os.path.getsize(file_path)

            with open(file_path, "r") as f:
                content = f.read()
                # Handle encoding issues in Python 2/3
                if isinstance(content, bytes):
                    content = content.decode("utf-8", errors="ignore")

            # Parse content line by line
            current_section = "PHP"  # Default section
            sections_dict = {}

            for line_num, line in enumerate(content.split("\n"), 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith(";") or line.startswith("#"):
                    continue

                # Check for section headers
                section_match = re.match(r"^\[(.*?)\]$", line)
                if section_match:
                    current_section = section_match.group(1)
                    if current_section not in sections_dict:
                        sections_dict[current_section] = {}
                    continue

                # Parse setting lines
                setting_match = re.match(r"^([^=;#]+?)\s*=\s*(.*)$", line)
                if setting_match:
                    key = setting_match.group(1).strip()
                    value = setting_match.group(2).strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Initialize section if it doesn't exist
                    if current_section not in sections_dict:
                        sections_dict[current_section] = {}

                    # Store setting in the appropriate section
                    sections_dict[current_section][key] = value

                    # Collect extensions
                    if key == "extension":
                        result["extensions"].append(value)

            # Convert sections dict to array format
            result["sections"] = []
            for section_name, section_settings in sections_dict.items():
                result["sections"].append(
                    {"name": section_name, "settings": section_settings}
                )

        except Exception as e:
            error_msg = "Error parsing {}: {}".format(file_path, str(e))
            result["errors"].append(error_msg)
            self.errors.append(error_msg)

        return result

    def get_php_summary(self, config_files):
        """Generate summary of PHP configuration"""
        summary = {
            "total_files": len(config_files),
            "main_config": None,
            "php_version": "unknown",
            "memory_limit": "unknown",
            "max_execution_time": "unknown",
            "all_extensions": [],
            "config_directories": [],
        }

        # Find main config file (usually the largest or /etc/php.ini)
        main_candidates = [
            cf for cf in config_files if cf["exists"] and "php.ini" in cf["path"]
        ]
        if main_candidates:
            main_config = max(main_candidates, key=lambda x: x["size"])
            summary["main_config"] = main_config["path"]

        # Collect all settings and extensions
        all_settings = {}
        all_extensions = set()
        config_dirs = set()

        for config_file in config_files:
            if config_file["exists"]:
                # Extract settings from sections array
                for section in config_file["sections"]:
                    section_name = section["name"]
                    section_settings = section["settings"]

                    # Add settings with section prefix if not PHP section
                    for key, value in section_settings.items():
                        if section_name != "PHP":
                            full_key = "{}.{}".format(section_name, key)
                        else:
                            full_key = key
                        all_settings[full_key] = value

                all_extensions.update(config_file["extensions"])
                config_dirs.add(os.path.dirname(config_file["path"]))

        # Extract key settings
        summary["memory_limit"] = all_settings.get("memory_limit", "unknown")
        summary["max_execution_time"] = all_settings.get(
            "max_execution_time", "unknown"
        )
        summary["all_extensions"] = sorted(list(all_extensions))
        summary["config_directories"] = sorted(list(config_dirs))

        # Try to detect PHP version from path
        for config_file in config_files:
            if config_file["exists"]:
                version_match = re.search(r"/php/(\d+\.\d+)/", config_file["path"])
                if version_match:
                    summary["php_version"] = version_match.group(1)
                    break

        return summary

    def run(self):
        """Main execution method"""
        try:
            # Determine which files to parse
            if self.paths:
                files_to_parse = self.paths
            else:
                files_to_parse = self.get_default_php_paths()

            # Parse main configuration files
            config_files = []
            additional_ini_paths = set()

            for file_path in files_to_parse:
                result = self.parse_ini_file(file_path)
                config_files.append(result)

                # If this is a main config file, look for additional .ini files
                if result["exists"] and "php.ini" in file_path:
                    main_config_dir = os.path.dirname(file_path)
                    additional_paths = self.get_additional_ini_paths(main_config_dir)
                    additional_ini_paths.update(additional_paths)

            # Parse additional .ini files
            for additional_path in additional_ini_paths:
                existing_paths = [cf["path"] for cf in config_files]
                if additional_path not in existing_paths:
                    result = self.parse_ini_file(additional_path)
                    config_files.append(result)

            # Generate summary
            php_summary = self.get_php_summary(config_files)

            return {
                "changed": False,
                "config_files": config_files,
                "php_summary": php_summary,
                "errors": self.errors,
            }

        except Exception as e:
            error_msg = "Failed to parse PHP configuration: {}".format(str(e))
            self.module.fail_json(msg=error_msg)


def main():
    module_args = dict(
        paths=dict(type="list", elements="str", required=False, default=[]),
        php_version=dict(type="str", required=False),
        include_additional_ini=dict(type="bool", required=False, default=True),
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    parser = PHPConfigParser(module)
    result = parser.run()

    module.exit_json(**result)


if __name__ == "__main__":
    main()
