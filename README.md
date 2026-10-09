# Ansible Discovery

**Automated infrastructure discovery system for Linux servers using Ansible**

A comprehensive solution that collects detailed information about processes,
Java applications, web servers, PHP applications, and system services,
storing discovered facts as local JSON files for analysis and reporting.

## ✨ Features

### Multi-Stage Discovery Pipeline

- **Selective Collection**: Use `collector_only` parameter for targeted discovery
- **Process Analysis**: Smart detection via custom `process_facts` module
- **Java Applications**: Deep inspection of Tomcat, JBoss/Wildfly, and standalone JARs
- **Web Servers**: Apache HTTPD and NGINX with full configuration parsing
- **PHP Applications**: Auto-discovery and configuration parsing with dynamic version detection
- **System Information**: Packages, services, network ports, firewall, and bootloader

### Advanced Capabilities

- **Custom Modules**: Four specialized modules for process and configuration discovery
- **Container Detection**: Automatic adjustment for containerized environments
- **Custom Filters**: File existence checks and path validation
- **JSON File Caching**: Persistent local storage with configurable TTL
- **HTML Report Generator**: Configurable report with upgrade eligibility analysis
- **Cross-Platform**: RHEL, Debian, SUSE support with unified output

### Modular Architecture

- **Selective Execution**: Target specific collectors with absolute precedence
- **Custom Modules**: Standalone parsers with minimal dependencies
- **Conditional Processing**: Process-based discovery for Java/web applications
- **Graceful Degradation**: Fallback mechanisms for missing tools/permissions

## Quick Start

### Prerequisites

- **System**: Linux with Python 3.9+
- **Network**: SSH connectivity to target servers
- **Permissions**: Sudo access on target machines

### Installation

1. **Clone and setup environment**

   ```bash
   git clone https://github.com/andrewlinuxadmin/ansible-discovery.git
   cd ansible-discovery

   # Setup Python environment
   source activate
   pip install -r pip-venv-requirements.txt
   ```

2. **Configure Ansible environment**

   ```bash
   cd playbooks

   # Install collections
   ansible-galaxy collection install -r galaxy-requirements.yaml

   # Setup inventory
   cp inventory.example inventory
   # Edit inventory with your target servers
   nano inventory
   ```

3. **Run discovery** (no extra services needed)

   ```bash
   ansible-playbook discovery.yaml
   ```

   Facts are cached as JSON files in `playbooks/facts_cache/`.
   The directory is created automatically on the first run.

## Usage

### Basic Discovery

```bash
# Full discovery (all collectors)
ansible-playbook discovery.yaml

# Selective discovery (single collector)
ansible-playbook discovery.yaml -e collector_only=java

# Individual collector control
ansible-playbook discovery.yaml -e collector_packages=false -e collector_services=false

# Debug mode
ansible-playbook discovery.yaml -e debug=true -e log=true
```

### Collector Selection

| Command                    | Description                | Collectors Executed |
|----------------------------|----------------------------|---------------------|
| `collector_only=java`      | Java applications only     | java                |
| `collector_only=apache`    | Apache web server only     | apache              |
| `collector_only=nginx`     | NGINX web server only      | nginx               |
| `collector_only=php`       | PHP configuration only     | php                 |
| `collector_only=packages`  | Package information only   | packages            |
| No `collector_only`        | All enabled collectors     | all (default)       |

### Available Collectors

| Tag          | Description                      | Scope        | Output                           |
|--------------|----------------------------------|--------------|----------------------------------|
| `packages`   | System package discovery         | All hosts    | Package list with versions       |
| `services`   | Service status and configuration | All hosts    | Service states and configs       |
| `ports`      | Network ports and listening svc  | All hosts    | Port mappings and processes      |
| `java`       | Java application discovery       | Java hosts   | Tomcat, JBoss, JAR details       |
| `apache`     | Apache HTTPD configuration       | Apache hosts | VirtualHosts, modules, config    |
| `nginx`      | NGINX configuration              | NGINX hosts  | Server blocks, PHP-FPM detection |
| `php`        | PHP configuration discovery      | PHP hosts    | Settings, extensions, versions   |
| `firewall`   | Firewall rules and status        | All hosts    | Rules, zones, policies           |
| `selinux`    | SELinux status and policies      | All hosts    | Mode, policies, contexts         |
| `blockdev`   | Block device information         | All hosts    | Disks, mounts, filesystems       |
| `bootloader` | Boot configuration               | All hosts    | GRUB, kernel parameters          |

### Fact Cache Management

```bash
# View cached hosts
ls playbooks/facts_cache/

# View facts for a specific host
cat playbooks/facts_cache/server1.example.com | python3 -m json.tool

# Clear cache for a specific host
rm playbooks/facts_cache/server1.example.com

# Clear all cache
rm -rf playbooks/facts_cache/*
```

### HTML Report Generation

After collecting facts, generate a comprehensive HTML report:

```bash
# Generate report (reads from export.json, outputs ansible-discovery-report.html)
python3 ansible-discovery-report.py

# Use custom config and files
python3 ansible-discovery-report.py --config my-config.ini --input data.json --output report.html
```

The report includes OS distribution overview, application inventory,
Java/PHP server details, and RHEL upgrade eligibility analysis.
Configuration is fully externalized in `ansible-discovery-report.ini`.

## Architecture

### Data Flow

```text
discovery.yaml → prereqs.yaml (selective config) → process_facts (custom module) →
                 → collectors/*.yaml (conditional execution) →
                 → custom modules (config parsing) →
                 → JSON file cache (playbooks/facts_cache/)
```

### Custom Modules

Located in `playbooks/library/`:

| Module                  | Purpose                        | Dependencies    | Status          |
|-------------------------|--------------------------------|-----------------|-----------------|
| `process_facts`         | System process discovery       | None            | Production      |
| `apache_config_parser`  | Apache configuration parsing   | `apacheconfig`  | Production      |
| `php_config_parser`     | PHP configuration discovery    | None            | Production      |
| `nginx_config_parser`   | NGINX configuration parsing    | None            | Production      |

### Custom Filters

Located in `playbooks/filter_plugins/file_utils.py`:

- **`file_exists`**: Check if a specific file exists (returns boolean)
- **`path_exists`**: Check if a path exists (file or directory)
- **`file_readable`**: Check if a file exists and is readable by current user

### Cross-Platform Support

- **Primary**: Uses official `fedora.linux_system_roles` when available
- **Fallback**: Custom modules and shell commands for older systems
- **Container**: Automatic detection and adjusted behavior
- **Distributions**: RHEL, Debian, SUSE support with unified output

### Project Structure

```text
ansible-discovery/
├── playbooks/
│   ├── discovery.yaml              # Main discovery orchestrator
│   ├── prereqs.yaml                # Collection variables configuration
│   ├── ansible.cfg                 # Ansible config (jsonfile caching)
│   ├── collectors/                 # Discovery collectors
│   │   ├── packages.yaml           # Package discovery
│   │   ├── services.yaml           # Service discovery
│   │   ├── ports.yaml              # Network ports discovery
│   │   ├── java/                   # Java application discovery
│   │   ├── apache.yaml             # Apache HTTPD discovery
│   │   ├── nginx.yaml              # NGINX discovery
│   │   ├── php.yaml                # PHP configuration discovery
│   │   ├── firewall.yaml           # Firewall discovery
│   │   ├── selinux.yaml            # SELinux discovery
│   │   ├── blockdev.yaml           # Block device discovery
│   │   └── bootloader.yaml         # Bootloader discovery
│   ├── library/                    # Custom Ansible modules
│   ├── filter_plugins/             # Custom Ansible filters
│   ├── inventory.example           # Inventory template
│   └── galaxy-requirements.yaml    # Required Ansible collections
├── ansible-discovery-report.py     # HTML report generator
├── ansible-discovery-report.ini    # Report configuration (i18n)
├── ARCHITECTURE.md                 # Technical architecture
├── DEPLOYMENT.md                   # Deployment guide
├── DOCS.md                         # Documentation index
├── TODO.md                         # Development roadmap
└── README.md                       # This file
```

## Contributing

1. Follow PEP 8 for Python code; use meaningful variable names and docstrings
2. Test all changes locally before submitting
3. Update relevant documentation and include examples
4. Create feature branches from `main` with clear commit messages

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
