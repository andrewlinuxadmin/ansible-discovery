# Documentation Index

## Overview

This directory contains comprehensive documentation for the Ansible Discovery System, a modular infrastructure discovery platform with custom modules, selective collection, and MongoDB caching.

## Documentation Structure

### Main Documentation

| File                                      | Purpose                           | Audience              |
|-------------------------------------------|-----------------------------------|-----------------------|
| **[README.md](README.md)**                | Project overview and quick start  | All users             |
| **[ARCHITECTURE.md](ARCHITECTURE.md)**    | Technical architecture and design | Developers/Architects |
| **[DEPLOYMENT.md](DEPLOYMENT.md)**        | Production deployment guide       | Operations/DevOps     |

### Custom Components Documentation

| Component           | Location                                                                      | Description                   |
|---------------------|-------------------------------------------------------------------------------|-------------------------------|
| **Custom Modules**  | [playbooks/library/docs/](playbooks/library/docs/)                           | Complete module documentation |
| **Custom Filters**  | [playbooks/filter_plugins/README.md](playbooks/filter_plugins/README.md)     | File operation filters        |
| **Module Tests**    | [playbooks/library/tests/](playbooks/library/tests/)                         | Module testing framework      |
| **Filter Tests**    | [playbooks/filter_plugins/tests/](playbooks/filter_plugins/tests/)           | Filter testing framework      |

### Collector Documentation

| Collector            | Status          | Description                                       |
|----------------------|-----------------|---------------------------------------------------|
| **Java Discovery**   | ✅ Production   | Tomcat, JBoss, generic Java applications         |
| **Apache HTTP**      | ✅ Production   | Configuration parsing with apache_config_parser  |
| **PHP Discovery**    | ✅ Production   | Multi-distribution with php_config_parser        |
| **NGINX**            | 🚧 Development  | Module complete, collector integration pending    |
| **System Collectors** | ✅ Production   | Packages, services, ports, firewall, SELinux     |

## Quick Navigation

### For New Users

1. **Start Here**: [README.md](README.md) - Project overview and features
2. **Setup**: [DEPLOYMENT.md](DEPLOYMENT.md) - Installation and configuration
3. **Usage**: Run `ansible-playbook discovery.yaml` for full discovery
4. **Selective**: Use `ansible-playbook discovery.yaml -e collector_only=java`

### For Developers

1. **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) - System design and patterns
2. **Custom Modules**: [playbooks/library/docs/README.md](playbooks/library/docs/README.md)
3. **Module Examples**:
   - [process_facts.md](playbooks/library/docs/process_facts.md) - Process discovery
   - [apache_config_parser.md](playbooks/library/docs/apache_config_parser.md) - Apache parsing
   - [nginx_config_parser.md](playbooks/library/docs/nginx_config_parser.md) - NGINX parsing (dev)
   - [php_config_parser.md](playbooks/library/docs/php_config_parser.md) - PHP discovery
4. **Testing**: Module and filter test frameworks in respective `/tests/` directories

### For Operations Teams

1. **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md) - Production setup and operations
2. **Cache Management**: MongoDB operations and maintenance
3. **Troubleshooting**: Debug mode with `-e debug=true -e log=true`
4. **Performance**: Selective collection and MongoDB optimization

## Key Technical Concepts

### Selective Collection System

The system implements **absolute precedence** for selective collection:

```bash
# Single collector (absolute precedence)
ansible-playbook discovery.yaml -e collector_only=java

# All collectors (default behavior)  
ansible-playbook discovery.yaml

# Individual control (when collector_only not used)
ansible-playbook discovery.yaml -e collector_packages=false
```

### Custom Module Architecture

Four production-ready custom modules replace shell scripts:

- **process_facts**: System process discovery via `/proc` filesystem
- **apache_config_parser**: Complete Apache configuration parsing
- **php_config_parser**: Multi-distribution PHP configuration discovery  
- **nginx_config_parser**: Complete NGINX configuration parsing (integration pending)

### Caching Strategy

- **Storage**: MongoDB with configurable TTL
- **Performance**: Subsequent runs skip discovery if cached
- **Management**: Scripts in `/scripts/` for cache operations
- **Connection**: `mongodb://localhost:27017/ansible`

## Development Workflows

### Adding New Collectors

1. **Create collector**: `collectors/new_collector.yaml`
2. **Add to discovery**: Update `discovery.yaml` with include_tasks
3. **Configure variables**: Add `_collector_new` to `prereqs.yaml`
4. **Test**: `ansible-playbook discovery.yaml -e collector_only=new_collector`

### Custom Module Development

1. **Create module**: `playbooks/library/new_module.py`
2. **Document**: `playbooks/library/docs/new_module.md`
3. **Update index**: `playbooks/library/docs/README.md`
4. **Create tests**: `playbooks/library/tests/test_new_module.py`
5. **Validate**: `./library/tests/run_tests.sh`

### Custom Filter Development

1. **Add filter**: `playbooks/filter_plugins/file_utils.py`
2. **Create tests**: `playbooks/filter_plugins/tests/test_file_utils.yaml`
3. **Validate**: `./filter_plugins/tests/run_tests.sh`
4. **Document**: Update `playbooks/filter_plugins/README.md`

## Current Development Status

### Production Ready ✅

- **Core Architecture**: Selective collection with absolute precedence
- **MongoDB Caching**: TTL-based with performance optimization
- **Process Discovery**: Custom `process_facts` module
- **Apache Discovery**: Complete configuration parsing
- **PHP Discovery**: Multi-distribution support
- **System Collectors**: Packages, services, firewall, etc.
- **Custom Filters**: File operation helpers

### In Development 🚧

- **NGINX Integration**: Module complete, collector integration pending
- **Docker Support**: Container discovery and process mapping
- **Performance Optimization**: Large-scale deployment patterns

### Planned 📋

- **.NET Discovery**: .NET Core/Framework application discovery
- **Python Discovery**: Django, Flask application support
- **Ruby Discovery**: Rails application support
- **Enhanced Docker**: Complete container ecosystem discovery

## Support and Resources

### Testing

```bash
# Test custom modules
cd playbooks/
./library/tests/run_tests.sh

# Test custom filters  
./filter_plugins/tests/run_tests.sh

# Validate syntax
ansible-playbook --syntax-check discovery.yaml
```

### Code Quality

```bash
# Python linting
source ../activate  # Activate virtual environment
flake8 library/ filter_plugins/
pylint library/ filter_plugins/

# Markdown linting
markdownlint *.md --fix
```

### Getting Help

1. **Module Documentation**: Check `playbooks/library/docs/` for detailed module info
2. **Test Examples**: Review test files for usage patterns
3. **Debug Mode**: Use `-e debug=true -e log=true` for detailed output
4. **Cache Inspection**: Use MongoDB shell or `scripts/manage-cache.sh`

## Contributing

### Documentation Standards

- **Markdown**: Use markdownlint for formatting consistency
- **Code Examples**: Include working examples in all documentation
- **Module Documentation**: Follow Ansible documentation format
- **Testing**: All new features must include tests

### Code Standards

- **Python**: Follow PEP 8, include docstrings and type hints
- **Ansible**: Use descriptive task names and proper YAML formatting
- **Testing**: Maintain test coverage for all custom components
- **Versioning**: Use semantic versioning for releases
### Code Standards

- **Python**: Follow PEP 8, include docstrings and type hints
- **Ansible**: Use descriptive task names and proper YAML formatting
- **Testing**: Maintain test coverage for all custom components
- **Versioning**: Use semantic versioning for releases

- **Versioning**: Use semantic versioning for releases

## Contributing

### Documentation Standards
- Use clear, descriptive headings
- Include working code examples
- Provide troubleshooting sections
- Maintain consistent formatting
- Update this index when adding new docs

### Code Documentation
- Document all variables and their defaults
- Include usage examples for each module
- Explain container-specific behavior
- Provide error handling patterns

## Support

### Common Issues
- **Permission Problems**: See graceful degradation patterns in ARCHITECTURE.md
- **Container Detection**: Multi-method detection examples in collectors/README.md
- **Cache Issues**: MongoDB operations guide in DEPLOYMENT.md
- **Java Discovery**: Detailed troubleshooting in java/README.md

### Debugging Resources
- **Debug Mode**: Use `-e debug=true -e log=true`
- **Single Collector**: Use `-e collector_only=COLLECTOR`
- **Verbose Output**: Add `-vvv` to ansible-playbook commands
- **Cache Inspection**: MongoDB queries in DEPLOYMENT.md

### Getting Help
1. Check relevant documentation section first
2. Review troubleshooting guides in component docs
3. Use debug mode for detailed execution information
4. Inspect MongoDB cache for stored facts

## Technical Specifications

### System Requirements
- Ansible 2.14+
- Python 3.9+
- MongoDB 4.4+ (for caching)
- Required collections: see galaxy-requirements.yaml

### Supported Platforms
- **Primary**: RHEL family (8+)
- **Secondary**: Ubuntu/Debian, SUSE
- **Containers**: Docker, Podman, LXC
- **Cloud**: AWS, Azure, GCP instances

### Performance Characteristics
- **Execution Time**: 30-120 seconds per host (depending on collectors)
- **Memory Usage**: 200-500MB per ansible-playbook process
- **Network**: Minimal traffic, primarily SSH
- **Storage**: MongoDB cache grows with discovered facts

## Version Information

### Current Version
- **Discovery System**: 2.0.0 (selective collection architecture)
- **Documentation**: 2.0.0 (complete rewrite)
- **Collections**: See galaxy-requirements.yaml for versions

### Compatibility Matrix
- **Ansible**: 2.14-2.16 (tested)
- **Python**: 3.9-3.12 (supported)
- **MongoDB**: 4.4-7.0 (compatible)
- **Platforms**: See support matrix in DEPLOYMENT.md
