# Deployment and Operations Guide

## Prerequisites

### System Requirements

- **Control Node**: Ansible 2.9+, Python 3.9+
- **Target Hosts**: Linux (RHEL/CentOS, Ubuntu/Debian, SUSE)
- **Network**: SSH connectivity to target hosts
- **Permissions**: Sudo access on targets for complete discovery

### Collection Dependencies

```bash
cd playbooks/
ansible-galaxy collection install -r galaxy-requirements.yaml
```

### Python Environment

```bash
source activate
pip install -r pip-venv-requirements.txt
```

## Installation

```bash
# Clone and setup
git clone https://github.com/andrewlinuxadmin/ansible-discovery.git
cd ansible-discovery
source activate
pip install -r pip-venv-requirements.txt

# Configure Ansible
cd playbooks/
ansible-galaxy collection install -r galaxy-requirements.yaml
cp inventory.example inventory
# Edit inventory with your target hosts
```

## Running Discovery

```bash
cd playbooks/

# Full discovery (all collectors)
ansible-playbook discovery.yaml

# Selective discovery
ansible-playbook discovery.yaml -e collector_only=java

# Individual collector control
ansible-playbook discovery.yaml -e collector_packages=false -e collector_services=false

# Debug mode
ansible-playbook discovery.yaml -e debug=true -e log=true
```

Facts are cached as JSON files in `playbooks/facts_cache/` (created automatically).

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
```

### Ansible Configuration

```ini
# ansible.cfg
[defaults]
inventory = inventory
host_key_checking = False
gathering = smart
fact_caching = ansible.builtin.jsonfile
fact_caching_timeout = 0
fact_caching_connection = ./facts_cache
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
collector_packages: true
collector_services: true
collector_ports: true
collector_firewall: true
collector_bootloader: true
collector_selinux: true
collector_blockdev: true
collector_java: true
collector_apache: true
collector_nginx: true
collector_php: true

debug: false
log: false
```

## Cache Management

```bash
# List cached hosts
ls playbooks/facts_cache/

# View facts for a specific host
cat playbooks/facts_cache/server1.example.com | python3 -m json.tool

# Clear cache for a specific host
rm playbooks/facts_cache/server1.example.com

# Clear all cache
rm -rf playbooks/facts_cache/*
```

## Report Generation

After collecting facts, generate an HTML report:

```bash
# Default: reads export.json, produces ansible-discovery-report.html
python3 ansible-discovery-report.py

# Custom input/output
python3 ansible-discovery-report.py --config my.ini --input data.json --output report.html
```

See [DOCS.md](DOCS.md) for full report generator documentation.

## Production Deployment

### Security Considerations

- Use SSH key-based authentication
- Configure passwordless sudo for automation accounts
- Consider TTL settings for sensitive cached data
- Use Ansible Vault for credentials

```bash
ansible-vault create group_vars/production.yml
ansible-vault edit group_vars/production.yml
```

### Performance Tuning

```ini
# ansible.cfg for large environments
[defaults]
forks = 50
timeout = 30
gathering = smart
fact_caching_timeout = 86400  # 24 hours

[ssh_connection]
ssh_args = -C -o ControlMaster=auto -o ControlPersist=300s
pipelining = True
```

### Batch Processing

```bash
# Process multiple environments
for env in dev staging prod; do
  ansible-playbook discovery.yaml -i inventories/$env -e environment=$env
done

# Parallel execution with limits
ansible-playbook discovery.yaml -l "batch1" --forks=10
```

## Troubleshooting

### Common Issues

1. **Module not found**: Ensure you're in the `playbooks/` directory
2. **SSH failures**: Check inventory and SSH key configuration
3. **Permission denied**: Ensure sudo access is configured
4. **Stale cache**: Delete `facts_cache/` contents to force re-discovery

### Debug Commands

```bash
# Test connectivity
ansible all -m ping

# Check custom modules
ansible localhost -m process_facts
ansible localhost -m apache_config_parser -a "path=/etc/httpd/conf/httpd.conf configroot=/etc/httpd"

# Validate syntax
ansible-playbook --syntax-check discovery.yaml

# Run with maximum verbosity
ansible-playbook discovery.yaml -vvv

# Step-by-step execution
ansible-playbook discovery.yaml --step
```

### Log Analysis

```bash
# Enable detailed logging
export ANSIBLE_LOG_PATH=/var/log/ansible-discovery.log
ansible-playbook discovery.yaml -vvv

# Filter errors
grep -i "error\|failed\|fatal" /var/log/ansible-discovery.log
```
