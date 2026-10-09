# Ansible Discovery

Automated infrastructure discovery for Linux servers using Ansible.

Collects detailed information from servers running **RHEL, CentOS, or
Oracle Linux 6/7**. The collected data is used to identify which servers
can be converted to Red Hat Enterprise Linux and upgraded to supported
versions (8+). It also determines the impossibility or difficulty of
these migrations, preserving the operation of the applications running
on these servers.

The playbook is **read-only** — it does not alter, install, or remove
anything on the target servers.

## Prerequisites

A **RHEL 9** server as the control node. Install the required packages:

```bash
sudo dnf install -y git ansible-core python3-pip
```

SSH access and sudo on the target servers.

## Installation

```bash
git clone https://github.com/andrewlinuxadmin/ansible-discovery.git
cd ansible-discovery
pip install -r pip-venv-requirements.txt

cd playbooks
ansible-galaxy collection install -r galaxy-requirements.yaml
```

## Inventory

```bash
cp inventory.example inventory
```

Edit `inventory` with your target servers:

```ini
[servers]
server1.example.com
server2.example.com
10.0.1.50
```

If the SSH user differs from the local user, add `ansible_user`:

```ini
server1.example.com ansible_user=deploy
```

### SSH Connection

**Option A — SSH key (recommended):** No extra configuration needed.
The key from the control node is used automatically.

**Option B — Password:** Add `ansible_ssh_pass` to the inventory.
If the sudo password differs from the SSH password, also add
`ansible_become_pass`:

```ini
server1.example.com ansible_user=deploy ansible_ssh_pass=pass123 ansible_become_pass=sudopass
```

To set credentials for all hosts at once:

```ini
[servers:vars]
ansible_user=deploy
ansible_ssh_pass=pass123
ansible_become_pass=sudopass
```

## Running Discovery

From the `playbooks/` directory:

```bash
# All collectors
ansible-playbook discovery.yaml

# Single collector
ansible-playbook discovery.yaml -e collector_only=java

# Debug mode
ansible-playbook discovery.yaml -e debug=true -e log=true
```

> **Note:** Record any servers that fail during execution (connectivity,
> permission, or availability issues). This list should be sent along
> with the collected data.

### Available Collectors

| Collector    | Description                      |
|--------------|----------------------------------|
| `packages`   | Installed packages and versions  |
| `services`   | Service status and configuration |
| `ports`      | Network ports and listeners      |
| `java`       | Tomcat, JBoss, standalone JARs   |
| `apache`     | Apache HTTPD configuration       |
| `nginx`      | NGINX config and PHP-FPM         |
| `php`        | PHP versions and extensions      |
| `firewall`   | Firewall rules and zones         |
| `selinux`    | SELinux mode and policies        |
| `blockdev`   | Disks, mounts, filesystems       |
| `bootloader` | GRUB and kernel parameters       |

Use `collector_only=<name>` to run a single collector, or disable
individual ones with `-e collector_<name>=false`.

## Fact Cache

Facts are stored as one JSON file per host in `playbooks/facts_cache/`
(created automatically).

```bash
# View cached hosts
ls facts_cache/

# Inspect a host
cat facts_cache/server1.example.com | python3 -m json.tool

# Clear cache
rm -rf facts_cache/*
```

### Exporting Collected Data

To compress and send the collected facts:

```bash
cd playbooks
tar czf facts_cache.tar.gz facts_cache/
```

## HTML Report

Generate a report from collected facts:

```bash
# Read directly from facts_cache directory (default)
python3 ansible-discovery-report.py

# Or point to a specific directory
python3 ansible-discovery-report.py --input playbooks/facts_cache

# Or use a single JSON file (array of {_id, data} objects)
python3 ansible-discovery-report.py --input export.json
```

| Argument   | Default                        | Description                       |
|------------|--------------------------------|-----------------------------------|
| `--config` | `ansible-discovery-report.ini` | INI configuration                 |
| `--input`  | `playbooks/facts_cache`        | facts_cache directory or JSON file|
| `--output` | `ansible-discovery-report.html`| Output HTML file                  |

All text, colors, and labels are configured in the INI file.
The report includes OS overview, application inventory,
Java/PHP details, and RHEL upgrade eligibility analysis.

## Architecture

```text
discovery.yaml
├── prereqs.yaml            → selective collection variables
├── process_facts module    → system processes (/proc)
├── system collectors       → packages, services, ports, firewall, ...
└── app collectors          → java/, apache, nginx, php
    └── custom modules      → config parsing
        └── JSON cache      → facts_cache/<hostname>
```

### Custom Modules (`playbooks/library/`)

| Module                 | Purpose                      | Dependencies  |
|------------------------|------------------------------|---------------|
| `process_facts`        | Process discovery via /proc  | None          |
| `apache_config_parser` | Apache configuration parsing | None          |
| `nginx_config_parser`  | NGINX configuration parsing  | None          |
| `php_config_parser`    | PHP multi-distro discovery   | None          |

All modules are standalone with no external Python dependencies.

### Custom Filters (`playbooks/filter_plugins/file_utils.py`)

| Filter          | Returns | Description                    |
|-----------------|---------|--------------------------------|
| `file_exists`   | bool    | Regular file exists            |
| `path_exists`   | bool    | File or directory exists       |
| `file_readable` | bool    | File exists and is readable    |

### Project Structure

```text
ansible-discovery/
├── playbooks/
│   ├── discovery.yaml           # Main playbook
│   ├── prereqs.yaml             # Selective collection config
│   ├── ansible.cfg              # Ansible config (jsonfile cache)
│   ├── collectors/              # Discovery collectors
│   │   ├── java/                # Tomcat, JBoss, JAR
│   │   ├── apache.yaml
│   │   ├── nginx.yaml
│   │   ├── php.yaml
│   │   └── ...                  # packages, services, ports, etc.
│   ├── library/                 # Custom modules
│   ├── filter_plugins/          # Custom filters
│   └── galaxy-requirements.yaml
├── ansible-discovery-report.py  # HTML report generator
├── ansible-discovery-report.ini # Report configuration
└── README.md
```

## Troubleshooting

```bash
# Test connectivity
ansible all -m ping

# Syntax check
ansible-playbook --syntax-check discovery.yaml

# Verbose execution
ansible-playbook discovery.yaml -vvv

# Test custom modules
ansible localhost -m process_facts
ansible localhost -m php_config_parser
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
