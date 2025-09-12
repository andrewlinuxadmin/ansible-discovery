# nginx_config_parser

Parse NGINX configuration files into structured data

## Synopsis

- Parses NGINX configuration files and returns structured JSON data
- Based on [nginx-crossplane library](https://github.com/nginxinc/crossplane) but completely standalone
- Supports file includes, comments preservation, and multiple output formats
- Can output in readable nginx-like format or technical crossplane format
- Handles complex NGINX configurations with nested blocks and includes

## Requirements

The below requirements are needed on the host that executes this module.

- python >= 2.7

## Parameters

| Parameter | Choices/Defaults | Comments |
|-----------|------------------|----------|
| **path**<br>*path* / *required* | | Path to the main NGINX configuration file to parse<br>Must be an existing file accessible by the module |
| **include_comments**<br>*boolean* | **Choices:**<br>- no ← (default)<br>- yes | Whether to include comments in the parsed output<br>Comments are preserved with line information when enabled<br>Useful for configuration analysis and documentation purposes |
| **single_file**<br>*boolean* | **Choices:**<br>- no ← (default)<br>- yes | Parse only the specified file, ignoring all include directives<br>When false, processes all included files recursively<br>Useful for analyzing individual configuration files in isolation |
| **ignore_directives**<br>*list* / *elements=string* | **Default:**<br>[] | List of directive names to ignore during parsing<br>Ignored directives will not appear in the output<br>Useful for security purposes to exclude sensitive data<br>Directive names are case-sensitive |
| **strict**<br>*boolean* | **Choices:**<br>- no ← (default)<br>- yes | Enable strict parsing mode for configuration validation<br>When true, unknown directives cause parsing to fail<br>When false, unknown directives are processed as-is<br>Recommended for production configuration validation |
| **combine**<br>*boolean* | **Choices:**<br>- no ← (default)<br>- yes | Combine all included files into a single configuration structure<br>When true, includes are expanded inline in crossplane format<br>When false, maintains separate file structures with references<br>Technical feature for crossplane compatibility |
| **crossplane_format**<br>*boolean* | **Choices:**<br>- no ← (default)<br>- yes | Controls the output format of the parsed configuration<br>When false (default), returns readable nginx-like hierarchical format<br>When true, returns technical crossplane format with parsing metadata<br>Crossplane format includes line numbers, file references, and include IDs<br>Readable format expands includes and creates clean hierarchical structure |

## Notes

- This module is completely standalone and self-contained
- Does not require external nginx-crossplane library installation
- Compatible with Python 2.7+ and Python 3.x environments
- Preserves all NGINX directive semantics and syntax rules
- Handles complex scenarios like globbed includes and deeply nested blocks
- Default output format prioritizes human readability with expanded includes

## See Also

- [NGINX Configuration Reference](https://nginx.org/en/docs/) - Official NGINX configuration documentation
- [nginx-crossplane project](https://github.com/nginxinc/crossplane) - Original library this module is based on

## Examples

```yaml
# Basic parsing of main NGINX configuration file
- name: Parse main nginx configuration in readable format
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
  register: nginx_config

# Parsing with comments preservation
- name: Parse nginx configuration with comments included
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    include_comments: true
  register: nginx_config_with_comments

# Parse single file without processing includes
- name: Parse individual site configuration file
  nginx_config_parser:
    path: /etc/nginx/sites-available/default
    single_file: true
  register: site_config

# Security-conscious parsing with sensitive directives ignored
- name: Parse configuration while ignoring sensitive data
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    ignore_directives:
      - ssl_certificate_key
      - ssl_password_file
      - auth_basic_user_file
      - auth_jwt_key_file
  register: secure_config

# Strict parsing mode for validation
- name: Validate configuration with strict mode
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    strict: true
  register: validated_config

# Technical crossplane format output
- name: Get technical crossplane format with metadata
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    crossplane_format: true
  register: technical_config

# Combined configuration with all includes expanded
- name: Parse with combined includes in crossplane format
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    combine: true
    crossplane_format: true
  register: combined_config

# Example of conditional logic based on parsing results
- name: Check for specific server configurations
  debug:
    msg: "Found {{ nginx_config.config.http.server | length }} servers"
  when:
    - nginx_config.config.status == 'ok'
    - nginx_config.config.http is defined
    - nginx_config.config.http.server is defined

# Example error handling
- name: Handle parsing errors gracefully
  debug:
    msg: "Configuration parsing failed: {{ nginx_config.errors | join(', ') }}"
  when: nginx_config.config.status == 'failed'

# Working with parsed data - Extract server names
- name: Extract all server names from configuration
  set_fact:
    server_names: "{{ nginx_config.config.http.server | 
                     map(attribute='server_name') | 
                     list | 
                     flatten }}"
  when: 
    - nginx_config.config.status == 'ok'
    - nginx_config.config.http.server is defined

# Working with parsed data - Find SSL configurations
- name: Find servers with SSL enabled
  set_fact:
    ssl_servers: "{{ nginx_config.config.http.server | 
                     selectattr('ssl_certificate', 'defined') | 
                     list }}"
  when: 
    - nginx_config.config.status == 'ok'
    - nginx_config.config.http.server is defined
```

## Return Values

Common return values are documented [here](https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html#common-return-values), the following are the fields unique to this module:

| Key | Returned | Description |
|-----|----------|-------------|
| **config**<br>*dictionary* | success | Parsed nginx configuration structure<br>Format varies based on crossplane_format parameter<br>When crossplane_format=false (default), returns readable hierarchical format with expanded includes<br>When crossplane_format=true, returns technical crossplane format with parsing metadata |
| **config.status**<br>*string* | always | Overall parsing status (ok or failed)<br>**Sample:** "ok" |
| **config.errors**<br>*list* | always | List of parsing errors encountered<br>**Sample:** [] |
| **config.config**<br>*dictionary* | success | Configuration content structure<br>In readable format, contains expanded directives<br>In crossplane format, contains list of parsed files |
| **changed**<br>*boolean* | always | Always false as this module only reads configuration<br>**Sample:** false |
| **errors**<br>*list* | always | Alias for config.errors for backward compatibility<br>**Sample:** [] |

### Sample Return Values

#### Readable Format (crossplane_format=false)

```json
{
    "changed": false,
    "config": {
        "status": "ok",
        "errors": [],
        "config": {
            "events": {
                "worker_connections": "1024"
            },
            "http": {
                "include": "mime.types",
                "server": [
                    {
                        "listen": "80",
                        "server_name": "example.com",
                        "location": [
                            {
                                "match": "/",
                                "root": "/var/www/html",
                                "index": "index.html"
                            }
                        ]
                    }
                ]
            }
        }
    },
    "errors": []
}
```

#### Crossplane Format (crossplane_format=true)

```json
{
    "changed": false,
    "config": {
        "status": "ok",
        "errors": [],
        "config": [
            {
                "file": "/etc/nginx/nginx.conf",
                "status": "ok",
                "errors": [],
                "parsed": [
                    {
                        "directive": "events",
                        "line": 1,
                        "args": [],
                        "block": [
                            {
                                "directive": "worker_connections",
                                "line": 2,
                                "args": ["1024"],
                                "block": null
                            }
                        ]
                    },
                    {
                        "directive": "http",
                        "line": 5,
                        "args": [],
                        "block": [
                            {
                                "directive": "server",
                                "line": 6,
                                "args": [],
                                "block": [
                                    {
                                        "directive": "listen",
                                        "line": 7,
                                        "args": ["80"],
                                        "block": null
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    },
    "errors": []
}
```

## Format Comparison

### Readable Format Features
- **Human-friendly structure**: Hierarchical organization matching NGINX logical structure
- **Expanded includes**: All included files are processed and merged into the main structure
- **Clean syntax**: Removes parsing metadata for easier data manipulation
- **Ansible-optimized**: Perfect for use with Ansible filters and conditional logic
- **Default choice**: Recommended for most automation scenarios

### Crossplane Format Features
- **Technical precision**: Maintains exact parsing information including line numbers
- **File separation**: Keeps track of which directives come from which files
- **Include tracking**: Preserves include relationships and file references
- **Debugging support**: Useful for configuration validation and error tracking
- **Library compatibility**: Compatible with original nginx-crossplane output

## Usage Patterns

### Configuration Validation

```yaml
- name: Validate NGINX configuration syntax
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    strict: true
  register: validation_result
  failed_when: validation_result.config.status != 'ok'
```

### Security Auditing

```yaml
- name: Parse configuration excluding sensitive data
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    ignore_directives:
      - ssl_certificate_key
      - ssl_password_file
      - auth_basic_user_file
      - auth_jwt_key_file
      - secure_link_secret
  register: audit_config
```

### Server Inventory

```yaml
- name: Build inventory of all configured servers
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
  register: nginx_parsed

- name: Extract server information
  set_fact:
    nginx_servers: "{{ nginx_parsed.config.http.server | 
                       map('dict2items') | 
                       map('selectattr', 'key', 'in', ['server_name', 'listen', 'root']) | 
                       map('items2dict') | 
                       list }}"
  when: nginx_parsed.config.status == 'ok'
```

### Configuration Migration

```yaml
- name: Parse old configuration
  nginx_config_parser:
    path: /etc/nginx/nginx.conf.old
  register: old_config

- name: Parse new configuration  
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
  register: new_config

- name: Compare configurations
  debug:
    msg: "Configuration changes detected"
  when: old_config.config.config != new_config.config.config
```

## Error Handling

The module provides comprehensive error handling with detailed error messages:

### Common Error Scenarios

1. **File not found**: When the specified configuration file doesn't exist
2. **Permission denied**: When the module can't read the configuration file
3. **Syntax errors**: When the NGINX configuration contains syntax errors
4. **Include failures**: When included files can't be found or parsed
5. **Unknown directives**: When strict mode is enabled and unknown directives are found

### Error Response Format

```json
{
    "config": {
        "status": "failed",
        "errors": [
            {
                "error": "file not found",
                "file": "/etc/nginx/missing.conf",
                "line": 0
            }
        ],
        "config": {}
    }
}
```

## Performance Considerations

- **Large configurations**: The module handles large configurations efficiently
- **Deep includes**: Processes deeply nested include structures without issues
- **Memory usage**: Readable format uses more memory due to include expansion
- **Processing time**: Crossplane format is faster as it doesn't expand includes

## Security Notes

- **Sensitive data**: Use `ignore_directives` to exclude sensitive information
- **File access**: Module requires read access to all configuration files
- **Include paths**: Follows include directives which may access unexpected files
- **Validation**: Use `strict` mode for production configuration validation

## Author

- Ansible Community

## License

This module is distributed under the same license as the nginx-crossplane project (Apache 2.0).
