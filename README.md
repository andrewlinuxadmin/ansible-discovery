# Ansible Discovery

**Automated infrastructure discovery system for Linux servers using Ansible**

A comprehensive solution that collects detailed information about processes, Java applications, web servers, and system services, storing data in MongoDB with intelligent caching for analysis and reporting.

## ✨ Features

### 🔍 **Multi-Stage Discovery Pipeline**

- **Selective Collection**: Use `collector_only` parameter for targeted discovery
- **Process Analysis**: Smart detection with JSON-structured output
- **Java Applications**: Deep inspection of Tomcat, JBoss/Wildfly, and standalone JARs
- **Web Servers**: Apache HTTPD and Nginx with configuration extraction
- **System Information**: Packages, services, network ports, firewall, and bootloader

### 🚀 **Advanced Capabilities**

- **Hybrid Collection**: Official roles with manual fallbacks
- **Container Detection**: Automatic adjustment for containerized environments
- **Custom Filters**: File existence checks and path validation
- **MongoDB Caching**: Persistent storage with configurable TTL
- **Cross-Platform**: RHEL, Debian, SUSE support with unified output

### 🛠 **Modular Architecture**

- **Selective Execution**: Target specific collectors with absolute precedence
- **Conditional Processing**: Process-based discovery for Java/web applications
- **Graceful Degradation**: Fallback mechanisms for missing tools/permissions

## 🚀 Quick Start

### Prerequisites

- **System**: Linux with Python 3.9+
- **Database**: MongoDB instance (local or remote)
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
   
   # Setup configuration
   cp ansible.cfg.example ansible.cfg
   cp inventory.example inventory
   ```

3. **Start MongoDB and configure inventory**

   ```bash
   # Docker (recommended)
   docker run -d -p 27017:27017 --name ansible-discovery-mongo mongo:latest
   
   # Edit inventory with your target servers
   nano inventory
   ```

## Usage

```bash
# Single collector (absolute precedence)
ansible-playbook discovery.yaml -e collector_only=java

# All collectors (default behavior)
ansible-playbook discovery.yaml

# Individual collector control (when collector_only not used)
ansible-playbook discovery.yaml -e collector_packages=false
```

### Collector Selection

The discovery system uses a selective collection approach with absolute precedence:

```bash
# Single collector (absolute precedence)
ansible-playbook discovery.yaml -e collector_only=java

# All collectors (default behavior)  
ansible-playbook discovery.yaml

# Individual collector control (when collector_only not used)
ansible-playbook discovery.yaml -e collector_packages=false
```

### System Collectors

| Collector | Description | Scope | Output |
|-----------|-------------|-------|--------|
| `packages` | Installed packages | All hosts | Package inventory with versions |
| `services` | System services | All hosts | Service status and configuration |
| `ports` | Network ports | All hosts | Listening ports and processes |
| `bootloader` | Boot configuration | All hosts | GRUB/bootloader settings |
| `firewall` | Firewall rules | All hosts | iptables/firewalld configuration |
| `selinux` | SELinux status | All hosts | SELinux mode and policies |
| `blockdev` | Block devices | All hosts | Disk and filesystem information |
| `java` | Java applications | Java hosts | Tomcat, JBoss, JAR discovery |
| `apache` | Apache servers | Apache hosts | Virtual hosts and configuration |
| `nginx` | Nginx servers | Nginx hosts | Server blocks and upstreams |

### Basic Examples

```bash
# Full discovery (all collectors)
ansible-playbook discovery.yaml

# System-only discovery
ansible-playbook discovery.yaml -e collector_only=packages

# Java applications only
ansible-playbook discovery.yaml -e collector_only=java

# Network and security focus
ansible-playbook discovery.yaml -e collector_only=firewall

# Debug mode with verbose logging
ansible-playbook discovery.yaml -e debug=true -e log=true
```

### Advanced Usage

```bash
# Run on specific host group
ansible-playbook discovery.yaml --limit java_servers -e collector_only=java

# Dry run to see what would be discovered
ansible-playbook discovery.yaml --check --diff

# Multiple collectors (without collector_only)
ansible-playbook discovery.yaml -e collector_java=true -e collector_apache=true
```

## Architecture

### Collection Strategy

The system follows a hybrid approach:

1. **Official Roles First**: Attempts to use `fedora.linux_system_roles` modules
2. **Manual Fallback**: Uses shell commands with JSON parsing when official roles fail
3. **Container Detection**: Automatically adjusts for containerized environments
4. **Graceful Degradation**: Provides meaningful fallback data when tools are unavailable

### Discovery Pipeline

```text
discovery.yaml → prereqs.yaml (variables) → process_facts → 
collectors/* (conditional) → java/apache/nginx (process-based)
```

### Data Structure

All collectors produce structured JSON output with consistent fields:

```json
{
  "source": "fedora.linux_system_roles|manual|container",
  "status": "active|inactive|unknown", 
  "note": "additional_context_when_applicable"
}
```

## Key Features

### Custom Ansible Filters

Enhanced file operations with custom filters:

- **`file_exists`**: Check if a specific file exists (returns boolean)
- **`path_exists`**: Check if a path exists (file or directory)  
- **`file_readable`**: Check if a file exists and is readable by current user

```yaml
# Example usage in discovery
- name: Check if Tomcat config exists
  debug:
    msg: "Tomcat found at {{ tomcat_home }}"
  when: "{{ tomcat_home }}/conf/server.xml" | file_exists

- name: Process only readable config files
  include_tasks: process_config.yaml
  when: item | file_readable
  loop: "{{ config_files }}"
```

**Configuration**: Add `filter_plugins = ./filter_plugins` to your `ansible.cfg`.

### Smart Process Classification

Advanced process analysis with structured JSON output:

- **Process Detection**: Identifies Java applications, web servers by command line patterns
- **PID-based Mapping**: Efficient process-to-application correlation
- **Container Awareness**: Automatic detection and handling of containerized processes

### MongoDB Caching with TTL

All discovered facts are cached in MongoDB with configurable TTL:

- **Performance**: Avoid re-discovery on subsequent runs
- **Persistence**: Data survives across playbook executions
- **Flexibility**: TTL=0 for infinite cache (current default)

### Cross-Platform Support

Hybrid collection strategy ensures compatibility:

- **Primary**: Uses official `fedora.linux_system_roles` when available
- **Fallback**: Shell commands with JSON parsing for older systems
- **Container**: Automatic detection and adjusted behavior
- **Distributions**: RHEL, Debian, SUSE support with unified output

## 🛠 Development Environment

### Setup for Contributors

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/ansible-discovery.git
   cd ansible-discovery
   ```

1. **Install development dependencies**

   ```bash
   # Setup Python environment
   source activate
   pip install -r pip-venv-requirements.txt
   ```

1. **Setup Ansible environment**

   ```bash
   cd playbooks
   
   # Install required collections
   ansible-galaxy collection install -r galaxy-requirements.yaml
   
   # Setup configuration files
   cp ansible.cfg.example ansible.cfg
   cp inventory.example inventory
   ```

1. **Configure development tools**

   ```bash
   # Install markdown linting (optional)
   npm install -g markdownlint-cli
   
   # Install Python linting tools (optional)
   pip install flake8 pylint black
   ```

1. **VS Code setup (recommended)**

   Install required extensions:

   - [Red Hat Ansible](https://marketplace.visualstudio.com/items?itemName=redhat.ansible)
   - [Jinja HTML](https://marketplace.visualstudio.com/items?itemName=samuelcolvin.jinjahtml)

   ```bash
   # Open project in VS Code
   code .
   ```

### Running Tests

#### Basic Testing

```bash
# Validate playbook syntax
ansible-playbook --syntax-check discovery.yaml

# Test selective collection
ansible-playbook discovery.yaml -e collector_only=java --check

# Run with debug output
ansible-playbook discovery.yaml -e debug=true -e log=true
```

#### Custom Filter Testing

```bash
# Test individual filters
ansible localhost -m debug -a "msg={{ '/etc/passwd' | file_exists }}"
ansible localhost -m debug -a "msg={{ '/tmp' | path_exists }}"
ansible localhost -m debug -a "msg={{ '/etc/shadow' | file_readable }}"

# Run comprehensive filter tests
ansible-playbook filter_plugins/tests/test_file_utils.yaml
./filter_plugins/tests/run_tests.sh
```

#### Cache Management

```bash
# List cached hosts
./scripts/manage-cache.sh --list

# Clear all cache
./scripts/clear-cache-simple.sh

# Clear cache for specific hosts
./scripts/manage-cache.sh server1.example.com server2.example.com

# Force clear all cache (automation)
./scripts/clear-cache-simple.sh --force
```

#### Performance Testing

```bash
# Time discovery execution
time ansible-playbook discovery.yaml

# Test MongoDB caching
ansible-playbook discovery.yaml -e collector_only=packages  # First run
time ansible-playbook discovery.yaml -e collector_only=packages  # Cached run
```

### Project Structure

```text
ansible-discovery/
├── playbooks/
│   ├── discovery.yaml          # Main discovery orchestrator
│   ├── prereqs.yaml           # Collection variables configuration
│   ├── collectors/            # Discovery modules
│   │   ├── packages.yaml      # Package discovery
│   │   ├── services.yaml      # Service discovery
│   │   ├── ports.yaml         # Network ports discovery
│   │   ├── firewall.yaml      # Firewall rules discovery
│   │   ├── bootloader.yaml    # Bootloader discovery
│   │   ├── selinux.yaml       # SELinux discovery
│   │   ├── blockdev.yaml      # Block device discovery
│   │   ├── apache.yaml        # Apache discovery
│   │   ├── nginx.yaml         # Nginx discovery
│   │   └── java/              # Java application discovery
│   │       ├── java.yaml      # Java orchestrator
│   │       ├── tomcat.yaml    # Tomcat discovery
│   │       ├── jboss.yaml     # JBoss/Wildfly discovery
│   │       └── jar.yaml       # JAR discovery
│   ├── filter_plugins/        # Custom Ansible filters
│   │   ├── file_utils.py      # File operation filters
│   │   ├── README.md          # Filter documentation
│   │   └── tests/             # Filter tests
│   ├── ansible.cfg            # Ansible configuration
│   ├── galaxy-requirements.yaml # Required collections
│   ├── inventory.example      # Example inventory
│   └── collections/           # Downloaded collections
├── scripts/                  # Cache management utilities
│   ├── clear-cache-simple.sh  # Simple cache cleanup
│   ├── clear-cache.sh         # Advanced cache cleanup  
│   ├── manage-cache.sh        # Selective cache management
│   └── README.md              # Script documentation
├── mongodbdata/              # MongoDB data (ignored)
│   ├── filter_plugins/        # Custom Ansible filters
│   │   ├── file_utils.py      # File operation filters
│   │   ├── README.md          # Filter documentation
│   │   └── tests/             # Filter tests
│   ├── ansible.cfg            # Ansible configuration
│   ├── galaxy-requirements.yaml # Required collections
│   ├── inventory.example      # Example inventory
│   └── collections/           # Downloaded collections
├── mongodbdata/              # MongoDB data (ignored)
├── activate                  # Python environment activation
├── pip-venv-requirements.txt # Python dependencies
└── README.md                 # This documentation
```

## Configuration

### MongoDB Cache Settings

Edit `playbooks/ansible.cfg`:

```ini
[defaults]
fact_caching = community.mongodb.mongodb
fact_caching_timeout = 0
fact_caching_connection = mongodb://localhost:27017/ansible
```

#### TTL Configuration Options

- **`fact_caching_timeout = 0`**: Infinite TTL (facts never expire) - current default
- **`fact_caching_timeout = 3600`**: 1 hour TTL
- **`fact_caching_timeout = 86400`**: 1 day TTL
- **`fact_caching_timeout = 604800`**: 1 week TTL

### Discovery Options

Available collector parameters for selective execution:

```bash
# Single collector (absolute precedence)
ansible-playbook discovery.yaml -e collector_only=packages

# Multiple collectors (when collector_only not used)
ansible-playbook discovery.yaml -e collector_java=true -e collector_apache=true

# Debug and logging
ansible-playbook discovery.yaml -e debug=true -e log=true
```

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the existing code style
4. Test your changes thoroughly
5. Submit a pull request with detailed description

### Code Guidelines

- Use descriptive task names in playbooks
- Include `cacheable: true` for important facts
- Use `no_log: "{{ not log }}"` for verbose output
- Follow hybrid collection pattern (official + fallback)
- Add container detection where applicable
- Document new collectors with examples

### Testing

Before submitting:

```bash
# Validate syntax
ansible-playbook --syntax-check discovery.yaml

# Test custom filters
ansible-playbook filter_plugins/tests/test_file_utils.yaml

# Test selective collection
ansible-playbook discovery.yaml -e collector_only=packages --check
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/andrewlinuxadmin/ansible-discovery/issues)
- **Documentation**: This README and inline code comments

## 🙏 Acknowledgments

- Built with [Ansible](https://www.ansible.com/)
- MongoDB integration via [community.mongodb](https://galaxy.ansible.com/community/mongodb)
- Hybrid collection using [fedora.linux_system_roles](https://galaxy.ansible.com/fedora/linux_system_roles)
- Process analysis powered by custom modules and shell scripting
