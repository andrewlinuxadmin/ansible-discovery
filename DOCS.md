# Documentation Index

## Overview

This directory contains comprehensive documentation for the Ansible Discovery System, a selective collection architecture for automated infrastructure discovery.

## Documentation Structure

### Main Documentation

| File | Purpose | Audience |
|------|---------|----------|
| **[README.md](README.md)** | Project overview and quick start | All users |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical architecture and design | Developers/Architects |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Production deployment guide | Operations/DevOps |

### Component Documentation

| Component | File | Description |
|-----------|------|-------------|
| **System Collectors** | [collectors/README.md](collectors/README.md) | Detailed system collection modules |
| **Java Discovery** | [java/README.md](java/README.md) | Java application discovery pipeline |
| **Custom Filters** | [playbooks/filter_plugins/README.md](playbooks/filter_plugins/README.md) | Custom Ansible filters |
| **Filter Tests** | [playbooks/filter_plugins/tests/README.md](playbooks/filter_plugins/tests/README.md) | Filter testing framework |

## Quick Navigation

### For New Users
1. Start with **[README.md](README.md)** for project overview
2. Follow **[DEPLOYMENT.md](DEPLOYMENT.md)** for setup instructions
3. Explore **[collectors/README.md](collectors/README.md)** for available collectors

### For Developers
1. Review **[ARCHITECTURE.md](ARCHITECTURE.md)** for system design
2. Study **[java/README.md](java/README.md)** for complex discovery patterns
3. Examine **[filter_plugins/README.md](playbooks/filter_plugins/README.md)** for custom extensions

### For Operations Teams
1. **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment
2. **[README.md](README.md)** - Daily usage patterns
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Troubleshooting reference

## Key Concepts

### Selective Collection System
- **collector_only**: Absolute precedence for single collector execution
- **collector_NAME**: Individual collector control when collector_only not used
- **Hybrid Discovery**: fedora.linux_system_roles with manual fallbacks

### Architecture Patterns
- **Multi-Stage Discovery**: Prerequisites → Collection → Analysis → Consolidation
- **Container Awareness**: Automatic detection and behavior adjustment
- **Graceful Degradation**: Fallback methods for missing dependencies
- **MongoDB Caching**: Persistent fact storage with TTL control

### Java Discovery Pipeline
- **Process Classification**: Automatic detection of Tomcat, JBoss, Spring Boot, Quarkus
- **Configuration Analysis**: Deep inspection of application configurations
- **Version Detection**: JVM and application version discovery
- **Data Consolidation**: Unified output format across application types

## Recent Updates

### Documentation Rewrite (Latest)
- Completely restructured all documentation to reflect current architecture
- Added comprehensive technical architecture guide
- Created detailed deployment and operations manual
- Expanded Java discovery documentation with examples
- Improved collector documentation with usage patterns

### Architecture Improvements
- Implemented selective collection system with absolute precedence
- Added hybrid discovery pattern using fedora.linux_system_roles
- Enhanced container detection and behavior adjustment
- Integrated MongoDB caching with infinite TTL for development

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
