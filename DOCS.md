# Documentation Index

## Overview

Comprehensive documentation for the Ansible Discovery System — a modular
infrastructure discovery platform with custom modules, selective collection,
and JSON file-based fact caching.

## Documentation Structure

### Main Documentation

| File                                      | Purpose                           | Audience              |
|-------------------------------------------|-----------------------------------|-----------------------|
| **[README.md](README.md)**                | Project overview and quick start  | All users             |
| **[ARCHITECTURE.md](ARCHITECTURE.md)**    | Technical architecture and design | Developers/Architects |
| **[DEPLOYMENT.md](DEPLOYMENT.md)**        | Deployment and operations guide   | Operations/DevOps     |

### Custom Components Documentation

| Component           | Location                                                                  | Description                   |
|---------------------|---------------------------------------------------------------------------|-------------------------------|
| **Custom Modules**  | [playbooks/library/docs/](playbooks/library/docs/)                       | Complete module documentation |
| **Custom Filters**  | [playbooks/filter_plugins/README.md](playbooks/filter_plugins/README.md) | File operation filters        |
| **Module Tests**    | [playbooks/library/tests/](playbooks/library/tests/)                     | Module testing framework      |
| **Filter Tests**    | [playbooks/filter_plugins/tests/](playbooks/filter_plugins/tests/)       | Filter testing framework      |

### Collector Status

| Collector            | Status      | Description                                       |
|----------------------|-------------|---------------------------------------------------|
| **Java Discovery**   | Production  | Tomcat, JBoss, generic Java applications          |
| **Apache HTTP**      | Production  | Configuration parsing with apache_config_parser   |
| **PHP Discovery**    | Production  | Multi-distribution with php_config_parser         |
| **NGINX**            | Development | Module complete, collector integration pending     |
| **System Collectors**| Production  | Packages, services, ports, firewall, SELinux      |

## Quick Navigation

### For New Users

1. **Start Here**: [README.md](README.md) — Project overview and quick start
2. **Setup**: Clone, install collections, run `ansible-playbook discovery.yaml`
3. **Selective**: Use `-e collector_only=java` to run a single collector

### For Developers

1. **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) — System design and patterns
2. **Custom Modules**: [playbooks/library/docs/](playbooks/library/docs/)
3. **Testing**: Module and filter test frameworks in `/tests/` directories

### For Operations Teams

1. **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md) — Installation, configuration, troubleshooting
2. **Cache Management**: Delete files in `facts_cache/` to clear cached data
3. **Debugging**: Use `-e debug=true -e log=true -vvv`

## Key Technical Concepts

### Selective Collection System

```bash
# Single collector (absolute precedence)
ansible-playbook discovery.yaml -e collector_only=java

# All collectors (default)
ansible-playbook discovery.yaml

# Disable specific collectors
ansible-playbook discovery.yaml -e collector_packages=false
```

### Fact Caching (JSON Files)

All discovered facts are cached as one JSON file per host in
`playbooks/facts_cache/`. The directory is created automatically.
All important facts use `cacheable: true` so subsequent runs skip
re-discovery when cached data exists.

```bash
# View cached data
cat playbooks/facts_cache/server1.example.com | python3 -m json.tool

# Clear cache
rm -rf playbooks/facts_cache/*
```

## HTML Report Generator

### Overview

The `ansible-discovery-report.py` script generates a comprehensive HTML report
from JSON fact data collected by the playbooks.

### Features

- **Sidebar navigation** with categorized host list
- **Summary tables**: OS distribution, application inventory
- **Detail sections**: per-host Java, PHP, Apache/NGINX configuration
- **RHEL upgrade eligibility**: Analysis identifying which servers can be
  converted to RHEL and upgraded to supported versions (8+)
- **Sortable tables**: Click column headers to sort
- **Fully configurable**: All text, colors, and labels defined in
  `ansible-discovery-report.ini`

### Configuration (`ansible-discovery-report.ini`)

The INI file controls all text output and visual settings:

| Section           | Purpose                                             |
|-------------------|-----------------------------------------------------|
| `[general]`       | Customer name, version, date format                 |
| `[colors]`        | Status badge colors (eligible, ineligible, etc.)    |
| `[report]`        | HTML title, page heading                            |
| `[sidebar]`       | Sidebar labels                                      |
| `[nav]`           | Navigation section names                            |
| `[headings]`      | Section headings in the report body                 |
| `[table_headers]` | Column headers for every table                      |
| `[labels]`        | Status labels, field descriptions                   |
| `[messages]`      | Informational/empty-state messages                  |
| `[eligibility]`   | Upgrade eligibility criteria and status labels      |

### Input Format

The script reads a JSON file (default `export.json`) containing an array
of objects with this structure:

```json
[
  {
    "_id": "ansible_factsserver1.example.com",
    "data": {
      "ansible_hostname": "server1",
      "ansible_distribution": "CentOS",
      "ansible_distribution_major_version": "7",
      ...
    }
  }
]
```

> **Note**: This format was originally designed for MongoDB exports.
> To use with `jsonfile` cache data, aggregate the per-host JSON files into
> this array format. Example:
>
> ```bash
> cd playbooks/facts_cache
> python3 -c "
> import json, glob, os
> result = []
> for f in glob.glob('*'):
>     with open(f) as fh:
>         data = json.load(fh)
>         result.append({'_id': 'ansible_facts' + os.path.basename(f), 'data': data})
> print(json.dumps(result, indent=2))
> " > ../export.json
> ```

### Usage

```bash
# Default (reads export.json, outputs ansible-discovery-report.html)
python3 ansible-discovery-report.py

# Custom paths
python3 ansible-discovery-report.py --config custom.ini --input data.json --output report.html
```

### Command-Line Arguments

| Argument     | Default                          | Description          |
|--------------|----------------------------------|----------------------|
| `--config`   | `ansible-discovery-report.ini`   | INI configuration    |
| `--input`    | `export.json`                    | Input JSON data file |
| `--output`   | `ansible-discovery-report.html`  | Output HTML file     |

## Development Workflows

### Adding New Collectors

1. Create collector: `collectors/new_collector.yaml`
2. Update `discovery.yaml` with `include_tasks`
3. Add variable `_collector_new` to `prereqs.yaml`
4. Test: `ansible-playbook discovery.yaml -e collector_only=new_collector`

### Custom Module Development

1. Create module: `playbooks/library/new_module.py`
2. Document: `playbooks/library/docs/new_module.md`
3. Create tests: `playbooks/library/tests/test_new_module.py`
4. Validate: `./library/tests/run_tests.sh`

### Custom Filter Development

1. Add filter: `playbooks/filter_plugins/file_utils.py`
2. Create tests: `playbooks/filter_plugins/tests/test_file_utils.yaml`
3. Validate: `./filter_plugins/tests/run_tests.sh`
4. Document: Update `playbooks/filter_plugins/README.md`

## Technical Specifications

### System Requirements

- Ansible 2.14+
- Python 3.9+
- Required collections: see `galaxy-requirements.yaml`

### Supported Platforms

- **Primary**: RHEL family (7+)
- **Secondary**: Ubuntu/Debian, SUSE
- **Containers**: Docker, Podman, LXC
- **Cloud**: AWS, Azure, GCP instances
