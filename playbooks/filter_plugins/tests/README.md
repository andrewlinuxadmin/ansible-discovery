# Filter Plugin Tests

## Overview

This directory contains comprehensive tests for the custom file utility filters:

- `file_exists`
- `path_exists`
- `file_readable`

## Test Structure

### `test_file_utils.yaml`

Main test playbook that validates:

#### ✅ **Basic Functionality**

- File existence detection
- Path existence detection (files and directories)
- File readability validation
- Proper handling of nonexistent files

#### 🛡️ **Error Handling**

- Empty string inputs
- Null value inputs
- Invalid path handling

#### 🔄 **Comparative Testing**

- Verifies different behaviors between filters
- Validates expected results for various file types
- Ensures filters work as documented

#### ⚡ **Performance Testing**

- Tests filters with file lists
- Validates performance with multiple iterations

## Running Tests

### Quick Test

```bash
# From the playbooks directory
ansible-playbook filter_plugins/tests/test_file_utils.yaml
```

### Using Test Runner

```bash
# From anywhere in the project
cd playbooks
./filter_plugins/tests/run_tests.sh
```

### Verbose Output

```bash
ansible-playbook filter_plugins/tests/test_file_utils.yaml -v
```

## Test Coverage

### Files Used in Tests

| File/Path | Purpose | Expected Results |
|-----------|---------|------------------|
| `/etc/passwd` | Readable file test | All filters: `true` |
| `/etc/shadow` | Unreadable file test | `file_exists`: `true`, `file_readable`: `false` |
| `/etc` | Directory test | `path_exists`: `true`, others: `false` |
| `/nonexistent/file` | Missing file test | All filters: `false` |
| `/tmp/ansible_filter_test_file` | Temporary test file | All filters: `true` |

### Test Scenarios

#### ✅ **Positive Tests**

- Readable files return correct values
- Directories are properly detected
- Temporary files work correctly

#### ❌ **Negative Tests**

- Nonexistent files return false
- Unreadable files behave correctly
- Directories fail file-specific tests

#### 🔧 **Edge Cases**

- Empty string handling
- Null value handling
- Permission boundary testing

## Expected Output

When tests pass, you'll see output like:

```
✅ file_exists correctly identified readable file
✅ path_exists correctly identified directory
✅ file_readable correctly identified unreadable file
🎉 All filter tests completed successfully!
```

## Troubleshooting

### Common Issues

#### Filter Not Found Error

```
ERROR! filter_plugins not configured
```

**Solution**: Ensure `ansible.cfg` contains:

```ini
filter_plugins = ./filter_plugins
```

#### Permission Denied

```
FAILED - permission denied
```

**Solution**: Run from directory with proper permissions, usually `playbooks/`

#### Test File Creation Failed

```
FAILED - could not create /tmp/ansible_filter_test_file
```

**Solution**: Ensure `/tmp` is writable or modify `temp_test_file` variable

### Debugging

Run with increased verbosity:

```bash
ansible-playbook filter_plugins/tests/test_file_utils.yaml -vvv
```

Check filter plugin loading:

```bash
ansible-doc -t filter file_exists
```

## Adding New Tests

To add new test cases:

1. Add test scenarios to `test_file_utils.yaml`
2. Use `assert` tasks for validation
3. Include both positive and negative test cases
4. Add meaningful success/failure messages

### Example Test Addition

```yaml
- name: "Test new filter functionality"
  assert:
    that:
      - some_condition | new_filter
    fail_msg: "New filter test failed"
    success_msg: "✅ New filter works correctly"
```

## Integration with CI/CD

These tests can be integrated into CI/CD pipelines:

```bash
# In CI script
cd playbooks
ansible-playbook filter_plugins/tests/test_file_utils.yaml --check
```

## Performance Considerations

- Tests create temporary files in `/tmp`
- Most tests complete in under 10 seconds
- Performance test loops through multiple files
- All temporary files are cleaned up automatically
