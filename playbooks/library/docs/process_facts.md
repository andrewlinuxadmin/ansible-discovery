# process_facts

Collect detailed process information from the Linux /proc filesystem.

## Synopsis

- Gathers comprehensive process details from the /proc filesystem
- Compatible with Python 2.7+ and Python 3.x environments  
- Pure Python implementation requiring no external dependencies
- Provides container detection capabilities for modern containerized environments
- Designed for system discovery, monitoring, and analysis workflows
- Efficiently handles large numbers of processes with optional kernel thread filtering

## Requirements

The below requirements are needed on the host that executes this module.

- Linux operating system with /proc filesystem
- Python 2.7+ or Python 3.x
- Read access to /proc filesystem entries

## Parameters

| Parameter               | Type    | Required | Default | Description                                                                                                                                                   |
|-------------------------|---------|----------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| exclude_kernel_threads  | boolean | no       | true    | Exclude kernel threads from results. Kernel threads typically have no command line arguments and run in kernel space, making them less relevant for application discovery |
| detect_containers       | boolean | no       | true    | Detect containerized processes by examining cgroup information and container runtime indicators                                                                |

## Return Values

Common return values are documented in the [Ansible documentation](https://docs.ansible.com/ansible/latest/reference_appendices/common_return_values.html), the following are the fields unique to this module:

| Key | Returned | Type | Description |
|-----|----------|------|-------------|
| ansible_facts | always | dictionary | Process information added to Ansible facts |
| ansible_facts.processes | always | list | List of all discovered processes with detailed information |

### Process Object Structure

Each process in the `ansible_facts.processes` list contains the following fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| pid | string | Process ID | "1234" |
| ppid | string | Parent Process ID | "1" |
| user | string | Username running the process | "apache" |
| command | string | Base command name (executable) | "httpd" |
| args | string | Full command line with arguments | "/usr/sbin/httpd -DFOREGROUND" |
| containerized | boolean | Whether process is running in a container | true |
| homedir | string | Home directory of the process user | "/home/apache" |
| state | string | Process state (R=running, S=sleeping, D=disk sleep, Z=zombie, T=stopped) | "S" |
| threads | integer | Number of threads used by the process | 8 |
| memory_kb | integer | Memory usage in kilobytes | 45120 |
| cpu_percent | float | CPU usage percentage | 2.5 |

## Examples

### Basic Usage

```yaml
- name: Collect all process information
  process_facts:
  register: system_processes

- name: Display total number of processes
  debug:
    msg: "Found {{ system_processes.ansible_facts.processes | length }} processes"
```

### Advanced Filtering and Analysis

```yaml
- name: Collect processes including kernel threads
  process_facts:
    exclude_kernel_threads: false
    detect_containers: true
  register: all_processes

- name: Find Java applications
  debug:
    msg: "Java process: {{ item.command }} (PID: {{ item.pid }}, User: {{ item.user }})"
  loop: "{{ all_processes.ansible_facts.processes }}"
  when: "'java' in item.args"

- name: Identify high memory usage processes
  debug:
    msg: "High memory process: {{ item.command }} using {{ item.memory_kb }}KB"
  loop: "{{ all_processes.ansible_facts.processes }}"
  when: item.memory_kb | int > 100000
```

### Container Detection

```yaml
- name: Find containerized processes
  debug:
    msg: "Container process: {{ item.command }} ({{ item.args }})"
  loop: "{{ system_processes.ansible_facts.processes }}"
  when: item.containerized | bool

- name: Count containerized vs native processes
  debug:
    msg: 
      - "Containerized: {{ system_processes.ansible_facts.processes | selectattr('containerized') | list | length }}"
      - "Native: {{ system_processes.ansible_facts.processes | rejectattr('containerized') | list | length }}"
```

### User and Permission Analysis

```yaml
- name: Find processes running as specific user
  debug:
    msg: "{{ item.user }} process: {{ item.command }}"
  loop: "{{ system_processes.ansible_facts.processes }}"
  when: item.user == "apache"

- name: Identify processes by state
  debug:
    msg: "{{ item.state }} process: {{ item.command }} (PID {{ item.pid }})"
  loop: "{{ system_processes.ansible_facts.processes }}"
  when: item.state in ['Z', 'D']  # Zombie or uninterruptible sleep
```

### Web Server Discovery

```yaml
- name: Discover web servers
  set_fact:
    web_servers: >-
      {{
        system_processes.ansible_facts.processes |
        selectattr('command', 'match', '(httpd|apache2|nginx)') |
        list
      }}

- name: Display web server information
  debug:
    msg: 
      - "Web server: {{ item.command }}"
      - "PID: {{ item.pid }}"
      - "User: {{ item.user }}"
      - "Memory: {{ item.memory_kb }}KB"
      - "Containerized: {{ item.containerized }}"
  loop: "{{ web_servers }}"
```

## Notes

### Performance Considerations

- The module reads directly from /proc filesystem which is generally fast
- Large systems with thousands of processes may take longer to scan
- Kernel thread exclusion (default) significantly reduces processing time on busy systems
- Container detection adds minimal overhead per process

### Permission Requirements

- Requires read access to /proc filesystem
- Some process information may be limited when running as non-root user
- Memory and CPU statistics require access to /proc/[pid]/stat and /proc/[pid]/status

### Container Detection Method

- Examines /proc/[pid]/cgroup for container runtime indicators
- Looks for Docker, Podman, LXC, and other container technologies
- Detection is heuristic-based and may not catch all containerization methods

### Process State Codes

- **R**: Running or runnable (on run queue)
- **S**: Interruptible sleep (waiting for an event to complete)
- **D**: Uninterruptible sleep (usually IO)
- **Z**: Zombie (terminated but not reaped by parent)
- **T**: Stopped (on a signal or because it is being traced)

### Limitations

- Only works on Linux systems with /proc filesystem
- Process information represents a snapshot at execution time
- High-frequency process creation/termination may be missed
- Memory values are approximate and may not match other tools exactly

## Best Practices

### Efficient Usage

```yaml
# Good: Exclude kernel threads for application discovery
- name: Find application processes
  process_facts:
    exclude_kernel_threads: true

# Good: Use specific filtering
- name: Find specific applications
  debug:
    msg: "Found {{ item.command }}"
  loop: "{{ ansible_facts.processes }}"
  when: item.command in ['java', 'python', 'node']
```

### Integration with Other Modules

```yaml
# Use with service facts for comprehensive discovery
- name: Gather service facts
  service_facts:

- name: Gather process facts  
  process_facts:

- name: Correlate services and processes
  debug:
    msg: "Service {{ item.key }} has processes: {{ ansible_facts.processes | selectattr('command', 'equalto', item.key) | list | length }}"
  loop: "{{ ansible_facts.services | dict2items }}"
  when: item.value.state == "running"
```

## Author

- Andrew Carlos (@andrewlinuxadmin)

## Collection

This module is part of the ansible-discovery collection.
