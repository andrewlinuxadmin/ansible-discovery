# Ansible Discovery

**Automated infrastructure discovery system for Linux servers using Ansible**

A comprehensive solution that collects detailed information about running
processes, Java applications, web servers, and system services,
storing data in MongoDB with intelligent caching for analysis and reporting.

## ✨ Features

### 🔍 **Comprehensive Discovery**

- **Process Analysis**: Smart detection excluding kernel threads with JSON-structured output
- **Java Applications**: Deep inspection of Tomcat, JBoss/Wildfly, and standalone JARs
- **Web Servers**: Apache HTTPD and Nginx with virtual host extraction  
- **System Information**: Packages, services, network ports, and security settings

### 🚀 **Advanced Capabilities**

- **Custom Filters**: File existence checks and path validation
- **MongoDB Caching**: Persistent storage with configurable TTL
- **Modular Design**: Tag-based execution for selective discovery

### 🛠 **Developer Experience**

- **VS Code Integration**: Workspace configuration and settings
- **Quality Assurance**: Markdown linting and Python standards
- **Smart Session Management**: Automatic tab closure for deleted files

## 🚀 Quick Start

### Prerequisites

- **System Requirements**: Linux with Python 3.9+
- **Database**: MongoDB instance (local or remote)
- **Network Access**: SSH connectivity to target servers
- **Permissions**: Sudo access on target machines

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/andrewlinuxadmin/ansible-discovery.git
   cd ansible-discovery
   ```

2. **Setup Python environment**

   ```bash
   # Install UV package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create Python environment
   uv python install 3.9
   uv venv --python 3.9
   source .venv/bin/activate
   
   # Install dependencies
   pip install -r pip-venv-requirements.txt
   ```

3. **Configure Ansible environment**

   ```bash
   cd playbooks
   
   # Install required collections
   ansible-galaxy collection install -r galaxy-requirements.yaml
   
   # Setup configuration
   cp ansible.cfg.example ansible.cfg
   cp inventory.example inventory
   ```

4. **Start MongoDB (if running locally)**

   ```bash
   # Using Docker (recommended)
   docker run -d -p 27017:27017 --name ansible-discovery-mongo mongo:latest
   
   # Or start local MongoDB service
   sudo systemctl start mongod
   ```

5. **Configure target servers**

   ```bash
   # Edit inventory with your target servers
   nano inventory
   ```

## Usage

### Available Discovery Tags

The discovery playbook supports granular execution through tags,
allowing you to run specific discovery modules:

| Tag | Description | Scope | Output |
|-----|-------------|-------|--------|
| `packages` | Installed packages | All hosts | Package inventory with versions |
| `services` | System services | All hosts | Service status and configuration |
| `ports` | Network ports | All hosts | Listening ports and processes |
| `bootloader` | Boot configuration | All hosts | GRUB/bootloader settings |
| `firewall` | Firewall rules | All hosts | iptables/firewalld configuration |
| `selinux` | SELinux status | All hosts | SELinux mode and policies |
| `blockdev` | Block devices | All hosts | Disk and filesystem information |
| `java` | Java applications | Java hosts | Tomcat, JBoss, JAR discovery |
| `tomcat` | Tomcat servers | Tomcat hosts | Tomcat instances and configurations |
| `jboss` | JBoss/Wildfly | JBoss hosts | JBoss deployments and settings |
| `jar` | Standalone JARs | Java hosts | JAR files and manifest info |

> **Note**: Web server discovery (`webservers` tag) is currently disabled.
> To enable it, uncomment the relevant section in `discovery.yaml`.

### Basic Usage Examples

```bash
# Full infrastructure discovery (all tags)
ansible-playbook -i inventory discovery.yaml

# System-only discovery (core facts + specific modules)
ansible-playbook -i inventory discovery.yaml --tags "packages,services,ports"

# Java applications only
ansible-playbook -i inventory discovery.yaml --tags java

# Specific Java application types
ansible-playbook -i inventory discovery.yaml --tags "tomcat,jboss"

# Network and security focus
ansible-playbook -i inventory discovery.yaml --tags "ports,firewall,selinux"

# Storage and system configuration
ansible-playbook -i inventory discovery.yaml --tags "blockdev,bootloader,packages"
```

#### Advanced Usage

```bash
# Skip specific modules (discover everything except Java)
ansible-playbook -i inventory discovery.yaml --skip-tags java

# Debug mode with verbose logging
ansible-playbook -i inventory discovery.yaml --tags java -e debug=true -e log=true

# Dry run to see what would be discovered
ansible-playbook -i inventory discovery.yaml --check --diff

# Run on specific host group
ansible-playbook -i inventory discovery.yaml --limit java_servers --tags java
```

## Recent Features

### Custom Ansible Filters

The project includes custom filters for enhanced file operations:

- **`file_exists`**: Check if a specific file exists (returns boolean)
- **`path_exists`**: Check if a path exists (file or directory)
- **`file_readable`**: Check if a file exists and is readable by current user

```yaml
# Example usage in playbooks
- name: Check if Tomcat JAR exists
  debug:
    msg: "Tomcat found at {{ tomcat_path }}"
  when: tomcat_path | file_exists

- name: Verify configuration directory
  debug:
    msg: "Config dir exists"
  when: "/etc/httpd/conf.d" | path_exists

- name: Process only accessible config files
  include_tasks: process_config.yaml
  when: item | file_readable
  loop: "{{ config_files }}"
```

**Configuration**: Add `filter_plugins = ./filter_plugins` to your `ansible.cfg`.

### Smart Process Classification

Advanced process analysis with structured JSON output:

- **AWK-based parsing**: Converts `ps` output to structured data
- **Application detection**: Identifies Tomcat, JBoss, web servers
- **PID-based mapping**: Efficient process-to-application correlation

### MongoDB Caching with TTL

All discovered facts are cached in MongoDB with configurable TTL:

- **Performance**: Avoid re-discovery on subsequent runs
- **Persistence**: Data survives across playbook executions  
- **Flexibility**: TTL=0 for infinite cache (current default)

### VS Code Integration

Project includes VS Code workspace configuration:

- **Auto-close tabs**: Deleted files close automatically
- **Python interpreter**: Pre-configured for Ansible development
- **Session management**: Prevents file restoration issues

## 🛠 Development Environment

### Setup for Contributors

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/ansible-discovery.git
   cd ansible-discovery
   ```

2. **Install development dependencies**

   ```bash
   # Install UV package manager (recommended)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create isolated Python environment
   uv python install 3.9
   uv venv --python 3.9
   source .venv/bin/activate
   
   # Install project dependencies
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
   
   # Ensure filter plugins are enabled
   echo "filter_plugins = ./filter_plugins" >> ansible.cfg
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
   - [Local History](https://marketplace.visualstudio.com/items?itemName=xyz.local-history)

   ```bash
   # Open project in VS Code
   code .
   ```

### Running Tests

#### Basic Testing

```bash
# Validate playbook syntax
ansible-playbook --syntax-check discovery.yaml

# Test specific discovery modules
ansible-playbook -i inventory discovery.yaml --tags java --check

# Run with debug output for troubleshooting
ansible-playbook -i inventory discovery.yaml -e debug=true -e log=true
```

#### Custom Filter Testing

Test the custom file operation filters:

```bash
# Test file_exists filter
ansible localhost -m debug -a "msg={{ '/etc/passwd' | file_exists }}"

# Test path_exists filter  
ansible localhost -m debug -a "msg={{ '/tmp' | path_exists }}"

# Test file_readable filter
ansible localhost -m debug -a "msg={{ '/etc/passwd' | file_readable }}"

# Test with non-existent file
ansible localhost -m debug -a "msg={{ '/nonexistent' | file_exists }}"

# Test with unreadable file (like /etc/shadow)
ansible localhost -m debug -a "msg={{ '/etc/shadow' | file_readable }}"

# Run comprehensive filter tests
ansible-playbook filter_plugins/tests/test_file_utils.yaml

# Or use the test runner script
./filter_plugins/tests/run_tests.sh
```

#### Performance Testing

```bash
# Time discovery execution
time ansible-playbook -i inventory discovery.yaml

# Compare with and without MongoDB caching
ansible-playbook -i inventory discovery.yaml --tags always  # First run
time ansible-playbook -i inventory discovery.yaml --tags always  # Cached run
```

#### Integration Testing

```bash
# Test MongoDB connection and caching
ansible-playbook -i inventory discovery.yaml --tags packages
mongo --eval "db.ansible_facts.find().limit(1).pretty()"

# Test tag combinations
ansible-playbook -i inventory discovery.yaml --tags "java,webservers" --check
```

### Project Structure

```text
ansible-discovery/
├── playbooks/
│   ├── discovery.yaml          # Main discovery playbook
│   ├── ansible.cfg            # Ansible configuration
│   ├── galaxy-requirements.yaml # Required collections
│   ├── filter_plugins/        # Custom Ansible filters
│   │   ├── file_utils.py      # File operation filters
│   │   ├── README.md          # Filter documentation
│   │   └── tests/             # Filter plugin tests
│   │       ├── test_file_utils.yaml  # Comprehensive filter tests
│   │       ├── run_tests.sh   # Test runner script
│   │       └── README.md      # Test documentation
│   ├── java/                  # Java application discovery
│   │   ├── java.yaml          # Main Java discovery
│   │   ├── tomcat.yaml        # Tomcat-specific discovery
│   │   ├── jboss.yaml         # JBoss/Wildfly discovery
│   │   └── jar.yaml           # Standalone JAR discovery
│   ├── webservers/            # Web server discovery
│   │   └── webservers.yaml    # Apache/Nginx discovery
│   ├── test/                  # Test playbooks
│   │   └── tomcat.yaml        # Tomcat testing
│   ├── collections/           # Downloaded Ansible collections
│   ├── inventory.example      # Example inventory file
│   └── ansible.cfg.example    # Example configuration
├── tests/                     # Unit and integration tests
├── mongodbdata/              # MongoDB data directory (ignored)
├── .vscode/                  # VS Code workspace configuration
├── .markdownlint.yaml        # Markdown linting rules
├── .gitignore                # Git ignore patterns
├── README.md                 # This documentation
├── LICENSE                   # Project license
└── pip-venv-requirements.txt # Python dependencies
```

## Configuration

### MongoDB Cache Settings

Edit `playbooks/ansible.cfg`:

```ini
[defaults]
fact_caching = community.mongodb.mongodb
fact_caching_timeout = 3600
fact_caching_connection = mongodb://localhost:27017
```

#### TTL Configuration Options

- **`fact_caching_timeout = 0`**: Infinite TTL (facts never expire)
- **`fact_caching_timeout = 3600`**: 1 hour TTL (default)
- **`fact_caching_timeout = 86400`**: 1 day TTL
- **`fact_caching_timeout = 604800`**: 1 week TTL

**Note**: With infinite TTL (`0`), you may need to manually clean old data:

```bash
# Connect to MongoDB and clean old data
mongo
use ansible_facts
db.ansible_facts.drop()
```

### Discovery Options

Available tags for selective execution:

- `packages`: Installed packages
- `services`: System services
- `ports`: Network ports
- `processes`: Running processes
- `java`: Java applications
- `webservers`: Apache/Nginx
- `tomcat`: Tomcat specific
- `jboss`: JBoss/Wildfly specific

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the existing code style
4. Test your changes thoroughly
5. Submit a pull request with detailed description

### Code Guidelines

- Use descriptive task names
- Add tags for modular execution
- Include debug tasks when `debug=true`
- Use `no_log` for sensitive data when `log=false`
- Follow Ansible best practices
- Document new discovery modules

## Roadmap

- [ ] Docker/Podman container discovery
- [ ] Python/Ruby/PHP process detection
- [ ] Grafana dashboard integration
- [ ] Enhanced Tomcat webapp analysis
- [ ] Virtual host configuration export
- [ ] Performance metrics collection

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Code Quality Standards

- **Python**: Follow PEP 8, use type hints, include docstrings
- **Ansible**: Use YAML format (.yaml), follow naming conventions
- **Markdown**: Pass markdownlint validation
- **Git**: Use conventional commit messages

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Testing

Before submitting:

```bash
# Validate syntax
ansible-playbook --syntax-check discovery.yaml

# Test custom filters
ansible localhost -m debug -a "msg={{ '/etc/passwd' | file_exists }}"

# Check markdown formatting
markdownlint README.md
```

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/andrewlinuxadmin/ansible-discovery/issues)
- **Discussions**: [GitHub Discussions](https://github.com/andrewlinuxadmin/ansible-discovery/discussions)
- **Documentation**: This README and inline code comments

## 🙏 Acknowledgments

- Built with [Ansible](https://www.ansible.com/)
- MongoDB integration via [community.mongodb](https://galaxy.ansible.com/community/mongodb)
- Process analysis powered by AWK and shell scripting
- Inspired by infrastructure automation best practices
