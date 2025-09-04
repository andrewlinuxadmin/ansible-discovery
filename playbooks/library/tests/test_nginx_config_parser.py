#!/usr/bin/env python3
"""
Test script for nginx_config_parser Ansible module
Tests both readable and crossplane formats using actual nginx.conf and
mime.types files

This module is based on nginx-crossplane:
https://github.com/nginxinc/crossplane
"""

import sys
import os
import json

# Add parent directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_nginx_config_parser():
    """Test the nginx_config_parser module with real configuration files"""

    # Import the module from parent directory
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    # Create a mock module for testing
    class MockAnsibleModule:
        def __init__(self, params):
            self.params = params

        def fail_json(self, **kwargs):
            raise Exception(f"Module failed: {kwargs}")

        def exit_json(self, **kwargs):
            self.result = kwargs

    # Get the test directory path
    test_dir = os.path.dirname(os.path.abspath(__file__))
    nginx_conf_path = os.path.join(test_dir, 'nginx.conf')

    print("=== NGINX Config Parser Test ===")
    print(f"Testing with: {nginx_conf_path}")
    print()

    # Test 1: Basic parsing with readable format (default)
    print("1. Testing readable format (default)...")
    try:
        def test_main_wrapper(params):
            # Call the actual implementation
            import nginx_config_parser as ncp
            result = ncp.parse(
                filename=params.get('path'),
                comments=params.get('include_comments', False),
                single=params.get('single_file', False),
                ignore=params.get('ignore_directives', []),
                strict=params.get('strict', False),
                combine=params.get('combine', False)
            )

            # Convert to readable format if needed
            if not params.get('crossplane_format', False):
                if result['status'] == 'ok' and result['config']:
                    result = ncp.create_readable_nginx_config(result)

            return {
                'changed': False,
                'config': result,
                'errors': result.get('errors', [])
            }

        result1 = test_main_wrapper({
            'path': nginx_conf_path,
            'include_comments': False,
            'single_file': False,
            'ignore_directives': [],
            'strict': False,
            'combine': False,
            'crossplane_format': False
        })

        print(f"   Status: {result1['config']['status']}")
        print(f"   Errors: {len(result1['config'].get('errors', []))}")
        if result1['config']['status'] == 'ok':
            config = result1['config'].get('config', {})
            if config:
                print(f"   Found sections: {list(config.keys())}")
                if 'http' in config:
                    print(f"   HTTP directives: {len(config['http'])}")
            else:
                print("   No config data found")
        print()

    except Exception as e:
        print(f"   Error: {e}")
        result1 = {'config': {'status': 'failed', 'errors': [str(e)]}}

    # Test 2: Crossplane format
    print("2. Testing crossplane format...")
    try:
        result2 = test_main_wrapper({
            'path': nginx_conf_path,
            'crossplane_format': True
        })

        print(f"   Status: {result2['config']['status']}")
        print(f"   Errors: {len(result2['config'].get('errors', []))}")
        if result2['config']['status'] == 'ok':
            files = result2['config']['config']
            print(f"   Files parsed: {len(files)}")
            for file_info in files:
                print(f"     - {file_info['file']}: {file_info['status']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        result2 = {'config': {'status': 'failed', 'errors': [str(e)]}}

    # Test 3: With comments
    print("3. Testing with comments included...")
    try:
        result3 = test_main_wrapper({
            'path': nginx_conf_path,
            'include_comments': True,
            'crossplane_format': False
        })

        print(f"   Status: {result3['config']['status']}")
        has_comments = bool([d for d in str(result3) if 'comment' in str(d)])
        print(f"   Has comments: {has_comments}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        result3 = {'config': {'status': 'failed', 'errors': [str(e)]}}

    # Test 4: Single file mode (ignore includes)
    print("4. Testing single file mode...")
    try:
        result4 = test_main_wrapper({
            'path': nginx_conf_path,
            'single_file': True,
            'crossplane_format': False
        })

        print(f"   Status: {result4['config']['status']}")
        print("   Single file mode: includes ignored")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        result4 = {'config': {'status': 'failed', 'errors': [str(e)]}}

    # Test 5: Security test with ignored directives
    print("5. Testing with ignored directives...")
    try:
        result5 = test_main_wrapper({
            'path': nginx_conf_path,
            'ignore_directives': ['error_log', 'access_log'],
            'crossplane_format': False
        })

        print(f"   Status: {result5['config']['status']}")
        print("   Ignored directives: error_log, access_log")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        result5 = {'config': {'status': 'failed', 'errors': [str(e)]}}

    # Test 6: Format comparison
    print("6. Format comparison...")
    try:
        if (result1['config']['status'] == 'ok' and
                result2['config']['status'] == 'ok'):
            readable_size = len(json.dumps(result1['config']['config']))
            crossplane_size = len(json.dumps(result2['config']['config']))
            print(f"   Readable format size: {readable_size} chars")
            print(f"   Crossplane format size: {crossplane_size} chars")
            is_larger = ('larger' if readable_size > crossplane_size
                         else 'smaller')
            print(f"   Readable is {is_larger}")
    except Exception as e:
        print(f"   Error in comparison: {e}")
    print()

    # Summary
    print("=== Test Summary ===")
    tests = [result1, result2, result3, result4, result5]
    passed = sum(1 for r in tests if r['config']['status'] == 'ok')
    print(f"Tests passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        for i, result in enumerate(tests, 1):
            if result['config']['status'] != 'ok':
                errors = result['config'].get('errors', [])
                print(f"   Test {i} failed: {errors}")
        return False


def show_sample_output():
    """Show sample of readable format output"""
    import sys
    import os

    test_dir = os.path.dirname(os.path.abspath(__file__))
    nginx_conf_path = os.path.join(test_dir, 'nginx.conf')

    # Import the module from parent directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)

    import nginx_config_parser as ncp

    print("\n=== Sample Readable Format Output ===")
    try:
        result = ncp.parse(
            filename=nginx_conf_path,
            comments=False,
            single=False,
            ignore=[],
            strict=False,
            combine=False
        )

        # Convert to readable format
        if result['status'] == 'ok' and result['config']:
            result = ncp.create_readable_nginx_config(result)

        if result['status'] == 'ok':
            config = result['config']

            # Show structure overview
            print(f"Main sections: {list(config.keys())}")

            # Show events section
            if 'events' in config:
                print("\nEvents section:")
                for key, value in config['events'].items():
                    print(f"  {key}: {value}")

            # Show some HTTP directives
            if 'http' in config:
                print("\nHTTP section (sample):")
                http_config = config['http']
                count = 0
                for key, value in http_config.items():
                    if count < 5:  # Show first 5 directives
                        if isinstance(value, list):
                            print(f"  {key}: [list with {len(value)} items]")
                        else:
                            print(f"  {key}: {value}")
                        count += 1
                    else:
                        remaining = len(http_config) - count
                        print(f"  ... and {remaining} more directives")
                        break
        else:
            print(f"Parse failed: {result['errors']}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    # Run tests
    success = test_nginx_config_parser()

    # Show sample output if tests passed
    if success:
        show_sample_output()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
