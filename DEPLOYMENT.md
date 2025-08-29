# Deployment and Operations Guide

## Quick Start

### Prerequisites

```bash
# Install required collections
ansible-galaxy collection install -r galaxy-requirements.yaml

# Configure Python environment (if needed)
pip install -r pip-venv-requirements.txt

# Start MongoDB (for caching)
systemctl start mongod
# or
docker run -d -p 27017:27017 --name ansible-mongo mongo:latest
```

### Basic Usage

```bash
# Full system discovery
ansible-playbook discovery.yaml

# Single collector
ansible-playbook discovery.yaml -e collector_only=packages

# Debug mode
ansible-playbook discovery.yaml -e debug=true -e log=true

# Specific host
ansible-playbook discovery.yaml -i "hostname," -e debug=true
```

## Configuration

### Inventory Setup

```ini
# inventory.example
[targets]
server1.example.com ansible_user=root
server2.example.com ansible_user=ansible ansible_become=true

[containers]
container1 ansible_connection=docker
container2 ansible_connection=podman

[development]
localhost ansible_connection=local
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

[inventory]
enable_plugins = host_list, script, auto, yaml, ini

[privilege_escalation]
become = False
become_method = sudo
become_user = root
```

### Variable Configuration

```yaml
# group_vars/all.yml
# Selective collection control
collector_packages: true
collector_services: true
collector_ports: true
collector_firewall: true
collector_bootloader: true
collector_selinux: true
collector_blockdev: true

# Output control
debug: false
log: false

# MongoDB settings
mongodb_host: localhost
mongodb_port: 27017
mongodb_database: ansible
```

## Production Deployment

### Security Configuration

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
# Connect to cache database
mongosh ansible

# View cached hosts
db.cache.find({}, {_id: 1}).toArray()

# Inspect specific host cache
db.cache.findOne({_id: "ansible_facts<hostname>"}).data

# Clear all cache
db.cache.drop()

# Clear specific host cache
db.cache.deleteOne({_id: "ansible_facts<hostname>"})

# Clear expired cache (if TTL > 0)
db.cache.deleteMany({timestamp: {$lt: new Date(Date.now() - 3600000)}})
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
