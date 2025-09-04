# apache_config_parser

Parse Apache HTTP Server configuration files with full include support.

## Synopsis

- Parse Apache HTTP Server configuration files including all directives, VirtualHosts, and included files
- Support for all Apache configuration constructs including conditional blocks, includes, and complex nested structures
- Based on the `apacheconfig` Python library with full feature compatibility
- Returns structured data suitable for configuration auditing, validation, and automation

## Requirements

The below requirements are needed on the host that executes this module.

- python >= 2.7
- apacheconfig

## Parameters

| Parameter                          | Choices/Defaults                                                           | Comments                                                                                                      |
|------------------------------------|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **path** <br>*string* / *required*      | | Path to the main Apache configuration file (typically httpd.conf or apache2.conf)                            |
| **configroot** <br>*string* / *required* | | Root directory for Apache configuration files. This is used to resolve relative paths in Include directives. |
| **output_format** <br>*string*         | **Choices:** <ul><li>dict *(default)*</li><li>json</li></ul>             | Format for the returned configuration data                                                                    |
| **allowmultioptions** <br>*boolean*    | **Default:** yes                                                          | Allow multiple occurrences of the same configuration directive                                               |
| **useapacheinclude** <br>*boolean*     | **Default:** yes                                                          | Process Apache Include and IncludeOptional directives                                                        |
| **includeagain** <br>*boolean*         | **Default:** yes                                                          | Allow the same file to be included multiple times                                                             |
| **includedirectories** <br>*boolean*   | **Default:** yes                                                          | Allow including entire directories                                                                            |
| **includeglob** <br>*boolean*          | **Default:** yes                                                          | Support glob patterns in Include directives                                                                  |
| **interpolatevars** <br>*boolean* | **Default:** yes | Interpolate variables defined in the configuration |
| **interpolateenv** <br>*boolean* | **Default:** yes | Interpolate environment variables |
| **mergeduplicateoptions** <br>*boolean* | **Default:** yes | Merge duplicate options into lists |

## Notes

- The `configroot` parameter is critical for proper Include directive processing. It should point to the Apache installation's configuration root directory (e.g., `/etc/httpd` on RHEL/CentOS or `/etc/apache2` on Debian/Ubuntu).
- All boolean parameters default to `yes` to provide the most comprehensive parsing by default.
- This module is read-only and will never modify configuration files.
- The module requires the `apacheconfig` Python library to be installed on the target host.

## Examples

```yaml
- name: Parse main Apache configuration
  apache_config_parser:
    path: /etc/httpd/conf/httpd.conf
    configroot: /etc/httpd
  register: apache_config

- name: Display parsed VirtualHosts
  debug:
    msg: "Found VirtualHost: {{ item.key }} -> {{ item.value.ServerName | default('unnamed') }}"
  loop: "{{ apache_config.config_data.VirtualHost | dict2items }}"
  when: apache_config.config_data.VirtualHost is defined

- name: Parse configuration without includes
  apache_config_parser:
    path: /etc/httpd/conf/httpd.conf
    configroot: /etc/httpd
    useapacheinclude: no
    includedirectories: no
    includeglob: no

- name: Get configuration as JSON string
  apache_config_parser:
    path: /etc/apache2/apache2.conf
    configroot: /etc/apache2
    output_format: json
  register: apache_json

- name: Save configuration to file
  copy:
    content: "{{ apache_json.config_data }}"
    dest: /tmp/apache_config.json
```

## Return Values

| Key | Returned | Description |
|-----|----------|-------------|
| **changed** <br>*boolean* | always | Always `false` since this module only reads configuration |
| **config_data** <br>*dictionary* or *string* | success | Parsed Apache configuration data. Format depends on `output_format` parameter |
| **file_path** <br>*string* | always | Path to the main configuration file that was parsed |
| **files_processed** <br>*list* | always | List of all configuration files that were processed, including included files |
| **parse_success** <br>*boolean* | always | Whether the parsing operation completed successfully |
| **msg** <br>*string* | failure | Error message when parsing fails |

### Example Return Values

```yaml
{
    "changed": false,
    "config_data": {
        "ServerRoot": "/etc/httpd",
        "Listen": "80",
        "User": "apache",
        "Group": "apache",
        "VirtualHost": {
            "*:80": {
                "ServerName": "www.example.com",
                "DocumentRoot": "/var/www/html",
                "Directory": {
                    "/var/www/html": {
                        "Options": "Indexes FollowSymLinks",
                        "AllowOverride": "All"
                    }
                }
            },
            "192.168.1.10:443": {
                "ServerName": "secure.example.com",
                "DocumentRoot": "/var/www/secure",
                "SSLEngine": "on"
            }
        },
        "IfModule": {
            "mod_dir.c": {
                "DirectoryIndex": "index.html index.php"
            }
        }
    },
    "file_path": "/etc/httpd/conf/httpd.conf",
    "files_processed": [
        "/etc/httpd/conf/httpd.conf",
        "/etc/httpd/conf.d/ssl.conf",
        "/etc/httpd/conf.d/welcome.conf"
    ],
    "parse_success": true
}
```

## Configuration Structure

The returned configuration data follows Apache's hierarchical structure:

### Global Directives
```yaml
config_data:
  ServerRoot: "/etc/httpd"
  Listen: "80"
  User: "apache"
  Group: "apache"
```

### VirtualHosts
```yaml
config_data:
  VirtualHost:
    "*:80":
      ServerName: "www.example.com"
      DocumentRoot: "/var/www/html"
      Directory:
        "/var/www/html":
          Options: "Indexes FollowSymLinks"
          AllowOverride: "All"
```

### Conditional Blocks
```yaml
config_data:
  IfModule:
    "mod_ssl.c":
      LoadModule: "ssl_module modules/mod_ssl.so"
      SSLEngine: "on"
```

### Directory Blocks
```yaml
config_data:
  Directory:
    "/var/www":
      Options: "Indexes FollowSymLinks"
      AllowOverride: "None"
      Require: "all granted"
```

## Troubleshooting

### VirtualHosts Not Found
If VirtualHosts are not appearing in the output:
1. Verify that `configroot` points to the correct Apache configuration directory
2. Ensure `useapacheinclude` is set to `yes` (default)
3. Check that VirtualHost configurations are in included files that are readable
4. Verify file permissions allow reading of included configuration files

### Include Processing Issues
If included files are not being processed:
1. Confirm `configroot` parameter is set correctly
2. Check that Include directives use paths relative to `configroot` or absolute paths
3. Verify that `includedirectories` and `includeglob` are enabled if needed
4. Ensure included files and directories exist and are readable

### Module Execution Errors
If the module fails to execute:
1. Install the required Python library: `pip install apacheconfig`
2. Verify Python interpreter compatibility (Python 2.7+ or 3.x)
3. Check that the main configuration file exists and is readable
4. Ensure Ansible can execute Python modules on the target host

## Authors

- Apache Config Parser Module Implementation

## License

Compatible with the original apacheconfig library license.

---

**Collection:** Not part of any collection
**Supported by:** Community
**Status:** Preview

Based on the project ApacheConfig at https://github.com/etingof/apacheconfig
