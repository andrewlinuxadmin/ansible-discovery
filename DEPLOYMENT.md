# Deployment and Operations Guide

## Prerequisites

### System Requirements

- **Control Node**: Ansible 2.9+, Python 3.9+, MongoDB
- **Target Hosts**: Linux (RHEL/CentOS, Ubuntu/Debian, SUSE)
- **Network**: SSH connectivity to target hosts
- **Permissions**: Sudo access on targets for complete discovery

### Collection Dependencies

```bash
# Install required Ansible collections
cd playbooks/
ansible-galaxy collection install -r galaxy-requirements.yaml
```

### Python Environment

```bash
# From project root
source activate  # Activates virtual environment
pip install -r pip-venv-requirements.txt
```

### MongoDB Setup

```bash
# Local MongoDB (recommended for development)
systemctl start mongod

# Docker alternative
docker run -d -p 27017:27017 --name ansible-mongo mongo:latest
```

## Quick Start

### Basic Deployment

```bash
# Navigate to playbooks directory
cd playbooks/

# Copy and configure inventory
cp inventory.example inventory
# Edit inventory with your target hosts

# Full discovery (all collectors)
ansible-playbook discovery.yaml

# Single collector (selective)
ansible-playbook discovery.yaml -e collector_only=java

# Debug mode with verbose output
ansible-playbook discovery.yaml -e debug=true -e log=true
```

### Verification

```bash
# Check MongoDB cache
mongosh ansible
> db.cache.find({}, {_id: 1}).toArray()
> exit

# Validate custom modules
ansible localhost -m process_facts
ansible localhost -m php_config_parser
```

## Configuration

### Inventory Setup

```ini
# inventory
[production]
web1.company.com ansible_user=ansible
web2.company.com ansible_user=ansible
db1.company.com ansible_user=ansible

[development]
dev1.company.com ansible_user=root
localhost ansible_connection=local

[containers]
app-container ansible_connection=docker
```

### Ansible Configuration

```ini
# ansible.cfg
[defaults]
inventory = inventory
host_key_checking = False
gathering = smart
fact_caching = community.mongodb.mongodb
fact_caching_timeout = 0
fact_caching_connection = mongodb://localhost:27017/ansible
filter_plugins = ./filter_plugins

[inventory]
enable_plugins = host_list, script, auto, yaml, ini

[privilege_escalation]
become = True
become_method = sudo
become_user = root
```

### Variable Configuration

```yaml
# group_vars/all.yml
# System collectors
collector_packages: true
collector_services: true
collector_ports: true
collector_firewall: true
collector_bootloader: true
collector_selinux: true
collector_blockdev: true

# Application collectors
collector_java: true
collector_apache: true
collector_nginx: true    # Note: Module in development
collector_php: true

# Output control
debug: false
log: false
```

## Production Deployment

### Security Considerations

- **SSH Keys**: Use key-based authentication instead of passwords
- **Sudo Access**: Configure passwordless sudo for automation accounts
- **Network**: Restrict MongoDB access to control nodes only
- **Data**: Consider TTL settings for sensitive cached data

### Performance Tuning

```yaml
# For large environments
forks = 50
host_key_checking = False
gathering = smart
fact_caching_timeout = 86400  # 24 hours instead of infinite
```

### Selective Collection Strategy

```bash
# For large-scale deployments, use selective collection
# Infrastructure discovery
ansible-playbook discovery.yaml -e collector_only=packages -l production

# Application discovery
ansible-playbook discovery.yaml -e collector_only=java -l production

# Web server discovery
ansible-playbook discovery.yaml -e collector_only=apache -l web_servers
```

## Operations

### Cache Management

```bash
# Clear all cache
./scripts/clear-cache.sh

# Clear specific host
mongosh ansible --eval "db.cache.deleteOne({_id:'ansible_factshostname.domain.com'})"

# Check cache size
mongosh ansible --eval "db.stats()"
```

### Troubleshooting

#### Common Issues

1. **Module not found**: Ensure you're in `playbooks/` directory
2. **MongoDB connection**: Verify MongoDB is running on localhost:27017
3. **SSH failures**: Check inventory and SSH key configuration
4. **Permission denied**: Ensure sudo access is configured

#### Debug Commands

```bash
# Test connectivity
ansible all -m ping

# Check custom modules
ansible localhost -m apache_config_parser -a "path=/etc/httpd/conf/httpd.conf configroot=/etc/httpd"

# Validate syntax
ansible-playbook --syntax-check discovery.yaml

# Run with maximum verbosity
ansible-playbook discovery.yaml -vvv
```

### Monitoring and Maintenance

#### Health Checks

```bash
# Weekly: Validate modules
./filter_plugins/tests/run_tests.sh
./library/tests/run_tests.sh

# Monthly: Clear stale cache
mongosh ansible --eval "db.cache.drop()"

# As needed: Update collections
ansible-galaxy collection install -r galaxy-requirements.yaml --force
```

#### Log Analysis

```bash
# Enable detailed logging
ansible-playbook discovery.yaml -e log=true -e debug=true > discovery.log 2>&1

# Parse logs for errors
grep -i error discovery.log
grep -i failed discovery.log
```

## Advanced Operations

### Custom Module Development

```bash
# Development workflow
cd playbooks/

# 1. Create module in library/
vim library/new_module.py

# 2. Create documentation
vim library/docs/new_module.md

# 3. Update module index
vim library/docs/README.md

# 4. Create tests
vim library/tests/test_new_module.py

# 5. Run tests
./library/tests/run_tests.sh
```

### Filter Plugin Development

```bash
# 1. Add filter to file_utils.py
vim filter_plugins/file_utils.py

# 2. Update tests
vim filter_plugins/tests/test_file_utils.yaml

# 3. Run tests
./filter_plugins/tests/run_tests.sh

# 4. Update documentation
vim filter_plugins/README.md
```

### Collector Development

```bash
# 1. Create collector
vim collectors/new_collector.yaml

# 2. Add to discovery.yaml
vim discovery.yaml

# 3. Add variable to prereqs.yaml
vim prereqs.yaml

# 4. Test individually
ansible-playbook discovery.yaml -e collector_only=new_collector
```

## Status and Roadmap

### Current Status

- ✅ **Production Ready**: process_facts, apache_config_parser, php_config_parser, custom filters
- ✅ **Stable**: Selective collection system, MongoDB caching, system collectors
- 🚧 **In Development**: nginx_config_parser collector integration
- 📋 **Planned**: Docker support, .NET discovery, Python application discovery

### Known Limitations

- NGINX module complete but collector integration pending
- Docker container discovery in development
- Limited support for Windows targets
- Requires sudo access for complete system discovery

```yaml
# Secure inventory management
- name: Production inventory encryption
  vars:
    ansible_ssh_private_key_file: "{{ vault_ssh_key_path }}"
    ansible_become_pass: "{{ vault_sudo_password }}"
  
# Vault integration
ansible-vault create group_vars/production.yml
ansible-vault edit group_vars/production.yml
```

### Performance Optimization

```ini
# ansible.cfg for production
[defaults]
forks = 50
poll_interval = 1
timeout = 30
gathering = smart
fact_caching_timeout = 3600  # 1 hour cache

[ssh_connection]
ssh_args = -C -o ControlMaster=auto -o ControlPersist=300s
pipelining = True
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
```

### Batch Processing

```bash
# Process multiple environments
for env in dev staging prod; do
  ansible-playbook discovery.yaml -i inventories/$env -e environment=$env
done

# Parallel execution with limits
ansible-playbook discovery.yaml -l "batch1" --forks=10
ansible-playbook discovery.yaml -l "batch2" --forks=10
```

## Cache Management

### MongoDB Operations

```bash
## Status and Roadmap

### Current Status

- ✅ **Production Ready**: process_facts, apache_config_parser, php_config_parser, custom filters
- ✅ **Stable**: Selective collection system, MongoDB caching, system collectors
- 🚧 **In Development**: nginx_config_parser collector integration
- 📋 **Planned**: Docker support, .NET discovery, Python application discovery

### Known Limitations

- NGINX module complete but collector integration pending
- Docker container discovery in development
- Limited support for Windows targets
- Requires sudo access for complete system discovery
```

### Cache Statistics

```bash
# Cache size and statistics
db.stats()
db.cache.stats()

# Count cached hosts
db.cache.countDocuments()

# Find large cache entries
db.cache.find({}, {_id: 1, size: {$bsonSize: "$$ROOT"}}).sort({size: -1}).limit(10)
```

## Monitoring and Troubleshooting

### Log Analysis

```bash
# Enable verbose logging
export ANSIBLE_LOG_PATH=/var/log/ansible-discovery.log
ansible-playbook discovery.yaml -vvv

# Real-time log monitoring
tail -f /var/log/ansible-discovery.log

# Error filtering
grep -i "error\|failed\|fatal" /var/log/ansible-discovery.log
```

### Performance Monitoring

```yaml
# Add timing to playbooks
- name: Start discovery timer
  set_fact:
    discovery_start_time: "{{ ansible_date_time.epoch }}"

- name: Calculate discovery duration
  set_fact:
    discovery_duration: "{{ ansible_date_time.epoch | int - discovery_start_time | int }}"
    cacheable: true
```

### Health Checks

```bash
# Verify MongoDB connectivity
ansible localhost -m shell -a "mongosh --eval 'db.runCommand({ping: 1})'"

# Test collection dependencies
ansible-galaxy collection list | grep -E "fedora.linux_system_roles|community.mongodb"

# Validate inventory
ansible-inventory --list --yaml

# Test connectivity
ansible all -m ping -o
```

## Error Handling

### Common Issues and Solutions

#### Permission Denied

```yaml
# Solution: Graceful permission handling
- name: Try privileged operation
  command: "{{ privileged_command }}"
  register: privileged_result
  failed_when: false
  become: true

- name: Fallback unprivileged operation
  command: "{{ unprivileged_command }}"
  register: unprivileged_result
  when: privileged_result.rc != 0
```

#### Missing Dependencies

```yaml
# Solution: Dynamic dependency checking
- name: Check for required tools
  command: "which {{ item }}"
  register: tool_check
  failed_when: false
  loop:
    - systemctl
    - netstat
    - lsblk

- name: Set available tools
  set_fact:
    available_tools: "{{ tool_check.results | selectattr('rc', 'equalto', 0) | map(attribute='item') | list }}"
```

#### Container Detection Issues

```yaml
# Solution: Multi-method container detection
- name: Comprehensive container detection
  shell: |
    # Multiple detection methods
    if [ -f /.dockerenv ]; then
      echo "docker"
    elif [ -f /run/.containerenv ]; then
      echo "podman"
    elif grep -q "docker\|lxc\|containerd" /proc/1/cgroup 2>/dev/null; then
      echo "container"
    elif [ "${container:-}" = "docker" ] || [ "${container:-}" = "podman" ]; then
      echo "$container"
    else
      echo "host"
    fi
  register: container_detection
```

### Debugging Strategies

#### Debug Mode Usage

```bash
# Full debug output
ansible-playbook discovery.yaml -e debug=true -e log=true -vvv

# Specific collector debugging
ansible-playbook discovery.yaml -e collector_only=packages -e debug=true

# Step-by-step execution
ansible-playbook discovery.yaml --step
```

#### Manual Testing

```bash
# Test individual tasks
ansible localhost -m fedora.linux_system_roles.package_facts

# Test custom filters
ansible localhost -m debug -a "msg={{ '/etc/passwd' | file_exists }}"

# Test shell commands
ansible localhost -m shell -a "ps aux | grep java"
```

## Integration

### CI/CD Pipeline Integration

```yaml
# .gitlab-ci.yml example
discover_infrastructure:
  stage: discovery
  script:
    - ansible-galaxy collection install -r galaxy-requirements.yaml
    - ansible-playbook discovery.yaml -i production
  artifacts:
    reports:
      junit: discovery-results.xml
    paths:
      - discovery-results.json
    expire_in: 30 days
```

### API Integration

```python
# Python integration example
import subprocess
import json

def run_discovery(host, collector=None):
    cmd = ["ansible-playbook", "discovery.yaml", "-i", f"{host},"]
    if collector:
        cmd.extend(["-e", f"collector_only={collector}"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

# Usage
result = run_discovery("server1.example.com", "packages")
```

### Webhook Integration

```bash
# Webhook trigger script
#!/bin/bash
WEBHOOK_URL="https://api.example.com/webhook/discovery"
HOST="$1"
COLLECTOR="${2:-all}"

# Run discovery
ansible-playbook discovery.yaml -i "$HOST," -e "collector_only=$COLLECTOR" > /tmp/discovery.log 2>&1

# Send results
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"host\": \"$HOST\", \"status\": \"$?\", \"log\": \"$(cat /tmp/discovery.log | base64)\"}"
```

## Best Practices

### Development Workflow

```bash
# 1. Test syntax
ansible-playbook discovery.yaml --syntax-check

# 2. Dry run
ansible-playbook discovery.yaml --check --diff

# 3. Limited scope testing
ansible-playbook discovery.yaml -l test_hosts -e debug=true

# 4. Single collector validation
ansible-playbook discovery.yaml -e collector_only=packages

# 5. Production deployment
ansible-playbook discovery.yaml -i production
```

### Code Organization

```text
ansible-discovery/
├── playbooks/
│   ├── discovery.yaml          # Main orchestrator
│   ├── prereqs.yaml           # Variable configuration
│   └── inventory.example      # Sample inventory
├── collectors/                # System collectors
│   ├── packages.yaml
│   ├── services.yaml
│   └── ...
├── java/                      # Application-specific
│   ├── java.yaml
│   ├── tomcat.yaml
│   └── ...
├── webservers/               # Web server discovery
│   ├── apache.yaml
│   └── nginx.yaml
├── filter_plugins/           # Custom filters
│   └── file_utils.py
├── tests/                    # Test infrastructure
└── docs/                     # Documentation
```

### Version Control

```bash
# Git hooks for validation
#!/bin/bash
# .git/hooks/pre-commit
ansible-playbook --syntax-check playbooks/*.yaml
ansible-lint playbooks/*.yaml
markdownlint docs/*.md
```

### Documentation Standards

- Keep README files updated with architecture changes
- Document all custom variables and their defaults
- Provide working examples for each collector
- Include troubleshooting sections
- Maintain changelog for major updates

## Scaling Considerations

### Large Infrastructure

```ini
# ansible.cfg for large deployments
[defaults]
forks = 100
timeout = 60
gathering = smart
fact_caching_timeout = 7200  # 2 hours

[ssh_connection]
retries = 3
ssh_args = -C -o ControlMaster=auto -o ControlPersist=600s
```

### Resource Management

```yaml
# Memory optimization
- name: Clear large variables
  set_fact:
    large_variable: null
  when: processing_complete

# Disk space management
- name: Clean temporary files
  file:
    path: "{{ item }}"
    state: absent
  loop:
    - /tmp/ansible-discovery-*
    - /var/tmp/discovery-*
```

### Network Optimization

```yaml
# Batch operations
- name: Process hosts in batches
  include_tasks: batch_discovery.yaml
  vars:
    batch_hosts: "{{ groups['all'][batch_start:batch_end] }}"
  loop: "{{ range(0, groups['all']|length, batch_size) }}"
  loop_control:
    loop_var: batch_start
  vars:
    batch_end: "{{ [batch_start + batch_size, groups['all']|length] | min }}"
    batch_size: 10
```
