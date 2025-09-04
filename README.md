# Ansible Discovery

**Automated infrastructure discovery system for Linux servers using Ansible**

A comprehensive solution that collects detailed information about processes, Java applications, web servers, PHP applications, and system services, storing data in MongoDB with intelligent caching for analysis and reporting.

## ✨ Features

### 🔍 **Multi-Stage Discovery Pipeline**

- **Selective Collection**: Use `collector_only` parameter for targeted discovery
- **Process Analysis**: Smart detection via custom `process_facts` module
- **Java Applications**: Deep inspection of Tomcat, JBoss/Wildfly, and standalone JARs
- **Web Servers**: Apache HTTPD with full configuration parsing, Nginx (in development)
- **PHP Applications**: Auto-discovery and configuration parsing across distributions
- **System Information**: Packages, services, network ports, firewall, and bootloader

### 🚀 **Advanced Capabilities**

- **Custom Modules**: Four specialized modules for process and configuration discovery
- **Container Detection**: Automatic adjustment for containerized environments
- **Custom Filters**: File existence checks and path validation
- **MongoDB Caching**: Persistent storage with configurable TTL
- **Cross-Platform**: RHEL, Debian, SUSE support with unified output

### 🛠 **Modular Architecture**

- **Selective Execution**: Target specific collectors with absolute precedence
- **Custom Modules**: Standalone parsers with minimal dependencies
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

## 🎯 Usage

### Basic Discovery

```bash
# Full discovery (all collectors)
ansible-playbook discovery.yaml

# Selective discovery (single collector)
ansible-playbook discovery.yaml -e collector_only=java

# Individual collector control
ansible-playbook discovery.yaml -e collector_packages=false -e collector_services=false
```

### Collector Selection

The discovery system uses a **selective collection approach** with absolute precedence:

| Command                    | Description                | Collectors Executed |
|----------------------------|----------------------------|---------------------|
| `collector_only=java`      | Java applications only     | java                |
| `collector_only=apache`    | Apache web server only     | apache              |
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
| `nginx`      | NGINX configuration              | NGINX hosts  | Server blocks, config (dev)      |
| `php`        | PHP configuration discovery      | PHP hosts    | Settings, extensions, versions   |
| `firewall`   | Firewall rules and status        | All hosts    | Rules, zones, policies           |
| `selinux`    | SELinux status and policies      | All hosts    | Mode, policies, contexts         |
| `blockdev`   | Block device information         | All hosts    | Disks, mounts, filesystems       |
| `bootloader` | Boot configuration               | All hosts    | GRUB, kernel parameters          |

## 🔧 Architecture

### Data Flow

```text
discovery.yaml → prereqs.yaml (selective config) → process_facts (custom module) →
                 → collectors/*.yaml (conditional execution) →
                 → custom modules (config parsing) →
                 → MongoDB cache (TTL-based)
```

### Custom Modules

Located in `playbooks/library/`:

| Module                  | Purpose                        | Dependencies    | Status          |
|-------------------------|--------------------------------|-----------------|-----------------|
| `process_facts`         | System process discovery       | None            | ✅ Production   |
| `apache_config_parser`  | Apache configuration parsing   | `apacheconfig`  | ✅ Production   |
| `php_config_parser`     | PHP configuration discovery    | None            | ✅ Production   |
| `nginx_config_parser`   | NGINX configuration parsing    | None            | 🚧 Development |

### Custom Filters

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

### MongoDB Caching

All discovered facts are cached in MongoDB with configurable TTL:

- **Performance**: Avoid re-discovery on subsequent runs
- **Persistence**: Data survives across playbook executions
- **Flexibility**: TTL=0 for infinite cache (current default)

### Cross-Platform Support

Hybrid collection strategy ensures compatibility:

- **Primary**: Uses official `fedora.linux_system_roles` when available
- **Fallback**: Custom modules and shell commands for older systems
- **Container**: Automatic detection and adjusted behavior
- **Distributions**: RHEL, Debian, SUSE support with unified output

## 🛠 Development Environment

### Setup for Contributors

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/ansible-discovery.git
   cd ansible-discovery
   ```

2. **Install development dependencies**

   ```bash
   # Setup Python environment
   source activate
   pip install -r pip-venv-requirements.txt
   ```

3. **Setup Ansible environment**

   ```bash
   cd playbooks
   
   # Install required collections
   ansible-galaxy collection install -r galaxy-requirements.yaml
   
   # Setup configuration files
   cp ansible.cfg.example ansible.cfg
   cp inventory.example inventory
   ```

4. **Configure development tools**

   ```bash
   # Install markdown linting (optional)
   npm install -g markdownlint-cli
   
   # Install Python linting tools (optional)
   pip install flake8 pylint black
   ```

5. **VS Code setup (recommended)**

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

#### Custom Module Testing

```bash
# Test individual modules
ansible localhost -m process_facts
ansible localhost -m php_config_parser
ansible localhost -m apache_config_parser -a "path=/etc/httpd/conf/httpd.conf configroot=/etc/httpd"
ansible localhost -m nginx_config_parser -a "path=/etc/nginx/nginx.conf"

# Run module tests (if available)
./library/tests/run_tests.sh
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
│   ├── discovery.yaml                 # Main discovery orchestrator
│   ├── prereqs.yaml                   # Collection variables configuration
│   ├── collectors/                    # Discovery modules
│   │   ├── packages.yaml              # Package discovery
│   │   ├── services.yaml              # Service discovery
│   │   ├── ports.yaml                 # Network ports discovery
│   │   ├── java/                      # Java application discovery
│   │   │   ├── java.yaml              # Java process classification
│   │   │   ├── tomcat.yaml            # Tomcat-specific discovery
│   │   │   ├── jboss.yaml             # JBoss/Wildfly discovery
│   │   │   └── jar.yaml               # Generic JAR analysis
│   │   ├── apache.yaml                # Apache HTTPD discovery
│   │   ├── nginx.yaml                 # NGINX discovery (in development)
│   │   ├── php.yaml                   # PHP configuration discovery
│   │   ├── firewall.yaml              # Firewall discovery
│   │   ├── selinux.yaml               # SELinux discovery
│   │   ├── blockdev.yaml              # Block device discovery
│   │   └── bootloader.yaml            # Bootloader discovery
│   ├── library/                       # Custom Ansible modules
│   │   ├── process_facts.py           # Process discovery module
│   │   ├── apache_config_parser.py    # Apache config parser
│   │   ├── php_config_parser.py       # PHP config parser
│   │   ├── nginx_config_parser.py     # NGINX config parser (dev)
│   │   ├── docs/                      # Module documentation
│   │   └── tests/                     # Module tests
│   ├── filter_plugins/                # Custom Ansible filters
│   │   ├── file_utils.py              # File operation filters
│   │   ├── README.md                  # Filter documentation
│   │   └── tests/                     # Filter tests
│   ├── ansible.cfg.example            # Ansible configuration template
│   ├── inventory.example              # Inventory template
│   └── galaxy-requirements.yaml       # Required Ansible collections
├── scripts/                           # Utility scripts
│   ├── manage-cache.sh                # MongoDB cache management
│   ├── clear-cache-simple.sh          # Simple cache clearing
│   └── README.md                      # Scripts documentation
├── tests/                             # Integration tests
├── ARCHITECTURE.md                    # Technical architecture documentation
├── DEPLOYMENT.md                      # Deployment guide
├── DOCS.md                            # Additional documentation
├── TODO.yaml                          # Future development roadmap
└── README.md                          # This file
```

## 📋 Contributing

### Development Guidelines

1. **Code Quality**
   - Follow PEP 8 for Python code
   - Use meaningful variable names
   - Include docstrings for all functions
   - Maintain Ansible best practices

2. **Testing**
   - Test all changes locally before submitting
   - Include unit tests for new modules
   - Update integration tests as needed
   - Verify markdown formatting

3. **Documentation**
   - Update relevant documentation
   - Include examples in module documentation
   - Update this README for significant changes
   - Follow markdown standards

4. **Pull Requests**
   - Create feature branches from `main`
   - Include clear commit messages
   - Reference relevant issues
   - Include testing evidence

### Custom Module Development

When creating new custom modules:

1. **Create module**: Place in `playbooks/library/`
2. **Documentation**: Create `.md` file in `library/docs/`
3. **Tests**: Add tests in `library/tests/`
4. **Integration**: Update collectors as needed
5. **Dependencies**: Document any external requirements

### Filter Development

When creating new custom filters:

1. **Add filter**: Implement in `filter_plugins/file_utils.py`
2. **Tests**: Add tests in `filter_plugins/tests/`
3. **Documentation**: Update `filter_plugins/README.md`
4. **Examples**: Include usage examples

## 🔮 Roadmap

See [TODO.yaml](TODO.yaml) for detailed development roadmap.

### Planned Features

- **Container Support**: Docker process discovery and mapping
- **Additional Languages**: .NET, Python, Ruby application discovery
- **Enhanced Web Servers**: Complete NGINX integration
- **Security Scanning**: Vulnerability and compliance checking
- **Reporting**: Web dashboard for discovered infrastructure

### Development Status

| Component            | Status              | Notes                               |
|----------------------|---------------------|-------------------------------------|
| Java Discovery       | ✅ Complete         | Tomcat, JBoss, JAR support          |
| Apache Discovery     | ✅ Complete         | Full configuration parsing          |
| PHP Discovery        | ✅ Complete         | Multi-distribution support          |
| NGINX Discovery      | 🚧 In Development   | Module available, collector pending |
| Container Discovery  | 📋 Planned          | Docker integration roadmap          |
| .NET Discovery       | 📋 Planned          | Core/Framework detection            |

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/andrewlinuxadmin/ansible-discovery/issues)
- **Documentation**: [Project Wiki](https://github.com/andrewlinuxadmin/ansible-discovery/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/andrewlinuxadmin/ansible-discovery/discussions)

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ansible Community** for the excellent automation framework
- **MongoDB** for reliable caching infrastructure  
- **nginx-crossplane** project for NGINX configuration parsing inspiration
- **Contributors** who help improve this project

---

**Made with ❤️ by the Ansible community**
- Process analysis powered by custom modules and shell scripting
