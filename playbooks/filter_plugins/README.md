# Custom Ansible Filters

This directory contains custom Ansible filters that extend the functionality
of the discovery system.

## Available Filters

### `file_exists`

Checks if a specific file exists on the filesystem.

**Syntax:** `path | file_exists`

**Returns:** Boolean (`true` if file exists, `false` otherwise)

**Example:**

```yaml
- name: Check if Apache config exists
  debug:
    msg: "Apache config found!"
  when: "/etc/httpd/conf/httpd.conf" | file_exists
```

### `path_exists`

Checks if a path exists (file or directory).

**Syntax:** `path | path_exists`

**Returns:** Boolean (`true` if path exists, `false` otherwise)

**Example:**

```yaml
- name: Check if Apache directory exists
  debug:
    msg: "Apache directory found!"
  when: "/etc/httpd" | path_exists
```

### `file_readable`

Checks if a file exists and is readable by the current user.

**Syntax:** `path | file_readable`

**Returns:** Boolean (`true` if file exists and is readable, `false` otherwise)

**Example:**

```yaml
- name: Check if log file is readable
  debug:
    msg: "Log file is accessible!"
  when: "/var/log/httpd/access_log" | file_readable
```

## Performance Benefits

These filters provide better performance compared to multiple `stat` module calls:

**Before (using stat):**

```yaml
- name: Check multiple files
  stat:
    path: "{{ item }}"
  loop:
    - /etc/httpd/conf/httpd.conf
    - /etc/nginx/nginx.conf
    - /etc/apache2/apache2.conf
  register: config_files

- name: Process only existing files
  debug:
    msg: "Found config: {{ item.item }}"
  loop: "{{ config_files.results }}"
  when: item.stat.exists
```

**After (using filters):**

```yaml
- name: Process only existing files
  debug:
    msg: "Found config: {{ item }}"
  loop:
    - /etc/httpd/conf/httpd.conf
    - /etc/nginx/nginx.conf
    - /etc/apache2/apache2.conf
  when: item | file_exists
```

## Configuration

Ensure `filter_plugins` is configured in your `ansible.cfg`:

```ini
[defaults]
filter_plugins = ./filter_plugins
```

## Testing

Run the test suite to validate filter functionality:

```bash
./filter_plugins/tests/run_tests.sh
```

## Implementation

The filters are implemented in `file_utils.py` using Python's `os.path`
module for cross-platform compatibility.
