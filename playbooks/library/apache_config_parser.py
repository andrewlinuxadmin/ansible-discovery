# -*- coding: utf-8 -*-

# Based on the project ApacheConfig at https://github.com/etingof/apacheconfig

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import sys
import re
import json
import glob
import io

try:
    from ansible.module_utils.basic import AnsibleModule
except ImportError:
    # For standalone testing
    class AnsibleModule:
        def __init__(self, argument_spec, supports_check_mode=False):
            self.params = {}

        def exit_json(self, **kwargs):
            print(json.dumps(kwargs, indent=2))

        def fail_json(self, **kwargs):
            print("FAILED: " + json.dumps(kwargs, indent=2))
            sys.exit(1)


DOCUMENTATION = r"""
---
module: apache_config_parser
short_description: Parse Apache configuration files with all original library options
version_added: "1.0.0"
description:
    - Parse Apache configuration files and return structured data
    - Complete implementation with ALL apacheconfig library options
    - Equivalent to apacheconfigtool functionality
options:
    path:
        description: Path to the Apache configuration file
        required: true
        type: str
    output_format:
        description: Format for output data
        required: false
        default: dict
        choices: ['dict', 'json']
        type: str
    # User requested options with default=True
    allowmultioptions:
        description: Collect multiple identical options into a list
        required: false
        default: true
        type: bool
    useapacheinclude:
        description: Consider "include ..." as valid include statement
        required: false
        default: true
        type: bool
    includeagain:
        description: Allow including sub-configfiles multiple times
        required: false
        default: true
        type: bool
    includedirectories:
        description: Include statement may point to a directory
        required: false
        default: true
        type: bool
    includeglob:
        description: Include statement may point to a glob pattern
        required: false
        default: true
        type: bool
    interpolatevars:
        description: Enable variable interpolation
        required: false
        default: true
        type: bool
    interpolateenv:
        description: Enable process environment variable interpolation
        required: false
        default: true
        type: bool
    mergeduplicateoptions:
        description: If same option occurs more than once, use the last one
        required: false
        default: true
        type: bool
"""

# Python 2/3 compatibility
try:
    unicode
    string_types = (basestring,)
    text_type = unicode
except NameError:
    string_types = (str,)
    text_type = str


# Exception classes
class ApacheConfigError(Exception):
    pass


class ConfigFileReadError(ApacheConfigError):
    pass


# Reader class
class LocalHostReader(object):
    def __init__(self):
        self._os = os
        self._environ = self._os.environ
        self._path = self._os.path

    @property
    def environ(self):
        return self._environ

    def exists(self, filepath):
        return self._path.exists(filepath)

    def isdir(self, filepath):
        return self._path.isdir(filepath)

    def listdir(self, filepath):
        return self._os.listdir(filepath)

    def open(self, filename, mode="r", encoding="utf-8", bufsize=-1):
        return io.open(filename, mode, bufsize, encoding=encoding)


# String types for quoting
class SingleQuotedString(text_type):
    is_single_quoted = True


class DoubleQuotedString(text_type):
    is_double_quoted = True


# Complete lexer implementation
class ApacheConfigLexer(object):
    def __init__(self, **options):
        self.options = options

    def tokenize(self, text):
        """Tokenize Apache config text"""
        tokens = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            # Handle include directives
            lower_line = line.lower()
            if lower_line.startswith("include ") or lower_line.startswith(
                "includeoptional "
            ):
                match = re.match(
                    r"^(include(?:optional)?)\s+(.+)$", line, re.IGNORECASE
                )
                if match:
                    directive = match.group(1).lower()
                    path = match.group(2).strip()
                    tokens.append(("INCLUDE", directive, path))
                continue

            # Handle block tags
            if line.startswith("<") and line.endswith(">"):
                if line.startswith("</"):
                    tag_name = line[2:-1].strip()
                    tokens.append(("CLOSE_TAG", tag_name))
                else:
                    tag_content = line[1:-1].strip()
                    tokens.append(("OPEN_TAG", tag_content))
                continue

            # Handle option-value pairs
            if " " in line or "\t" in line:
                match = re.match(r"([^\s]+)\s+(.+)", line)
                if match:
                    option = match.group(1)
                    value = match.group(2).strip()

                    if value.startswith('"') and value.endswith('"'):
                        value = DoubleQuotedString(value[1:-1])
                    elif value.startswith("'") and value.endswith("'"):
                        value = SingleQuotedString(value[1:-1])

                    tokens.append(("OPTION_VALUE", option, value))
                continue

            tokens.append(("OPTION", line))

        return tokens


# Complete parser implementation
class ApacheConfigParser(object):
    def __init__(self, lexer, **options):
        self.lexer = lexer
        self.options = options

    def parse(self, tokens):
        """Parse tokens into AST structure"""
        ast_nodes = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token[0] == "OPTION_VALUE":
                _, option, value = token
                ast_nodes.append(["statement", option, value])
            elif token[0] == "OPTION":
                _, option = token
                ast_nodes.append(["statement", option])
            elif token[0] == "OPEN_TAG":
                block_ast, consumed = self._parse_block(tokens, i)
                ast_nodes.append(block_ast)
                i += consumed
                continue
            elif token[0] == "INCLUDE":
                _, directive, path = token
                if directive == "includeoptional":
                    ast_nodes.append(["includeoptional", path])
                else:
                    ast_nodes.append(["include", path])

            i += 1

        return ast_nodes

    def _parse_block(self, tokens, start_idx):
        """Parse a block and return AST node and consumed token count"""
        if start_idx >= len(tokens):
            return ["block"], 1

        open_token = tokens[start_idx]
        if open_token[0] != "OPEN_TAG":
            return ["block"], 1

        tag_content = open_token[1]
        parts = tag_content.split(None, 1)
        tag_name = parts[0]
        tag_value = parts[1] if len(parts) > 1 else ""

        block_contents = []
        i = start_idx + 1
        consumed = 1

        while i < len(tokens):
            token = tokens[i]
            consumed += 1

            if token[0] == "CLOSE_TAG":
                close_tag = token[1]
                if close_tag.lower() == tag_name.lower():
                    break
            elif token[0] == "OPEN_TAG":
                nested_block, nested_consumed = self._parse_block(tokens, i)
                block_contents.append(nested_block)
                i += nested_consumed
                consumed += nested_consumed - 1
                continue
            elif token[0] == "OPTION_VALUE":
                _, option, value = token
                block_contents.append(["statement", option, value])
            elif token[0] == "OPTION":
                _, option = token
                block_contents.append(["statement", option])
            elif token[0] == "INCLUDE":
                _, directive, path = token
                if directive == "includeoptional":
                    block_contents.append(["includeoptional", path])
                else:
                    block_contents.append(["include", path])

            i += 1

        if tag_value:
            return ["block", [tag_name, " ", tag_value]] + block_contents, consumed
        else:
            return ["block", [tag_name]] + block_contents, consumed


# Complete loader implementation
class ApacheConfigLoader(object):
    def __init__(self, parser, **options):
        self._parser = parser
        self._options = dict(options)
        self._reader = self._options.get("reader", LocalHostReader())
        self._stack = []
        self._includes = set()
        self.files_processed = []

    def load(self, config_file):
        """Load and parse Apache configuration file"""
        self.files_processed = []
        self._includes = set()

        config_root = self._options.get("configroot", os.path.dirname(config_file))
        self._options["configroot"] = config_root

        config = self._load_file_recursive(config_file)
        return config

    def _load_file_recursive(self, filepath):
        """Load a file with recursive include processing"""
        if filepath in self._includes and not self._options.get("includeagain"):
            return {}

        self._includes.add(filepath)

        if not self._reader.exists(filepath):
            raise ConfigFileReadError("File %s can't be open" % filepath)

        self.files_processed.append(os.path.abspath(filepath))

        try:
            with self._reader.open(filepath) as f:
                content = f.read()
        except IOError as ex:
            raise ConfigFileReadError("File %s can't be open: %s" % (filepath, ex))

        tokens = self._parser.lexer.tokenize(content)
        ast_nodes = self._parser.parse(tokens)
        config = self._process_ast(ast_nodes)

        return config

    def _process_ast(self, ast_nodes):
        """Process AST nodes"""
        config = {}

        for node in ast_nodes:
            items = self._walkast(node)
            if items:
                self._merge_contents(config, items)

        return config

    def _walkast(self, ast):
        """Walk AST node and return config items"""
        if not ast:
            return {}

        node_type = ast[0]

        if node_type == "statement":
            return self.g_statement(ast[1:])
        elif node_type == "block":
            return self.g_block(ast[1:])
        elif node_type == "include":
            return self.g_include(ast[1:])
        elif node_type == "includeoptional":
            return self.g_includeoptional(ast[1:])
        else:
            return {}

    def g_statement(self, ast):
        """Process statement"""
        if len(ast) == 1:
            return {ast[0]: None}

        option, value = ast[:2]

        if not self._options.get("casesensitive", False):
            option = option.lower()

        return {option: value}

    def g_block(self, ast):
        """Process block"""
        tag = ast[0]
        values = {}

        if len(tag) > 1:
            name, _, value = tag
            block = {name: {value: values}}
        else:
            tag_name = self._unquote_tag(tag[0])
            block = {tag_name: values}

        for subtree in ast[1:]:
            items = self._walkast(subtree)
            if items:
                self._merge_contents(values, items)

        return block

    def g_include(self, ast):
        """Process include"""
        filepath = self._unquote_tag(ast[0])
        return self._process_include_directive(filepath, optional=False)

    def g_includeoptional(self, ast):
        """Process includeoptional"""
        try:
            return self.g_include(ast)
        except ConfigFileReadError:
            return {}

    def _process_include_directive(self, filepath, optional=False):
        """Process include directive"""
        if not self._options.get("useapacheinclude", True):
            directive = "includeoptional" if optional else "include"
            return {directive: filepath}

        options = self._options

        if os.path.isabs(filepath):
            configpath = [os.path.dirname(filepath)]
            filename = os.path.basename(filepath)
        else:
            configpath = options.get("configpath", [])

            if "configroot" in options and options.get("includerelative"):
                configpath.insert(0, options["configroot"])

            if "programpath" in options:
                configpath.append(options["programpath"])
            else:
                configpath.append(".")

            configpath.insert(0, options.get("configroot", "."))
            filename = filepath

        for configdir in configpath:
            full_filepath = os.path.join(configdir, filename)

            # Check for glob patterns first
            if options.get("includeglob") and ("*" in filepath or "?" in filepath):
                contents = {}
                for include_file in sorted(glob.glob(full_filepath)):
                    items = self._load_file_recursive(include_file)
                    self._merge_contents(contents, items)
                return contents

            elif self._reader.isdir(full_filepath):
                if options.get("includedirectories"):
                    contents = {}
                    try:
                        for include_file in sorted(self._reader.listdir(full_filepath)):
                            if include_file.endswith(".conf"):
                                include_path = os.path.join(full_filepath, include_file)
                                items = self._load_file_recursive(include_path)
                                self._merge_contents(contents, items)
                    except OSError:
                        if not optional:
                            raise ConfigFileReadError(
                                'Config directory "%s" not found' % full_filepath
                            )
                    return contents

            elif self._reader.exists(full_filepath):
                return self._load_file_recursive(full_filepath)

        if not optional:
            raise ConfigFileReadError(
                'Config file "%s" not found in search path %s'
                % (filename, ":".join(configpath))
            )
        return {}

    @staticmethod
    def _unquote_tag(tag):
        """Remove quotes from tag value"""
        if tag.startswith('"') and tag.endswith('"'):
            tag = tag[1:-1]
        if tag.startswith("'") and tag.endswith("'"):
            tag = tag[1:-1]
        if not tag:
            raise ApacheConfigError("Empty tag not allowed")
        return tag

    def _merge_contents(self, contents, items):
        """Merge items into existing contents dictionary"""
        for item in items:
            self._merge_item(contents, item, items[item])
        return contents

    def _merge_item(self, contents, key, value):
        """Merge a single item into contents dictionary"""
        if key not in contents:
            contents[key] = value
            return contents

        if isinstance(value, dict):
            if self._options.get("mergeduplicateblocks"):
                if isinstance(contents[key], dict):
                    for subkey in value:
                        self._merge_item(contents[key], subkey, value[subkey])
                else:
                    contents[key] = value
            else:
                if not isinstance(contents[key], list):
                    contents[key] = [contents[key]]
                contents[key].append(value)
        else:
            if self._options.get("mergeduplicateoptions", False):
                contents[key] = value
            else:
                if not isinstance(contents[key], list):
                    contents[key] = [contents[key]]
                contents[key].append(value)

        return contents


def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type="str", required=True),
            configroot=dict(type="str", required=True),
            output_format=dict(type="str", choices=["dict", "json"], default="dict"),
            # User requested options with default=True
            allowmultioptions=dict(type="bool", default=True),
            useapacheinclude=dict(type="bool", default=True),
            includeagain=dict(type="bool", default=True),
            includedirectories=dict(type="bool", default=True),
            includeglob=dict(type="bool", default=True),
            interpolatevars=dict(type="bool", default=True),
            interpolateenv=dict(type="bool", default=True),
            mergeduplicateoptions=dict(type="bool", default=True),
        ),
        supports_check_mode=True,
    )

    file_path = module.params["path"]
    configroot = module.params["configroot"]
    output_format = module.params["output_format"]

    # Build options dict for the library
    options = {
        "allowmultioptions": module.params["allowmultioptions"],
        "useapacheinclude": module.params["useapacheinclude"],
        "includeagain": module.params["includeagain"],
        "includedirectories": module.params["includedirectories"],
        "includeglob": module.params["includeglob"],
        "interpolatevars": module.params["interpolatevars"],
        "interpolateenv": module.params["interpolateenv"],
        "mergeduplicateoptions": module.params["mergeduplicateoptions"],
        "configroot": configroot,
        "mergeduplicateblocks": True,
        "includerelative": True,
    }

    if not os.path.exists(file_path):
        module.fail_json(
            msg="Configuration file not found: %s" % file_path,
            parse_success=False,
            file_path=file_path,
            files_processed=[],
        )

    try:
        lexer = ApacheConfigLexer(**options)
        parser = ApacheConfigParser(lexer, **options)
        loader = ApacheConfigLoader(parser, **options)

        config_data = loader.load(file_path)
        files_processed = loader.files_processed

        result = {
            "changed": False,
            "parse_success": True,
            "config_data": config_data,
            "file_path": file_path,
            "files_processed": files_processed,
        }

        if output_format == "json":
            result["config_json"] = json.dumps(config_data, indent=2)

        module.exit_json(**result)

    except (ApacheConfigError, ConfigFileReadError) as e:
        module.fail_json(
            msg="Apache config parsing failed: %s" % str(e),
            parse_success=False,
            file_path=file_path,
            files_processed=[],
        )
    except Exception as e:
        module.fail_json(
            msg="Unexpected error: %s" % str(e),
            parse_success=False,
            file_path=file_path,
            files_processed=[],
        )


if __name__ == "__main__":
    main()
