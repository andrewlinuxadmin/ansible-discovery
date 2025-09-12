# Changelog - Ansible Discovery Project

## Version 2.0 (September 2025)

### 🎉 Major Features Completed

#### ✅ NGINX Discovery Module - Production Ready
- **Complete NGINX configuration parsing** with `nginx_config_parser` module
- **Software Collections (SCL) support** - detects processes like `nginx: master process`
- **PHP-FPM integration detection** - automatically identifies FastCGI configuration
- **Multi-format output** - both readable hierarchical and technical crossplane formats
- **Include file expansion** - processes all included configuration files
- **Cross-platform compatibility** - RHEL, Debian, SUSE support

#### ✅ Enhanced PHP Configuration Discovery
- **Dynamic version discovery** - auto-detects installed PHP versions from system directories
- **Software Collections support** - handles SCL PHP installations (rh-php74, etc.)
- **Multi-distribution compatibility** - unified output across RHEL, Debian, SUSE
- **Intelligent fallback** - graceful handling when directories are inaccessible

### 🔧 Technical Improvements

#### Module Enhancements
- **Python 2.7 compatibility** - fixed f-string usage in nginx_config_parser for CentOS 6
- **Robust error handling** - graceful degradation when configuration files are missing
- **Memory efficient parsing** - optimized for large configuration files

#### Discovery Pipeline
- **Process detection improvements** - better handling of containerized and SCL environments
- **Enhanced regex patterns** - more accurate version detection across distributions
- **Conditional execution** - smarter filtering of hosts based on detected processes

### 📊 Updated Capabilities

#### Web Server Support
- **Apache HTTPD**: ✅ Complete (VirtualHosts, modules, configuration parsing)
- **NGINX**: ✅ Complete (server blocks, PHP-FPM detection, includes)

#### Application Platforms
- **Java**: ✅ Complete (Tomcat, JBoss/Wildfly, JAR analysis)
- **PHP**: ✅ Complete (dynamic versions, extensions, multi-distro)

#### System Discovery
- **Processes**: ✅ Complete (container detection, comprehensive info)
- **Services**: ✅ Complete (status, configuration)
- **Network**: ✅ Complete (ports, listening services)
- **Security**: ✅ Complete (firewall, SELinux)

### 🎯 Usage Examples

#### NGINX Discovery
```bash
# Full NGINX discovery
ansible-playbook discovery.yaml -e collector_only=nginx

# Test NGINX config parser directly
ansible localhost -m nginx_config_parser -a "path=/etc/nginx/nginx.conf"
```

#### PHP Discovery with Dynamic Versions
```bash
# Auto-detects all installed PHP versions
ansible-playbook discovery.yaml -e collector_only=php
```

### 📝 Documentation Updates

- **README.md**: Updated with current status and capabilities
- **Module documentation**: Complete API reference for all modules
- **TODO.yaml**: Reorganized with completed vs. planned features
- **Architecture diagrams**: Reflects current modular design

### 🔮 Next Steps

#### Planned Features (Q4 2025)
- **Container Discovery**: Docker and Podman integration
- **Additional Languages**: .NET, Python, Ruby application discovery
- **Enhanced Reporting**: Grafana dashboard for infrastructure visualization
- **Security Scanning**: Vulnerability and compliance checking

---

**Migration Notes**: 
- All modules are now production-ready
- NGINX module requires no additional dependencies
- PHP discovery automatically adapts to system configuration
- Backward compatibility maintained for all existing playbooks
