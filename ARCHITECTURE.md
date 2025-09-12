# Ansible Discovery System - Technical Architecture

## Overview

The Ansible Discovery System implements a modular, selective collection architecture with custom modules, intelligent caching, and cross-platform compatibility. The system prioritizes modern module-based approaches while maintaining fallback mechanisms for legacy environments.

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
5. **Data Consolidation**: Store all facts in MongoDB with configurable TTL

## Selective Collection System

### Variable Precedence Logic

The system implements **absolute precedence** for `collector_only`:

```yaml
# Logic in prereqs.yaml:
_collector_java: "{{ (collector_only == 'java') if collector_only is defined 
                    else (collector_java | default(true) | bool) }}"
```

### Usage Patterns

```bash
# Single collector (absolute precedence) - only executes one collector
ansible-playbook discovery.yaml -e collector_only=java

# All collectors (default behavior) - executes all enabled collectors
ansible-playbook discovery.yaml

# Individual control (when collector_only not used) - granular control
ansible-playbook discovery.yaml -e collector_packages=false -e collector_services=false
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
4. **Cacheable**: Results stored in MongoDB for performance

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
- **Status**: 🚧 Module complete, collector integration in development

#### php_config_parser.py

- **Purpose**: Multi-distribution PHP configuration discovery
- **Implementation**: Pure Python with smart discovery algorithms
- **Features**: Auto-discovery, SCL support, multi-version handling
- **Dependencies**: None (pure Python)
- **Output**: Configuration files list with settings and extensions

### Module Integration Pattern

```yaml
# Modern collector pattern using custom modules
- name: Parse PHP configurations
  php_config_parser:
  register: php_config_raw

- name: Create PHP facts
  ansible.builtin.set_fact:
    php_info: "{{ php_config_raw }}"
    cacheable: true
```

## Data Flow Architecture

### Discovery Pipeline

```text
ansible-playbook discovery.yaml
├── prereqs.yaml → Configure selective collection variables
├── process_facts → Collect all system processes
├── System Collectors (conditional)
│   ├── packages.yaml → fedora.linux_system_roles.packages
│   ├── services.yaml → fedora.linux_system_roles.services
│   └── ports.yaml → community.general.listen_ports_facts
└── Application Collectors (process-based)
    ├── java/ → Process classification + discovery
    ├── apache.yaml → apache_config_parser module
    ├── nginx.yaml → nginx_config_parser module (production)
    └── php.yaml → php_config_parser module
```

### Caching Strategy

- **Storage**: MongoDB with configurable TTL
- **Connection**: `mongodb://localhost:27017/ansible`
- **Collection**: `cache` with document structure `{_id: "ansible_facts<hostname>", data: {...}}`
- **TTL**: Configurable (default: 0 = infinite)
- **Performance**: Subsequent runs skip discovery if cached data exists

## Performance Architecture

### Optimization Strategies

1. **Selective Collection**: Use `collector_only` to run specific collectors
2. **MongoDB Caching**: Avoid re-discovery with persistent caching
3. **Custom Modules**: Replace shell scripts with efficient Python modules
4. **Conditional Execution**: Skip collectors when processes not detected
5. **Custom Filters**: Use `file_exists` filter vs. multiple `stat` calls

### Development Status

| Component             | Status          | Notes                                   |
|-----------------------|-----------------|-----------------------------------------|
| Process Facts Module  | ✅ Production   | Replaces AWK scripts                    |
| Apache Config Parser  | ✅ Production   | Full configuration parsing              |
| PHP Config Parser     | ✅ Production   | Multi-distribution support              |
| NGINX Config Parser   | ✅ Production   | Complete with PHP-FPM detection        |
| Selective Collection  | ✅ Production   | Absolute precedence implemented         |
| MongoDB Caching       | ✅ Production   | TTL-based with performance optimization |
| Custom Filters        | ✅ Production   | File operation filters                  |

## Technical Specifications

### Dependencies

#### Required Collections

- `ansible.posix`
- `community.general`
- `community.mongodb`
- `fedora.linux_system_roles`

#### Python Dependencies

- **Core**: Python 2.7+ or 3.x
- **apache_config_parser**: `apacheconfig` package
- **Other modules**: No external dependencies

### System Requirements

- **Target Systems**: Linux (RHEL, Debian, SUSE families)
- **Control Node**: Ansible 2.9+, Python 3.9+
- **Database**: MongoDB (local or remote)
- **Network**: SSH connectivity to target hosts
- **Permissions**: Sudo access for system discovery

### Hybrid Collection Pattern

All collectors follow this standard pattern:

```yaml
# 1. Try official role
- name: Try official collection method
  fedora.linux_system_roles.MODULE_facts: {}
  register: result
  ignore_errors: true

# 2. Manual fallback
- name: Fallback manual method
  shell: |
    # JSON output generation
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

### Standard JSON Output

```json
{
  "source": "fedora.linux_system_roles|manual|container",
  "status": "active|inactive|unknown",
  "note": "additional_context_when_applicable"
}
```

## Available Collectors

| Collector | Official Module | Fallback Method | Container Aware |
|-----------|-----------------|-----------------|-----------------|
| packages | `package_facts` | `dpkg -l` / `rpm -qa` | ✓ |
| services | `service_facts` | `systemctl` / `chkconfig` | ✓ |
| ports | `listen_ports_facts` | `/proc/net/tcp` parsing | ✓ |
| firewall | `firewall_lib_facts` | `iptables -L` / `firewall-cmd` | ✓ |
| bootloader | `bootloader_facts` | `grub.cfg` parsing | ✓ |
| selinux | `selinux_modules_facts` | `getenforce` / `sestatus` | ✓ |
| blockdev | `blockdev_info` | `lsblk` / `fdisk -l` | ✓ |
| java | Process-based | Command line parsing | ✓ |
| apache | Process-based | Config file analysis | ✓ |
| nginx | Process-based | Server blocks, PHP-FPM detection | ✓ |

## Java Discovery Pipeline

### Multi-Stage Process

```text
1. java.yaml: Process classification (tomcat/jboss/jar)
2. Detection: Set has_*_processes flags
3. Conditional includes: tomcat.yaml, jboss.yaml, jar.yaml
4. Consolidation: Merge into unified java_processes structure
```

### Process Classification

```yaml
# Classification logic
app_type: >-
  {{
    'tomcat' if 'catalina' in args or 'tomcat' in args else
    'jboss' if 'jboss' in args or 'wildfly' in args else
    'springboot' if 'spring' in args else
    'quarkus' if 'quarkus' in args else
    'java-app'
  }}
```

### Data Consolidation

Final `java_processes` structure includes:

- Basic process info (PID, user, command)
- Java version detection
- Application-specific data (tomcat_info, jboss_info, jar_info)
- Configuration file analysis
- Deployment information

## MongoDB Caching Strategy

### Configuration

```ini
# ansible.cfg
fact_caching = community.mongodb.mongodb
fact_caching_timeout = 0  # Infinite cache
fact_caching_connection = mongodb://localhost:27017/ansible
```

### Cache Usage

- All important facts use `cacheable: true`
- TTL=0 for development (infinite cache)
- Manual cleanup via MongoDB when needed
- Cache validation through subsequent runs

### Cache Inspection

```bash
# Connect to MongoDB
mongosh ansible

# List cached hosts
db.cache.find({}, {_id: 1}).toArray()

# Inspect specific host data
db.cache.findOne({_id: "ansible_facts<hostname>"}).data

# Clear cache
db.cache.drop()
```

## Custom Filters

### File Operation Filters

```python
# filter_plugins/file_utils.py
class FilterModule:
    def filters(self):
        return {
            "file_exists": self.file_exists,    # Regular file check
            "path_exists": self.path_exists,    # Any path check
            "file_readable": self.file_readable # Readable file check
        }
```

### Usage in Discovery

```yaml
# Conditional file processing
- name: Read Tomcat config
  slurp:
    src: "{{ tomcat_home }}/conf/server.xml"
  when: "{{ tomcat_home }}/conf/server.xml" | file_readable

# JAR file detection
- name: Find application JAR
  set_fact:
    jar_path: "{{ candidates | select('file_exists') | first | default('unknown') }}"
  vars:
    candidates:
      - "{{ app_home }}/lib/app.jar"
      - "{{ app_home }}/app.jar"
```

## Error Handling Strategy

### Graceful Degradation

1. **Try official modules first** (best data quality)
2. **Fall back to manual collection** (maintains functionality)
3. **Detect containers** (adjust expectations)
4. **Provide meaningful defaults** (avoid failures)

### Container Detection

```bash
# Standard container detection
if [ -f /.dockerenv ] || grep -q "docker\|lxc\|podman" /proc/1/cgroup 2>/dev/null; then
  echo '{"status": "container", "note": "managed_by_host"}'
```

### Cross-Platform Support

- **RHEL Family**: Primary target with full feature support
- **Debian Family**: Tested fallback methods
- **SUSE Family**: Basic compatibility
- **Containers**: Adjusted behavior and expectations

## Performance Optimizations

### Process Efficiency

- Custom `process_facts` module with kernel thread exclusion
- PID-based mapping for efficient correlation
- JSON parsing optimized with AWK in shell commands

### Conditional Execution

- `include_tasks` for runtime evaluation
- Process detection before expensive analysis
- Container detection for automatic skip

## Development Guidelines

### Code Standards

```yaml
# Required patterns
- name: Descriptive task name
  module: 
    param: value
  register: result
  failed_when: false      # For discovery tasks
  changed_when: false     # For fact collection
  no_log: "{{ not log }}" # For verbose output
  when: condition         # For conditional execution

- name: Set facts
  set_fact:
    fact_name: "{{ value }}"
    cacheable: true       # Required for important facts
```

### Testing Requirements

1. **Syntax validation**: `ansible-playbook --syntax-check`
2. **Dry run testing**: `--check --diff`
3. **Selective testing**: `-e collector_only=MODULE`
4. **Debug validation**: `-e debug=true`
5. **Cache verification**: MongoDB inspection

### Documentation Standards

- Update collector table when adding new modules
- Include JSON output examples
- Document container behavior differences
- Provide usage examples for new features
