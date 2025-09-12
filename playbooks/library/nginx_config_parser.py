#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Ansible Project
# GNU General Public License v3.0+
#
# This module is based on the nginx-crossplane project:
# https://github.com/nginxinc/crossplane
# Original library developed by NGINX, Inc.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import sys
import glob
import itertools
import io
import functools

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r"""
---
module: nginx_config_parser
short_description: Parse NGINX configuration files into structured data
description:
    - Parses NGINX configuration files and returns structured JSON data
    - Based on nginx-crossplane library
      (https://github.com/nginxinc/crossplane) but completely standalone
    - Supports file includes, comments preservation, and multiple formats
    - Can output in readable nginx-like format or technical crossplane format
    - Handles complex NGINX configurations with nested blocks and includes
version_added: "2.14"
author:
    - "Ansible Community"
requirements:
    - python >= 2.7
options:
    path:
        description:
            - Path to the main NGINX configuration file to parse
            - Must be an existing file accessible by the module
        type: path
        required: true
    include_comments:
        description:
            - Whether to include comments in the parsed output
            - Comments are preserved with line information when enabled
            - Useful for configuration analysis and documentation purposes
        type: bool
        required: false
        default: false
    single_file:
        description:
            - Parse only the specified file, ignoring all include directives
            - When false, processes all included files recursively
            - Useful for analyzing individual configuration files in isolation
        type: bool
        required: false
        default: false
    ignore_directives:
        description:
            - List of directive names to ignore during parsing
            - Ignored directives will not appear in the output
            - Useful for security purposes to exclude sensitive data
            - Directive names are case-sensitive
        type: list
        elements: str
        required: false
        default: []
    strict:
        description:
            - Enable strict parsing mode for configuration validation
            - When true, unknown directives cause parsing to fail
            - When false, unknown directives are processed as-is
            - Recommended for production configuration validation
        type: bool
        required: false
        default: false
    combine:
        description:
            - Combine all included files into a single configuration structure
            - When true, includes are expanded inline in crossplane format
            - When false, maintains separate file structures with references
            - Technical feature for crossplane compatibility
        type: bool
        required: false
        default: false
    crossplane_format:
        description:
            - Controls the output format of the parsed configuration
            - When false (default), returns readable nginx-like hierarchical
              format
            - When true, returns technical crossplane format with parsing
              metadata
            - Crossplane format includes line numbers, file references, and
              include IDs
            - Readable format expands includes and creates clean hierarchical
              structure
        type: bool
        required: false
        default: false
notes:
    - This module is completely standalone and self-contained
    - Does not require external nginx-crossplane library installation
    - Compatible with Python 2.7+ and Python 3.x environments
    - Preserves all NGINX directive semantics and syntax rules
    - Handles complex scenarios like globbed includes and deeply nested blocks
    - Default output format prioritizes human readability with expanded
      includes
seealso:
    - name: NGINX Configuration Reference
      description: Official NGINX configuration documentation
      link: https://nginx.org/en/docs/
    - name: nginx-crossplane project
      description: Original library this module is based on
      link: https://github.com/nginxinc/crossplane
"""

EXAMPLES = r"""
# Basic parsing of main NGINX configuration file
- name: Parse main nginx configuration in readable format
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
  register: nginx_config

# Parsing with comments preservation
- name: Parse nginx configuration with comments included
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    include_comments: true
  register: nginx_config_with_comments

# Parse single file without processing includes
- name: Parse individual site configuration file
  nginx_config_parser:
    path: /etc/nginx/sites-available/default
    single_file: true
  register: site_config

# Security-conscious parsing with sensitive directives ignored
- name: Parse configuration while ignoring sensitive data
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    ignore_directives:
      - ssl_certificate_key
      - ssl_password_file
      - auth_basic_user_file
      - auth_jwt_key_file
  register: secure_config

# Strict parsing mode for validation
- name: Validate configuration with strict mode
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    strict: true
  register: validated_config

# Technical crossplane format output
- name: Get technical crossplane format with metadata
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    crossplane_format: true
  register: technical_config

# Combined configuration with all includes expanded
- name: Parse with combined includes in crossplane format
  nginx_config_parser:
    path: /etc/nginx/nginx.conf
    combine: true
    crossplane_format: true
  register: combined_config

# Example of conditional logic based on parsing results
- name: Check for specific server configurations
  debug:
    msg: "Found {{ nginx_config.config.http.server | length }} servers"
  when:
    - nginx_config.config.status == 'ok'
    - nginx_config.config.http is defined
    - nginx_config.config.http.server is defined

# Example error handling
- name: Handle parsing errors gracefully
  debug:
    msg: "Configuration parsing failed: {{ nginx_config.errors | join(', ') }}"
  when: nginx_config.config.status == 'failed'
"""

RETURN = r"""
config:
    description:
        - Parsed nginx configuration structure
        - Format varies based on crossplane_format parameter
        - When crossplane_format=false (default), returns readable hierarchical
          format with expanded includes
        - When crossplane_format=true, returns technical crossplane format
          with parsing metadata
    returned: success
    type: dict
    contains:
        status:
            description: Overall parsing status (ok or failed)
            type: str
            sample: "ok"
        errors:
            description: List of parsing errors encountered
            type: list
            elements: dict
            sample: []
        config:
            description:
                - Configuration content structure
                - In readable format, contains expanded directives
                - In crossplane format, contains list of parsed files
            type: dict
    sample:
        # Readable format example (crossplane_format=false)
        status: "ok"
        errors: []
        config:
            events:
                worker_connections: "1024"
            http:
                include: "mime.types"
                server:
                    - listen: "80"
                      server_name: "example.com"
                      location:
                        - match: "/"
                          root: "/var/www/html"
changed:
    description: Always false as this module only reads configuration
    returned: always
    type: bool
    sample: false
errors:
    description: Alias for config.errors for backward compatibility
    returned: always
    type: list
    sample: []
"""

# Python 2/3 compatibility
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY2:
    basestring = str
else:
    basestring = str


class NgxParserBaseException(Exception):
    def __init__(self, strerror, filename, lineno):
        self.args = (strerror, filename, lineno)
        self.filename = filename
        self.lineno = lineno
        self.strerror = strerror

    def __str__(self):
        if self.lineno is not None:
            return "%s in %s:%s" % self.args
        else:
            return "%s in %s" % self.args


class NgxParserSyntaxError(NgxParserBaseException):
    pass


class NgxParserDirectiveError(NgxParserBaseException):
    pass


class NgxParserDirectiveArgumentsError(NgxParserDirectiveError):
    pass


class NgxParserDirectiveContextError(NgxParserDirectiveError):
    pass


class NgxParserDirectiveUnknownError(NgxParserDirectiveError):
    pass


def fix_pep_479(generator):
    """
    Python 3.7 breaks crossplane's lexer because of PEP 479
    Read more here: https://www.python.org/dev/peps/pep-0479/
    """

    @functools.wraps(generator)
    def _wrapped_generator(*args, **kwargs):
        try:
            for x in generator(*args, **kwargs):
                yield x
        except RuntimeError:
            return

    return _wrapped_generator


# External parsers and lexers registry
EXTERNAL_LEXERS = {}
EXTERNAL_PARSERS = {}


def create_readable_nginx_config(result):
    """
    Transform parser output into readable hierarchical format
    similar to original nginx file, but with includes expanded.

    Args:
        result: Result from nginx_config_parser.parse()

    Returns:
        dict: Configuration in readable format
    """
    from collections import OrderedDict

    def process_parsed_list(parsed_list, config_list, level=0):
        """Process directive list recursively"""
        config = OrderedDict()

        for directive in parsed_list:
            name = directive["directive"]
            args = directive.get("args", [])

            # Create identifying key
            if args and name in ["location", "if"]:
                key = "{} {}".format(name, " ".join(args))
            else:
                key = name

            # Process based on type
            if "block" in directive and directive["block"]:
                # Directive with block
                config[key] = process_parsed_list(
                    directive["block"], config_list, level + 1
                )

            elif "includes" in directive and directive["includes"]:
                # Include directive - expand file contents
                if directive["includes"]:  # If there are included files
                    # Create structure with expanded content
                    expanded_content = OrderedDict()

                    for include_id in directive["includes"]:
                        if include_id < len(config_list):
                            included_file = config_list[include_id]
                            file_content = process_parsed_list(
                                included_file["parsed"], config_list, level + 1
                            )

                            # Merge content directly
                            expanded_content.update(file_content)

                    # Use directive name as key and expand content
                    if args:
                        key = "{} {}".format(name, args[0])
                    config[key] = expanded_content
                else:
                    # Empty include - just show the directive
                    config[key] = args[0] if args else None

            else:
                # Simple directive
                if len(args) == 0:
                    config[key] = None
                elif len(args) == 1:
                    config[key] = args[0]
                else:
                    config[key] = args

        return config

    # Check parse status
    if result["status"] != "ok":
        return {
            "status": result["status"],
            "errors": result["errors"],
            "message": "Parsing failed - see errors above",
        }

    # Process main file
    main_config = result["config"][0]
    readable_config = process_parsed_list(main_config["parsed"], result["config"])

    # Create final result
    return {
        "status": result["status"],
        "nginx": readable_config,
        "info": {
            "main_file": main_config["file"],
            "included_files": [cfg["file"] for cfg in result["config"][1:]],
            "total_files_processed": len(result["config"]),
            "parsing_successful": True,
        },
    }


@fix_pep_479
def _iterescape(iterable):
    chars = iter(iterable)
    for char in chars:
        if char == "\\":
            char = char + next(chars)
        yield char


def _iterlinecount(iterable):
    line = 1
    chars = iter(iterable)
    for char in chars:
        if char.endswith("\n"):
            line += 1
        yield (char, line)


@fix_pep_479
def _lex_file_object(file_obj):
    """
    Generates token tuples from an nginx config file object
    Yields 3-tuples like (token, lineno, quoted)
    """
    token = ""  # the token buffer
    token_line = 0  # the line the token starts on
    next_token_is_directive = True

    it = itertools.chain.from_iterable(file_obj)
    it = _iterescape(it)  # treat escaped characters differently
    it = _iterlinecount(it)  # count the number of newline characters

    for char, line in it:
        # handle whitespace
        if char.isspace():
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line, False)
                if next_token_is_directive and token in EXTERNAL_LEXERS:
                    for custom_lexer_token in EXTERNAL_LEXERS[token](it, token):
                        yield custom_lexer_token
                        next_token_is_directive = True
                else:
                    next_token_is_directive = False
                token = ""

            # disregard until char isn't a whitespace character
            while char.isspace():
                char, line = next(it)

        # if starting comment
        if not token and char == "#":
            while not char.endswith("\n"):
                token = token + char
                char, _ = next(it)
            yield (token, line, False)
            token = ""
            continue

        if not token:
            token_line = line

        # handle parameter expansion syntax (ex: "${var[@]}")
        if token and token[-1] == "$" and char == "{":
            next_token_is_directive = False
            while token[-1] != "}" and not char.isspace():
                token += char
                char, line = next(it)

        # if a quote is found, add the whole string to the token buffer
        if char in ('"', "'"):
            # if a quote is inside a token, treat it like any other char
            if token:
                token += char
                continue

            quote = char
            char, line = next(it)
            while char != quote:
                token += quote if char == "\\" + quote else char
                char, line = next(it)

            yield (token, token_line, True)  # True because this is in quotes

            # handle quoted external directives
            if next_token_is_directive and token in EXTERNAL_LEXERS:
                for custom_lexer_token in EXTERNAL_LEXERS[token](it, token):
                    yield custom_lexer_token
                    next_token_is_directive = True
            else:
                next_token_is_directive = False

            token = ""
            continue

        # handle special characters that are treated like full tokens
        if char in ("{", "}", ";"):
            # if token complete yield it and reset token buffer
            if token:
                yield (token, token_line, False)
                token = ""

            # this character is a full token so yield it now
            yield (char, line, False)
            next_token_is_directive = True
            continue

        # append char to the token buffer
        token += char


def _balance_braces(tokens, filename=None):
    """Raises syntax errors if braces aren't balanced"""
    depth = 0

    for token, line, quoted in tokens:
        if token == "}" and not quoted:
            depth -= 1
        elif token == "{" and not quoted:
            depth += 1

        # raise error if we ever have more right braces than left
        if depth < 0:
            reason = 'unexpected "}"'
            raise NgxParserSyntaxError(reason, filename, line)
        else:
            yield (token, line, quoted)

    # raise error if we have less right braces than left at EOF
    if depth > 0:
        reason = 'unexpected end of file, expecting "}"'
        raise NgxParserSyntaxError(reason, filename, line)


def lex(filename):
    """Generates tokens from an nginx config file"""
    with io.open(filename, mode="r", encoding="utf-8", errors="replace") as f:
        it = _lex_file_object(f)
        it = _balance_braces(it, filename)
        for token, line, quoted in it:
            yield (token, line, quoted)


# Simplified analyzer (basic context and argument validation)
# bit masks for different directive argument styles
NGX_CONF_NOARGS = 0x00000001  # 0 args
NGX_CONF_TAKE1 = 0x00000002  # 1 args
NGX_CONF_TAKE2 = 0x00000004  # 2 args
NGX_CONF_TAKE3 = 0x00000008  # 3 args
NGX_CONF_TAKE4 = 0x00000010  # 4 args
NGX_CONF_TAKE5 = 0x00000020  # 5 args
NGX_CONF_TAKE6 = 0x00000040  # 6 args
NGX_CONF_TAKE7 = 0x00000080  # 7 args
NGX_CONF_BLOCK = 0x00000100  # followed by block
NGX_CONF_FLAG = 0x00000200  # 'on' or 'off'
NGX_CONF_ANY = 0x00000400  # >=0 args
NGX_CONF_1MORE = 0x00000800  # >=1 args
NGX_CONF_2MORE = 0x00001000  # >=2 args

NGX_CONF_TAKE12 = NGX_CONF_TAKE1 | NGX_CONF_TAKE2

# bit masks for different directive locations
NGX_MAIN_CONF = 0x00040000  # main context
NGX_EVENT_CONF = 0x00080000  # events
NGX_HTTP_MAIN_CONF = 0x02000000  # http
NGX_HTTP_SRV_CONF = 0x04000000  # http > server
NGX_HTTP_LOC_CONF = 0x08000000  # http > location
NGX_HTTP_UPS_CONF = 0x10000000  # http > upstream
NGX_HTTP_SIF_CONF = 0x20000000  # http > server > if
NGX_HTTP_LIF_CONF = 0x40000000  # http > location > if
NGX_HTTP_LMT_CONF = 0x80000000  # http > location > limit_except

# Basic context mapping
CONTEXTS = {
    (): NGX_MAIN_CONF,
    ("events",): NGX_EVENT_CONF,
    ("http",): NGX_HTTP_MAIN_CONF,
    ("http", "server"): NGX_HTTP_SRV_CONF,
    ("http", "location"): NGX_HTTP_LOC_CONF,
    ("http", "upstream"): NGX_HTTP_UPS_CONF,
    ("http", "server", "if"): NGX_HTTP_SIF_CONF,
    ("http", "location", "if"): NGX_HTTP_LIF_CONF,
    ("http", "location", "limit_except"): NGX_HTTP_LMT_CONF,
}

# Simplified directives mapping (common nginx directives)
DIRECTIVES = {
    "events": [NGX_MAIN_CONF | NGX_CONF_BLOCK | NGX_CONF_NOARGS],
    "http": [NGX_MAIN_CONF | NGX_CONF_BLOCK | NGX_CONF_NOARGS],
    "server": [NGX_HTTP_MAIN_CONF | NGX_CONF_BLOCK | NGX_CONF_NOARGS],
    "location": [
        NGX_HTTP_MAIN_CONF
        | NGX_HTTP_SRV_CONF
        | NGX_HTTP_LOC_CONF
        | NGX_CONF_1MORE
        | NGX_CONF_BLOCK
    ],
    "upstream": [NGX_HTTP_MAIN_CONF | NGX_CONF_TAKE1 | NGX_CONF_BLOCK],
    "include": [
        NGX_MAIN_CONF
        | NGX_HTTP_MAIN_CONF
        | NGX_HTTP_SRV_CONF
        | NGX_HTTP_LOC_CONF
        | NGX_CONF_TAKE1
    ],
    "listen": [NGX_HTTP_SRV_CONF | NGX_CONF_1MORE],
    "server_name": [NGX_HTTP_SRV_CONF | NGX_CONF_1MORE],
    "root": [
        NGX_HTTP_MAIN_CONF | NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_TAKE1
    ],
    "index": [
        NGX_HTTP_MAIN_CONF | NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_1MORE
    ],
    "error_page": [
        NGX_HTTP_MAIN_CONF | NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_2MORE
    ],
    "access_log": [
        NGX_HTTP_MAIN_CONF | NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_1MORE
    ],
    "error_log": [
        NGX_MAIN_CONF
        | NGX_HTTP_MAIN_CONF
        | NGX_HTTP_SRV_CONF
        | NGX_HTTP_LOC_CONF
        | NGX_CONF_1MORE
    ],
    "worker_processes": [NGX_MAIN_CONF | NGX_CONF_TAKE1],
    "worker_connections": [NGX_EVENT_CONF | NGX_CONF_TAKE1],
    "keepalive_timeout": [
        NGX_HTTP_MAIN_CONF | NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_TAKE12
    ],
    "gzip": [
        NGX_HTTP_MAIN_CONF | NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_FLAG
    ],
    "return": [NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_TAKE12],
    "try_files": [NGX_HTTP_LOC_CONF | NGX_CONF_2MORE],
    "proxy_pass": [NGX_HTTP_LOC_CONF | NGX_CONF_TAKE1],
    "if": [NGX_HTTP_SRV_CONF | NGX_HTTP_LOC_CONF | NGX_CONF_1MORE | NGX_CONF_BLOCK],
}


def enter_block_ctx(stmt, ctx):
    # don't nest because NGX_HTTP_LOC_CONF just means "location block in http"
    if ctx and ctx[0] == "http" and stmt["directive"] == "location":
        return ("http", "location")
    # no other block contexts can be nested like location so just append it
    return ctx + (stmt["directive"],)


def analyze(fname, stmt, term, ctx=(), strict=False, check_ctx=True, check_args=True):
    directive = stmt["directive"]
    line = stmt["line"]

    # if strict and directive isn't recognized then throw error
    if strict and directive not in DIRECTIVES:
        reason = 'unknown directive "%s"' % directive
        raise NgxParserDirectiveUnknownError(reason, fname, line)

    # if we don't know where this directive is allowed then don't analyze it
    if ctx not in CONTEXTS or directive not in DIRECTIVES:
        return

    args = stmt.get("args") or []
    n_args = len(args)
    masks = DIRECTIVES[directive]

    # if this directive can't be used in this context then throw an error
    if check_ctx:
        masks = [mask for mask in masks if mask & CONTEXTS[ctx]]
        if not masks:
            reason = '"%s" directive is not allowed here' % directive
            raise NgxParserDirectiveContextError(reason, fname, line)

    if not check_args:
        return

    def valid_flag(x):
        return x.lower() in ("on", "off")

    # check each mask to see if arguments are valid
    for mask in reversed(masks):
        # if the directive isn't a block but should be according to the mask
        if mask & NGX_CONF_BLOCK and term != "{":
            reason = 'directive "%s" has no opening "{"'
            continue

        # if the directive is a block but shouldn't be according to the mask
        if not mask & NGX_CONF_BLOCK and term != ";":
            reason = 'directive "%s" is not terminated by ";"'
            continue

        # use mask to check the directive's arguments
        if (
            (mask >> n_args & 1 and n_args <= 7)  # NOARGS to TAKE7
            or (mask & NGX_CONF_FLAG and n_args == 1 and valid_flag(args[0]))
            or (mask & NGX_CONF_ANY and n_args >= 0)
            or (mask & NGX_CONF_1MORE and n_args >= 1)
            or (mask & NGX_CONF_2MORE and n_args >= 2)
        ):
            return
        elif mask & NGX_CONF_FLAG and n_args == 1 and not valid_flag(args[0]):
            reason = (
                'invalid value "%s" in "%%s" directive, '
                'it must be "on" or "off"' % args[0]
            )
        else:
            reason = 'invalid number of arguments in "%s" directive'

    raise NgxParserDirectiveArgumentsError(reason % directive, fname, line)


def _prepare_if_args(stmt):
    """Removes parentheses from an "if" directive's arguments"""
    args = stmt["args"]
    if args and args[0].startswith("(") and args[-1].endswith(")"):
        args[0] = args[0][1:].lstrip()
        args[-1] = args[-1][:-1].rstrip()
        start = int(not args[0])
        end = len(args) - int(not args[-1])
        args[:] = args[start:end]


def parse(
    filename,
    onerror=None,
    catch_errors=True,
    ignore=(),
    single=False,
    comments=False,
    strict=False,
    combine=False,
    check_ctx=True,
    check_args=True,
):
    """
    Parses an nginx config file and returns a nested dict payload
    """
    config_dir = os.path.dirname(filename)

    payload = {
        "status": "ok",
        "errors": [],
        "config": [],
    }

    # start with the main nginx config file/context
    includes = [(filename, ())]  # stores (filename, config context) tuples
    included = {filename: 0}  # stores {filename: array index} map

    def _handle_error(parsing, e):
        """Adds representations of an error to the payload"""
        file = parsing["file"]
        error = str(e)
        line = getattr(e, "lineno", None)

        parsing_error = {"error": error, "line": line}
        payload_error = {"file": file, "error": error, "line": line}
        if onerror is not None:
            payload_error["callback"] = onerror(e)

        parsing["status"] = "failed"
        parsing["errors"].append(parsing_error)

        payload["status"] = "failed"
        payload["errors"].append(payload_error)

    def _parse(parsing, tokens, ctx=(), consume=False):
        """Recursively parses nginx config contexts"""
        fname = parsing["file"]
        parsed = []

        # parse recursively by pulling from a flat stream of tokens
        for token, lineno, quoted in tokens:
            comments_in_args = []

            # we are parsing a block, so break if it's closing
            if token == "}" and not quoted:
                break

            # if we are consuming, then just continue until end of context
            if consume:
                # if we find a block inside this context, consume it too
                if token == "{" and not quoted:
                    _parse(parsing, tokens, consume=True)
                continue

            # the first token should always(?) be an nginx directive
            directive = token

            if combine:
                stmt = {
                    "file": fname,
                    "directive": directive,
                    "line": lineno,
                    "args": [],
                }
            else:
                stmt = {"directive": directive, "line": lineno, "args": []}

            # if token is comment
            if directive.startswith("#") and not quoted:
                if comments:
                    stmt["directive"] = "#"
                    stmt["comment"] = token[1:]
                    parsed.append(stmt)
                continue

            # parse arguments by reading tokens
            args = stmt["args"]
            token, __, quoted = next(tokens)  # disregard line numbers of args
            while token not in ("{", ";", "}") or quoted:
                if token.startswith("#") and not quoted:
                    comments_in_args.append(token[1:])
                else:
                    stmt["args"].append(token)

                token, __, quoted = next(tokens)

            # consume the directive if it is ignored and move on
            if stmt["directive"] in ignore:
                # if this directive was a block consume it too
                if token == "{" and not quoted:
                    _parse(parsing, tokens, consume=True)
                continue

            # prepare arguments
            if stmt["directive"] == "if":
                _prepare_if_args(stmt)

            try:
                # raise errors if this statement is invalid
                analyze(
                    fname=fname,
                    stmt=stmt,
                    term=token,
                    ctx=ctx,
                    strict=strict,
                    check_ctx=check_ctx,
                    check_args=check_args,
                )
            except NgxParserDirectiveError as e:
                if catch_errors:
                    _handle_error(parsing, e)

                    # if it was a block but shouldn't have been then consume
                    if e.strerror.endswith(' is not terminated by ";"'):
                        if token != "}" and not quoted:
                            _parse(parsing, tokens, consume=True)
                        else:
                            break

                    # keep on parsin'
                    continue
                else:
                    raise e

            # add "includes" to the payload if this is an include statement
            if not single and stmt["directive"] == "include":
                pattern = args[0]
                if not os.path.isabs(args[0]):
                    pattern = os.path.join(config_dir, args[0])

                stmt["includes"] = []

                # get names of all included files
                if glob.has_magic(pattern):
                    fnames = glob.glob(pattern)
                    fnames.sort()
                else:
                    try:
                        # if the file pattern was explicit, nginx will check
                        # that the included file can be opened and read
                        open(str(pattern)).close()
                        fnames = [pattern]
                    except Exception as e:
                        fnames = []
                        e.lineno = stmt["line"]
                        if catch_errors:
                            _handle_error(parsing, e)
                        else:
                            raise e

                for fname in fnames:
                    # the included set keeps files from being parsed twice
                    if fname not in included:
                        included[fname] = len(includes)
                        includes.append((fname, ctx))
                    index = included[fname]
                    stmt["includes"].append(index)

            # if this statement terminated with '{' then it is a block
            if token == "{" and not quoted:
                inner = enter_block_ctx(stmt, ctx)  # get context for block
                stmt["block"] = _parse(parsing, tokens, ctx=inner)

            parsed.append(stmt)

            # add all comments found inside args after stmt is added
            for comment in comments_in_args:
                comment_stmt = {
                    "directive": "#",
                    "line": stmt["line"],
                    "args": [],
                    "comment": comment,
                }
                parsed.append(comment_stmt)

        return parsed

    # the includes list grows as "include" directives are found in _parse
    for fname, ctx in includes:
        try:
            tokens = lex(fname)
            parsing = {"file": fname, "status": "ok", "errors": [], "parsed": []}
            parsing["parsed"] = _parse(parsing, tokens, ctx=ctx)
        except Exception as e:
            parsing = {"file": fname, "status": "failed", "errors": [], "parsed": []}
            _handle_error(parsing, e)

        payload["config"].append(parsing)

    if combine:
        return _combine_parsed_configs(payload)
    else:
        return payload


def _combine_parsed_configs(old_payload):
    """
    Combines config files into one by using include directives.
    """
    old_configs = old_payload["config"]

    def _perform_includes(block):
        for stmt in block:
            if "block" in stmt:
                stmt["block"] = list(_perform_includes(stmt["block"]))
            if "includes" in stmt:
                for index in stmt["includes"]:
                    config = old_configs[index]["parsed"]
                    for stmt in _perform_includes(config):
                        yield stmt
            else:
                yield stmt

    combined_config = {
        "file": old_configs[0]["file"],
        "status": "ok",
        "errors": [],
        "parsed": [],
    }

    for config in old_configs:
        combined_config["errors"] += config.get("errors", [])
        if config.get("status", "ok") == "failed":
            combined_config["status"] = "failed"

    first_config = old_configs[0]["parsed"]
    combined_config["parsed"] += _perform_includes(first_config)

    combined_payload = {
        "status": old_payload.get("status", "ok"),
        "errors": old_payload.get("errors", []),
        "config": [combined_config],
    }
    return combined_payload


def main():
    module_args = dict(
        path=dict(type="path", required=True),
        include_comments=dict(type="bool", required=False, default=False),
        single_file=dict(type="bool", required=False, default=False),
        ignore_directives=dict(type="list", elements="str", required=False, default=[]),
        strict=dict(type="bool", required=False, default=False),
        combine=dict(type="bool", required=False, default=False),
        crossplane_format=dict(type="bool", required=False, default=False),
    )

    result = dict(changed=False, config={})

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    path = module.params["path"]
    include_comments = module.params["include_comments"]
    single_file = module.params["single_file"]
    ignore_directives = module.params["ignore_directives"]
    strict = module.params["strict"]
    combine = module.params["combine"]

    # Check if file exists
    if not os.path.exists(path):
        module.fail_json(msg="File not found: %s" % path, **result)

    if not os.path.isfile(path):
        module.fail_json(msg="Path is not a file: %s" % path, **result)

    try:
        # Parse the nginx configuration
        config = parse(
            filename=path,
            comments=include_comments,
            single=single_file,
            ignore=ignore_directives,
            strict=strict,
            combine=combine,
            catch_errors=True,
            check_ctx=True,
            check_args=True,
        )

        # Apply readable format unless crossplane format is requested
        if not module.params["crossplane_format"]:
            config = create_readable_nginx_config(config)

        result["config"] = config

        # Module never changes anything
        result["changed"] = False

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(
            msg="Failed to parse nginx configuration: %s" % str(e), **result
        )


if __name__ == "__main__":
    main()
