# Ansible Discovery System - Technical Architecture

## Overview

The Ansible Discovery System implements a modular, selective collection
architecture with custom modules, intelligent caching, and cross-platform
compatibility. The system prioritizes modern module-based approaches while
maintaining fallback mechanisms for legacy environments.

## Core Architecture

### Main Components

```text
discovery.yaml (orchestrator)
├── prereqs.yaml (selective collection configuration)
├── process_facts (custom module - process discovery)
├── collectors/*.yaml (conditional system discovery)
└── custom modules (configuration parsing)
```

### Execution Flow

1. **Prerequisites**: Configure selective collection variables with absolute precedence
2. **Process Collection**: Gather running processes using custom `process_facts` module
3. **System Discovery**: Execute enabled collectors conditionally based on `_collector_*` variables
4. **Application Discovery**: Java/Apache/PHP based on detected processes and custom modules
5. **Data Consolidation**: Store all facts as cached JSON files with configurable TTL

## Selective Collection System

### Variable Precedence Logic

The system implements **absolute precedence** for `collector_only`:

```yaml
_collector_java: "{{ (collector_only == 'java') if collector_only is defined
                    else (collector_java | default(true) | bool) }}"
```

### Precedence Matrix

| Scenario  | `collector_only`  | Individual flags        | Result                    |
|-----------|-------------------|-------------------------|---------------------------|
| Absolute  | `java`            | Ignored                 | Only Java collector runs  |
| Default   | Undefined         | Default `true`          | All collectors run        |
| Selective | Undefined         | `collector_java=false`  | All except Java run       |

## Custom Modules Architecture

### Module Design Principles

1. **Standalone**: Minimal external dependencies
2. **Cross-platform**: Python 2.7+ and 3.x compatibility
3. **Comprehensive**: Full parsing with error handling
4. **Cacheable**: Results stored via Ansible fact caching for performance

### Module Specifications

#### process_facts.py

- **Purpose**: Replace AWK-based process parsing with native Python
- **Implementation**: Direct `/proc` filesystem reading
- **Features**: Container detection, comprehensive process information
- **Dependencies**: None (pure Python)
- **Output**: Structured process list with PID, command, args, user, etc.

#### apache_config_parser.py

- **Purpose**: Complete Apache configuration parsing
- **Implementation**: Uses `apacheconfig` library for robust parsing
- **Features**: Include directive processing, VirtualHost extraction, conditional blocks
- **Dependencies**: `apacheconfig` Python package
- **Output**: Hierarchical configuration structure

#### nginx_config_parser.py

- **Purpose**: Complete NGINX configuration parsing
- **Implementation**: Standalone parser based on nginx-crossplane
- **Features**: Two output formats (readable/crossplane), security filtering, include processing
- **Dependencies**: None (completely standalone)
- **Output**: Configurable format - readable hierarchical or technical crossplane

#### php_config_parser.py

- **Purpose**: Multi-distribution PHP configuration discovery
- **Implementation**: Pure Python with smart discovery algorithms
- **Features**: Auto-discovery, SCL support, multi-version handling
- **Dependencies**: None (pure Python)
- **Output**: Configuration files list with settings and extensions

## Data Flow Architecture

### Discovery Pipeline

```text
ansible-playbook discovery.yaml
├── prereqs.yaml → Configure selective collection variables
├── process_facts → Collect all system processes
├── System Collectors (conditional)
│   ├── packages.yaml → ansible.builtin.package_facts
│   ├── services.yaml → ansible.builtin.service_facts
│   └── ports.yaml → community.general.listen_ports_facts
└── Application Collectors (process-based)
    ├── java/ → Process classification + discovery
    ├── apache.yaml → apache_config_parser module
    ├── nginx.yaml → nginx_config_parser module
    └── php.yaml → php_config_parser module
```

### Fact Caching

Facts are stored as one JSON file per host using the built-in `jsonfile` plugin:

```ini
# ansible.cfg
fact_caching = ansible.builtin.jsonfile
fact_caching_timeout = 0
fact_caching_connection = ./facts_cache
```

- **Storage**: `playbooks/facts_cache/<hostname>` (one file per host, auto-created)
- **TTL**: Configurable (default: 0 = infinite)
- **Performance**: Subsequent runs skip discovery if cached data exists
- **Management**: `rm facts_cache/<hostname>` to clear a host; `rm -rf facts_cache/*` to clear all

## Hybrid Collection Pattern

All system collectors follow this standard pattern:

```yaml
# 1. Try official role
- name: Try official collection method
  fedora.linux_system_roles.MODULE_facts: {}
  register: result
  ignore_errors: true

# 2. Manual fallback
- name: Fallback manual method
  shell: |
    echo '{"key": "value", "source": "manual"}'
  register: manual_result
  when: result is failed

# 3. Container detection
- name: Container-specific handling
  when: container_detected

# 4. Fact setting
- name: Set facts
  set_fact:
    MODULE_info: "{{ parsed_result }}"
    cacheable: true
```

## Available Collectors

| Collector  | Official Module          | Fallback Method                  | Container Aware |
|------------|--------------------------|----------------------------------|-----------------|
| packages   | `package_facts`          | `dpkg -l` / `rpm -qa`           | Yes             |
| services   | `service_facts`          | `systemctl` / `chkconfig`       | Yes             |
| ports      | `listen_ports_facts`     | `/proc/net/tcp` parsing          | Yes             |
| firewall   | `firewall_lib_facts`     | `iptables -L` / `firewall-cmd`  | Yes             |
| bootloader | `bootloader_facts`       | `grub.cfg` parsing               | Yes             |
| selinux    | `selinux_modules_facts`  | `getenforce` / `sestatus`        | Yes             |
| blockdev   | `blockdev_info`          | `lsblk` / `fdisk -l`            | Yes             |
| java       | Process-based            | Command line parsing             | Yes             |
| apache     | Process-based            | Config file analysis             | Yes             |
| nginx      | Process-based            | Server blocks, PHP-FPM detection | Yes             |

## Java Discovery Pipeline

```text
1. java.yaml: Process classification (tomcat/jboss/jar)
2. Detection: Set has_*_processes flags
3. Conditional includes: tomcat.yaml, jboss.yaml, jar.yaml
4. Consolidation: Merge into unified java_processes structure
```

## HTML Report Generator

The `ansible-discovery-report.py` script generates a comprehensive HTML report
from collected facts. See [DOCS.md](DOCS.md) for full documentation.

## Technical Specifications

### Required Collections

- `ansible.posix`
- `community.general`
- `fedora.linux_system_roles`

### System Requirements

- **Target Systems**: Linux (RHEL, Debian, SUSE families)
- **Control Node**: Ansible 2.9+, Python 3.9+
- **Network**: SSH connectivity to target hosts
- **Permissions**: Sudo access for system discovery

### Development Status

| Component             | Status      | Notes                              |
|-----------------------|-------------|------------------------------------|
| Process Facts Module  | Production  | Replaces AWK scripts               |
| Apache Config Parser  | Production  | Full configuration parsing         |
| PHP Config Parser     | Production  | Multi-distribution support         |
| NGINX Config Parser   | Production  | Complete with PHP-FPM detection    |
| Selective Collection  | Production  | Absolute precedence implemented    |
| JSON File Caching     | Production  | Built-in, no external dependencies |
| Custom Filters        | Production  | File operation filters             |
| HTML Report Generator | Production  | Configurable via INI file          |
