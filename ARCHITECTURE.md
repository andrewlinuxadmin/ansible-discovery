# Ansible Discovery System - Technical Architecture

## Overview

The Ansible Discovery System implements a modular, selective collection architecture with hybrid discovery strategies and MongoDB caching.

## Core Architecture

### Main Components

```text
discovery.yaml (orchestrator)
├── prereqs.yaml (variables configuration)
├── process_facts (custom module)
├── collectors/* (system discovery)
└── conditional blocks (application discovery)
```

### Execution Flow

1. **Prerequisites**: Configure selective collection variables
2. **Process Collection**: Gather running processes using custom module
3. **System Discovery**: Execute enabled collectors conditionally
4. **Application Discovery**: Java/Apache/Nginx based on detected processes

## Selective Collection System

### Variable Precedence

```yaml
# Absolute precedence logic:
_collector_X = (collector_only == 'X') if collector_only is defined 
               else (collector_X | default(true) | bool)
```

### Usage Patterns

```bash
# Single collector (absolute precedence)
ansible-playbook discovery.yaml -e collector_only=java

# All collectors (default)
ansible-playbook discovery.yaml

# Individual control (when collector_only not used)
ansible-playbook discovery.yaml -e collector_packages=false
```

## Collector Architecture

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
| nginx | Process-based | Server block parsing | ✓ |

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

### Caching Strategy

- MongoDB persistence across runs
- Infinite TTL for development
- Selective cache invalidation support

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
