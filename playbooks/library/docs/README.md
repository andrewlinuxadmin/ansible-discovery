# Custom Ansible Modules Documentation

This directory contains documentation for custom Ansible modules used in the
ansible-discovery project.

## Available Modules

### process_facts

**Purpose:** System process discovery via `/proc` filesystem with container detection

- **Dependencies:** None (pure Python implementation)
- **Compatibility:** Python 2.7+/3.x
- **Documentation:** [process_facts.md](process_facts.md)

**Key Features:**

- Container detection and classification
- Comprehensive process information extraction
- No external dependencies required
- Cross-platform compatibility

**Usage:**

```yaml
- name: Discover system processes
  process_facts:
  register: system_processes
```

### apache_config_parser

**Purpose:** Complete Apache HTTP Server configuration parsing with include support

- **Dependencies:** `apacheconfig` Python library
- **Compatibility:** Python 2.7+/3.x
- **Documentation:** [apache_config_parser.md](apache_config_parser.md)

**Key Features:**

- Full Apache configuration parsing including includes
- VirtualHost and Directory block extraction
- Conditional block processing (IfModule, etc.)
- Structured data output for automation

**Usage:**

```yaml
- name: Parse Apache configuration
  apache_config_parser:
    path: /etc/httpd/conf/httpd.conf
    configroot: /etc/httpd
  register: apache_config
```

### nginx_config_parser

**Purpose:** Complete NGINX configuration parsing with include expansion and multiple output formats

- **Dependencies:** None (completely standalone, based on nginx-crossplane)
- **Compatibility:** Python 2.7+/3.x
- **Documentation:** [nginx_config_parser.md](nginx_config_parser.md)

**Key Features:**

- Standalone implementation with no external dependencies
- Full NGINX configuration parsing including includes and globbed patterns
- Two output formats: readable hierarchical and technical crossplane format
- Security-conscious parsing with directive filtering capabilities
- Strict validation mode for production environments
- Comments preservation with line number information

**Usage:**

```yaml
- name: Parse NGINX configuration in readable format
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
  register: nginx_config

- name: Parse with security filtering
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    ignore_directives:
      - ssl_certificate_key
      - ssl_password_file
  register: secure_nginx_config
```

### php_config_parser

**Purpose:** PHP configuration discovery and parsing across multiple distributions

- **Dependencies:** None (pure Python implementation)
- **Compatibility:** Python 2.7+/3.x
- **Documentation:** [php_config_parser.md](php_config_parser.md)

**Key Features:**

- Multi-distribution support (RHEL/CentOS, Debian/Ubuntu)
- Smart discovery of PHP configuration directories and versions
- Comprehensive parsing of php.ini and additional .ini files
- Extension detection and configuration extraction
- SCL (Software Collections) package support

**Usage:**

```yaml
- name: Discover and parse PHP configurations
  php_config_parser:
  register: php_configs

- name: Parse specific PHP version
  php_config_parser:
    php_version: "8.1"
    include_additional_ini: true
  register: php81_config
```

## Installation Requirements

### System Requirements

- Ansible 2.9+ (modules are placed in `playbooks/library/` directory)
- Python 2.7+ or Python 3.x on target hosts

### Python Dependencies

Install required Python libraries on target hosts:

```bash
# For apache_config_parser module
pip install apacheconfig

# process_facts, nginx_config_parser, and php_config_parser have no external dependencies
```

## Module Development Guidelines

When creating or modifying custom modules:

1. **Documentation:** Create comprehensive markdown documentation following
   Ansible standards
2. **Testing:** Include unit tests and integration tests
3. **Code Quality:** Maintain high standards with linting tools (flake8,
   pylint, black)
4. **Dependencies:** Document all external dependencies clearly
5. **Examples:** Provide practical usage examples in documentation

## Directory Structure

```text
playbooks/library/
├── docs/                        # Module documentation
│   ├── README.md               # This file
│   ├── process_facts.md        # process_facts module documentation
│   ├── apache_config_parser.md # apache_config_parser module documentation
│   ├── nginx_config_parser.md  # nginx_config_parser module documentation
│   └── php_config_parser.md    # php_config_parser module documentation
├── tests/                      # Module tests
├── process_facts.py            # Process discovery module
├── apache_config_parser.py     # Apache config parsing module
├── nginx_config_parser.py      # NGINX config parsing module
└── php_config_parser.py        # PHP config parsing module
```

## Related Documentation

- [Project Main README](../../../README.md)
- [Custom Ansible Filters](../../filter_plugins/README.md)
- [GitHub Copilot Instructions](../../../.github/copilot-instructions.md)
