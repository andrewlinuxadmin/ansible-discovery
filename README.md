# Ansible Discovery

**Automated infrastructure discovery for Linux servers using Ansible**

Collects detailed information about running processes, Java applications, web servers, and other services, storing the data in MongoDB for analysis and reporting.

## Features

- **Process Discovery**: Detects running processes excluding kernel threads
- **Java Applications**: Deep analysis of Tomcat, JBoss/Wildfly, Spring Boot, Quarkus, and JAR applications
- **Web Servers**: Apache HTTPD and Nginx detection with virtual host extraction
- **Service Information**: Packages, services, and network ports
- **Persistent Cache**: MongoDB storage with configurable TTL
- **Modular Design**: Tag-based execution for selective discovery

## Quick Start

### Prerequisites

- Linux system with Python 3.9+
- MongoDB instance (for fact caching)
- Target servers accessible via SSH
- Sudo access on target machines

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/andrewlinuxadmin/ansible-discovery.git
   cd ansible-discovery
   ```

2. **Install UV package manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Setup Python environment**
   ```bash
   uv python install 3.9
   uv venv --python 3.9
   source .venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r pip-venv-requirements.txt
   ```

5. **Install Ansible collections**
   ```bash
   cd playbooks
   ansible-galaxy collection install -r galaxy-requirements.yaml
   ```

6. **Configure inventory**
   ```bash
   # Create your inventory file
   cp inventory.example inventory
   # Edit inventory with your target servers
   ```

7. **Start MongoDB (if not running)**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name ansible-discovery-mongo mongo:latest
   
   # Or start local MongoDB service
   sudo systemctl start mongod
   ```

### Usage

```bash
# Full discovery on all hosts
ansible-playbook -i inventory collector.yaml

# Discover only Java applications
ansible-playbook -i inventory collector.yaml --tags java

# Discover only web servers
ansible-playbook -i inventory collector.yaml --tags webservers

# Simple facts collection (no caching)
ansible-playbook -i inventory simple.yaml
```

## Development Environment

### Setup for Contributors

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/ansible-discovery.git
   cd ansible-discovery
   ```

2. **Install development dependencies**
   ```bash
   # Install UV package manager
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create isolated Python environment
   uv python install 3.9
   uv venv --python 3.9 venv-dev
   source venv-dev/bin/activate
   
   # Install project dependencies
   pip install -r pip-venv-requirements.txt
   ```

3. **Setup Ansible collections**
   ```bash
   cd playbooks
   mkdir -p collections
   ansible-galaxy collection install -r galaxy-requirements.yaml
   ```

4. **Configure test environment**
   ```bash
   # Copy example configurations
   cp ansible.cfg.example ansible.cfg
   cp inventory.example inventory
   
   # Setup MongoDB for testing
   docker run -d -p 27017:27017 --name test-mongo mongo:latest
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

```bash
# Test basic functionality
ansible-playbook -i inventory test/tomcat.yaml

# Validate playbook syntax
ansible-playbook --syntax-check collector.yaml

# Run with debug output
ansible-playbook -i inventory collector.yaml -e debug=true -e log=true
```

### Project Structure

```
ansible-discovery/
├── playbooks/
│   ├── collector.yaml          # Main discovery playbook
│   ├── simple.yaml            # Basic facts collection
│   ├── ansible.cfg            # Ansible configuration
│   ├── galaxy-requirements.yaml # Required collections
│   ├── java/                  # Java application discovery
│   │   ├── java.yaml
│   │   ├── tomcat.yaml
│   │   ├── jboss.yaml
│   │   └── jar.yaml
│   ├── webservers/            # Web server discovery
│   │   └── webservers.yaml
│   └── test/                  # Test playbooks
├── mongodbdata/               # MongoDB data directory
└── pip-venv-requirements.txt  # Python dependencies
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

## License

[MIT License](LICENSE)

## Support

For questions or issues, please open a GitHub issue or contact the maintainers.

