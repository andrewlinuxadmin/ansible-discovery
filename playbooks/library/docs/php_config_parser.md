# PHP Config Parser Module Documentation

## Overview

The `php_config_parser` module is a custom Ansible module designed to parse PHP configuration files across different Linux distributions. It automatically discovers PHP configuration files and extracts settings, extensions, and sections.

## Features

- **Multi-distribution support**: Optimized for RHEL/CentOS and Debian/Ubuntu patterns
- **Smart discovery**: Automatically finds PHP config directories instead of guessing versions
- **Comprehensive parsing**: Extracts settings, extensions, sections, and file information
- **Python 2/3 compatible**: Works with older systems (CentOS 6) and modern distributions

## Distribution-specific Behavior

### RHEL/CentOS/Fedora
- Main config: `/etc/php.ini`
- Additional configs: `/etc/php.d/*.ini`
- SCL packages: `/opt/rh/rh-php*/root/etc/php.ini`

### Debian/Ubuntu
- Main config: `/etc/php/<version>/apache2/php.ini`
- Additional configs: `/etc/php/<version>/apache2/conf.d/*.ini`
- **Smart discovery**: Scans `/etc/php/` to find existing version directories

## Module Parameters

| Parameter                | Type | Required | Default | Description                                |
|--------------------------|------|----------|---------|-------------------------------------------|
| `paths`                  | list | No       | []      | Specific PHP config file paths to parse   |
| `php_version`            | str  | No       | None    | Specific PHP version to look for           |
| `include_additional_ini` | bool | No       | true    | Include additional .ini files from conf.d |

## Return Values

### config_files
List of PHP configuration files found and parsed.

**Structure:**
```yaml
config_files:
  - path: "/etc/php.ini"
    exists: true
    size: 69097
    sections: ["PHP", "Session", "MySQL", ...]
    settings:
      memory_limit: "128M"
      max_execution_time: "30"
      # ... more settings
    extensions: ["json.so", "curl.so", ...]
    errors: []
```

### php_summary
Summary of PHP configuration across all files.

**Structure:**
```yaml
php_summary:
  total_files: 8
  main_config: "/etc/php.ini"
  php_version: "7.4"  # or "unknown"
  memory_limit: "128M"
  max_execution_time: "30"
  all_extensions: ["json.so", "curl.so", ...]
  config_directories: ["/etc", "/etc/php.d"]
```

## Usage Examples

### Basic Usage (Auto-discovery)
```yaml
- name: Parse PHP configuration
  php_config_parser:
  register: php_config

- name: Display summary
  debug:
    var: php_config.php_summary
```

### Specific Files Only
```yaml
- name: Parse specific PHP config
  php_config_parser:
    paths:
      - /etc/php.ini
      - /etc/php.d/custom.ini
  register: php_config
```

### Specific PHP Version (Debian/Ubuntu)
```yaml
- name: Parse PHP 8.1 configuration
  php_config_parser:
    php_version: "8.1"
  register: php_config
```

### Main Config Only
```yaml
- name: Parse main php.ini only
  php_config_parser:
    include_additional_ini: false
  register: php_config
```

## Integration with Discovery System

The module is designed to integrate with the ansible-discovery project:

```yaml
- name: Parse PHP configuration
  php_config_parser:
  register: php_config_result

- name: Store PHP configuration facts
  set_fact:
    cacheable: true
    php_configuration: "{{ php_config_result.php_summary }}"
    php_config_files: "{{ php_config_result.config_files }}"
```

## Error Handling

The module gracefully handles:
- Missing files (marked as `exists: false`)
- Permission errors (logged in `errors` array)
- Parsing errors (individual file errors logged)
- Directory access issues (falls back to common paths)

## Performance Optimizations

1. **Directory discovery**: Only checks existing directories on Debian/Ubuntu
2. **Lazy evaluation**: Skips non-existent paths quickly
3. **Efficient parsing**: Single-pass INI file parsing
4. **Minimal filesystem operations**: Uses os.path checks before file operations

## Testing

Test the module with:
```bash
ansible-playbook tests/test_php_ini_parser.yaml
```

## Compatibility

- **Python**: 2.7+ and 3.x
- **Ansible**: 2.9+
- **OS**: RHEL/CentOS 6+, Ubuntu 16.04+, Debian 9+

## Technical Notes

- Uses regex parsing for INI files instead of ConfigParser for better control
- Handles both quoted and unquoted values
- Preserves section hierarchy in setting names
- Compatible with older Python versions (no f-strings)
