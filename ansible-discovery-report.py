#!/usr/bin/env python3
import json
import html as html_mod
import configparser
import argparse
from collections import Counter, defaultdict

VERSION = '6'

# ─── Parse arguments ─────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Ansible Discovery Report Generator')
parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
parser.add_argument('--config', default='ansible-discovery-report.ini', help='INI configuration file (default: ansible-discovery-report.ini)')
parser.add_argument('--input', dest='input_file', help='Input JSON file (overrides INI value)')
parser.add_argument('--output', dest='output_file', help='Output HTML file (overrides INI value)')
args = parser.parse_args()

# ─── Load configuration ──────────────────────────────────────────
cfg = configparser.ConfigParser(interpolation=None)
cfg.read(args.config, encoding='utf-8')

C = lambda section, key: cfg.get(section, key)
colors = lambda key: C('colors', key)
rep = lambda key: C('report', key)
sb = lambda key: C('sidebar', key)
nav = lambda key: C('nav', key)
hd = lambda key: C('headings', key)
th = lambda key: C('table_headers', key)
lb = lambda key: C('labels', key)
msg = lambda key: C('messages', key)
el = lambda key: C('eligibility', key)

INPUT_FILE = args.input_file or C('general', 'input_file')
OUTPUT_FILE = args.output_file or C('general', 'output_file')
LANG = C('general', 'lang')
LOCALE_SORT = C('general', 'locale_sort')
DATE_FORMAT = C('general', 'report_date')

PRIMARY = colors('primary')
SECONDARY = colors('secondary')
SIDEBAR_BG = colors('sidebar_bg')
SIDEBAR_ACTIVE_BG = colors('sidebar_active_bg')
SIDEBAR_ACTIVE_BORDER = colors('sidebar_active_border')

with open(INPUT_FILE) as f:
    raw = f.read().strip()
    if raw.startswith('['):
        records = json.loads(raw)
    else:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]

def clean_id(raw_id):
    if raw_id.startswith('ansible_facts'):
        return raw_id.replace('ansible_facts', '')
    return raw_id

def fmt_bytes(b):
    if b is None or b == 0:
        return f'0 {lb("bytes")}'
    for unit in [lb('bytes'), lb('kilobytes'), lb('megabytes'), lb('gigabytes'), lb('terabytes')]:
        if abs(b) < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} {lb("petabytes")}'

def pct_used(total, avail):
    if not total:
        return '0%'
    return f'{((total - avail) / total) * 100:.1f}%'

def esc(s):
    return html_mod.escape(str(s)) if s else ''

# ─── Parse all hosts ──────────────────────────────────────────────
hosts = []
for rec in records:
    raw_id = rec['_id']
    d = rec['data']
    vm = clean_id(raw_id)
    distro = d.get('ansible_distribution', '?')
    distro_ver = d.get('ansible_distribution_version', '?')
    distro_major = d.get('ansible_distribution_major_version', '?')
    kernel = d.get('ansible_kernel', '?')
    fqdn = d.get('ansible_fqdn', vm)
    hostname = d.get('ansible_hostname', vm)
    domain = d.get('ansible_domain', '')

    # Namespace: try multiple sources from the data
    namespace = ''
    group_names = d.get('group_names', [])
    if isinstance(group_names, list) and group_names:
        namespace = group_names[0]
    if not namespace:
        namespace = d.get('namespace', '') or d.get('inventory_group', '')
    if not namespace:
        custom_ns = d.get('ansible_local', {}).get('custom', {}).get('all', {}).get('namespace', '')
        if custom_ns:
            namespace = custom_ns
    if not namespace:
        namespace = '—'
    vcpus = d.get('ansible_processor_vcpus', '?')
    ram_mb = d.get('ansible_memtotal_mb', 0)
    swap_mb = d.get('ansible_swaptotal_mb', 0)
    arch = d.get('ansible_architecture', '?')
    product = d.get('ansible_product_name', '?')
    product_ver = d.get('ansible_product_version', '?')
    bios_ver = d.get('ansible_bios_version', '?')
    os_family = d.get('ansible_os_family', '?')
    pkg_mgr = d.get('ansible_pkg_mgr', '?')
    python_ver = d.get('ansible_python_version', '?')
    service_mgr = d.get('ansible_service_mgr', '?')
    uptime = d.get('ansible_uptime_seconds', 0)

    ipv4_all = d.get('ansible_all_ipv4_addresses', [])
    ipv6_all = d.get('ansible_all_ipv6_addresses', [])
    default_ipv4 = d.get('ansible_default_ipv4', {})
    interfaces = d.get('ansible_interfaces', [])

    devices = d.get('ansible_devices', {})
    mounts = d.get('ansible_mounts', [])
    lvm = d.get('ansible_lvm', {})

    processes = d.get('processes', [])
    tcp_listen = d.get('tcp_listen', [])
    udp_listen = d.get('udp_listen', [])
    services = d.get('services', {})

    custom = d.get('ansible_local', {}).get('custom', {}).get('all', {})
    installed_jboss = custom.get('installed_jboss', '')
    running_jboss = custom.get('running_jboss', '')
    port_80 = custom.get('port_80', '')
    port_8080 = custom.get('port_8080', '')

    has_java = d.get('has_java_processes', False)
    has_jboss_procs = d.get('has_jboss_processes', False)
    has_tomcat_procs = d.get('has_tomcat_processes', False)
    has_jar_procs = d.get('has_jar_processes', False)
    java_processes_detail = d.get('java_processes', [])

    pkgs = d.get('packages', {})
    java_pkgs = {k: v for k, v in pkgs.items() if any(w in k.lower() for w in ['java-', 'jdk', 'jre'])}
    java_version = ''
    for pk, pv in java_pkgs.items():
        if isinstance(pv, list) and pv:
            java_version = f'{pk} {pv[0].get("version", "")}'
            break

    apache_processes_detail = d.get('apache_processes', [])
    apache_has_php = d.get('apache_has_php', False)
    php_info = d.get('php_info', {})

    httpd_pkg = pkgs.get('httpd', [])
    httpd_ver = ''
    if httpd_pkg and isinstance(httpd_pkg, list):
        httpd_ver = f'{httpd_pkg[0].get("version","")}-{httpd_pkg[0].get("release","")}'

    nginx_pkgs_list = {k: v for k, v in pkgs.items() if 'nginx' in k.lower() and ('runtime' not in k.lower() and 'filesystem' not in k.lower())}
    nginx_ver = ''
    for nk, nv in nginx_pkgs_list.items():
        if isinstance(nv, list) and nv:
            nginx_ver = f'{nk} {nv[0].get("version","")}'
            break

    php_pkgs = {k: v for k, v in pkgs.items() if 'php' in k.lower() and k.lower().endswith('-php')}
    php_ver = ''
    for ppk, ppv in php_pkgs.items():
        if isinstance(ppv, list) and ppv:
            php_ver = f'{ppk} {ppv[0].get("version","")}'
            break

    memcached_pkg = pkgs.get('memcached', [])
    memcached_ver = ''
    if memcached_pkg and isinstance(memcached_pkg, list):
        memcached_ver = f'{memcached_pkg[0].get("version","")}'

    fw = d.get('firewall_info', {})
    se = d.get('selinux_info', {})

    app_type = []
    if running_jboss:
        app_type.append(f'JBoss ({running_jboss})')
    elif installed_jboss and has_java:
        app_type.append(f'JBoss ({installed_jboss})')
    elif has_java:
        app_type.append('Java Application')
    if port_80 == 'httpd' or httpd_ver:
        app_type.append('Apache HTTPD')
    if port_80 == 'nginx' or nginx_ver:
        app_type.append('Nginx')
    if port_80 in ('lighttpd',):
        app_type.append('Lighttpd')
    if port_80 == 'httpd.worker':
        app_type.append('Apache HTTPD (worker)')
    if php_ver:
        app_type.append('PHP')
    if memcached_ver:
        app_type.append('Memcached')
    if not app_type:
        app_type.append(msg('infra_other'))

    hosts.append({
        'vm': vm, 'raw_id': raw_id, 'namespace': namespace,
        'distro': distro, 'distro_ver': distro_ver,
        'distro_major': distro_major, 'kernel': kernel, 'fqdn': fqdn,
        'hostname': hostname, 'domain': domain, 'vcpus': vcpus, 'ram_mb': ram_mb,
        'swap_mb': swap_mb, 'arch': arch, 'product': product, 'product_ver': product_ver,
        'os_family': os_family, 'pkg_mgr': pkg_mgr, 'python_ver': python_ver,
        'service_mgr': service_mgr, 'uptime': uptime,
        'ipv4_all': ipv4_all, 'ipv6_all': ipv6_all, 'default_ipv4': default_ipv4,
        'interfaces': interfaces, 'devices': devices, 'mounts': mounts, 'lvm': lvm,
        'processes': processes, 'tcp_listen': tcp_listen, 'udp_listen': udp_listen,
        'services': services, 'custom': custom,
        'installed_jboss': installed_jboss, 'running_jboss': running_jboss,
        'port_80': port_80, 'port_8080': port_8080,
        'has_java': has_java, 'has_jboss_procs': has_jboss_procs,
        'has_tomcat_procs': has_tomcat_procs, 'has_jar_procs': has_jar_procs,
        'java_processes_detail': java_processes_detail,
        'java_version': java_version, 'java_pkgs': java_pkgs,
        'apache_processes_detail': apache_processes_detail,
        'apache_has_php': apache_has_php, 'php_info': php_info,
        'httpd_ver': httpd_ver, 'nginx_ver': nginx_ver, 'php_ver': php_ver,
        'memcached_ver': memcached_ver,
        'fw': fw, 'se': se, 'app_type': app_type,
        'pkgs': pkgs,
    })

hosts.sort(key=lambda h: h['vm'])

# Namespace is derived from export.json if available (group_names, custom fact, etc.)
# No hardcoded mapping — the script is fully data-driven.
has_namespace = any(h['namespace'] != '—' for h in hosts)

def ns_th():
    return f'<th>{esc(th("namespace"))}</th>' if has_namespace else ''

def ns_td(h):
    return f'<td>{esc(h["namespace"])}</td>' if has_namespace else ''

# ─── Upgrade eligibility ──────────────────────────────────────────
EL_COMPATIBLE_DISTROS = {'OracleLinux', 'CentOS', 'AlmaLinux', 'Rocky', 'CentOS Stream'}

def _check_app_blockers(h):
    """Check application-level blockers and warnings for RHEL 8 upgrade."""
    installed = h.get('installed_jboss', '')
    running = h.get('running_jboss', '')
    blockers = []
    warnings = []

    if 'jboss-eap-4.3' in installed or '4.3.0' in running:
        blockers.append(el('jboss43_incompatible'))
    if 'jboss-eap-6' in installed or 'EAP 6' in running:
        warnings.append(el('jboss6_eol'))
    if 'jboss-eap-7.0' in installed or 'EAP 7.0' in running:
        warnings.append(el('jboss70_upgrade'))
    if h['php_ver'] and '5.6' in h['php_ver']:
        warnings.append(el('php56_unsupported'))
    if h.get('memcached_ver'):
        warnings.append(el('memcached_upgrade'))

    return blockers, warnings

def upgrade_analysis(h):
    distro = h['distro']
    major = h['distro_major']
    is_rhel = distro == 'RedHat'
    is_el = distro in EL_COMPATIBLE_DISTROS

    try:
        major_int = int(major)
    except (ValueError, TypeError):
        return False, el('status_not_analyzed'), [el('out_of_scope')], []

    if major_int <= 6:
        return False, el('status_not_eligible'), [el('el6_eol')], []

    if is_rhel and major_int >= 8:
        return True, el('status_already_rhel8'), [], [el('check_rhel8_latest')]

    if is_el and major_int >= 8:
        return True, el('status_eligible_convert_direct'), [], [el('convert2rhel_direct')]

    if major_int == 7:
        blockers, warnings = _check_app_blockers(h)
        eligible = len(blockers) == 0

        if is_rhel:
            if not eligible:
                status = el('status_not_eligible')
            elif warnings:
                status = el('status_eligible_caveats_leapp')
            else:
                status = el('status_eligible_leapp')
        else:
            if not eligible:
                status = el('status_not_eligible')
            elif warnings:
                status = el('status_eligible_caveats_convert')
            else:
                status = el('status_eligible_convert')

        return eligible, status, blockers, warnings

    return False, el('status_not_analyzed'), [el('out_of_scope')], []


# ─── Build HTML ──────────────────────────────────────────────────
html_parts = []
html_parts.append(f'''<!DOCTYPE html>
<html lang="{LANG}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(rep('html_title'))}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Red Hat Display', 'Segoe UI', Arial, sans-serif; background: #f5f5f5; color: #333; line-height: 1.5; }}

  .sidebar {{ position: fixed; top: 0; left: 0; width: 260px; height: 100vh; background: {SIDEBAR_BG}; color: #ccc; overflow-y: auto; z-index: 100; padding: 15px 0; transition: transform 0.3s ease; }}
  .sidebar.collapsed {{ transform: translateX(-260px); }}
  .sidebar-toggle {{ position: fixed; top: 12px; left: 270px; z-index: 101; background: {SIDEBAR_BG}; color: #ccc; border: none; border-radius: 4px; width: 36px; height: 36px; font-size: 22px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: left 0.3s ease, background 0.2s; box-shadow: 0 1px 4px rgba(0,0,0,0.2); }}
  .sidebar-toggle:hover {{ background: {SIDEBAR_ACTIVE_BG}; color: #fff; }}
  .sidebar-toggle.collapsed {{ left: 10px; }}
  .sidebar-logo {{ text-align: center; padding: 10px 20px 15px; border-bottom: 1px solid #333; }}
  .sidebar-logo svg {{ width: 120px; height: auto; }}
  .sidebar-search {{ padding: 10px 15px; }}
  .sidebar-search input {{ width: 100%; padding: 7px 10px; border: 1px solid #444; border-radius: 4px; background: #2a2a2a; color: #eee; font-size: 12px; outline: none; }}
  .sidebar-search input:focus {{ border-color: #888; }}
  .sidebar-section {{ padding: 8px 15px 4px; font-size: 10px; text-transform: uppercase; color: #888; letter-spacing: 1px; margin-top: 8px; }}
  .sidebar a {{ display: block; padding: 5px 15px 5px 20px; color: #bbb; text-decoration: none; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: all 0.15s; }}
  .sidebar a:hover {{ color: #fff; background: #333; }}
  .sidebar a.active {{ color: #fff; background: {SIDEBAR_ACTIVE_BG}; border-left: 3px solid {SIDEBAR_ACTIVE_BORDER}; padding-left: 17px; }}
  .sidebar a.s-section {{ font-weight: 600; color: #eee; font-size: 13px; padding: 8px 15px; }}
  .sidebar a.s-sub {{ padding-left: 30px; font-size: 11px; color: #999; }}
  .sidebar a.s-host {{ padding-left: 25px; }}
  .sidebar .hidden {{ display: none; }}

  .main {{ margin-left: 260px; transition: margin-left 0.3s ease; }}
  .main.expanded {{ margin-left: 0; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 20px 30px; }}
  .header {{ background: {PRIMARY}; color: white; padding: 25px 40px; margin-bottom: 30px; border-radius: 8px; display: flex; align-items: center; gap: 30px; }}
  .header-logo {{ display: none; }}
  .header-text {{ flex: 1; }}
  .header h1 {{ font-size: 26px; margin-bottom: 5px; }}
  .header p {{ opacity: 0.9; font-size: 14px; }}
  h2 {{ color: {PRIMARY}; font-size: 22px; margin: 30px 0 15px 0; padding-bottom: 8px; border-bottom: 3px solid {PRIMARY}; }}
  h3 {{ color: {SECONDARY}; font-size: 18px; margin: 25px 0 10px 0; }}
  h4 {{ color: {SECONDARY}; font-size: 15px; margin: 15px 0 8px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 13px; background: white; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background: {PRIMARY}; color: white; padding: 10px 12px; text-align: left; font-weight: 600; white-space: nowrap; }}
  td {{ padding: 8px 12px; border-bottom: 1px solid #eee; vertical-align: top; }}
  tr:hover td {{ background: {colors('table_hover_bg')}; }}
  .card {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  .card-header {{ background: {PRIMARY}; color: white; padding: 12px 20px; margin: -20px -20px 15px -20px; border-radius: 8px 8px 0 0; }}
  .card-header h3 {{ color: white; margin: 0; }}
  .badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
  .badge-green {{ background: {colors('badge_green_bg')}; color: {colors('badge_green_fg')}; }}
  .badge-yellow {{ background: {colors('badge_yellow_bg')}; color: {colors('badge_yellow_fg')}; }}
  .badge-red {{ background: {colors('badge_red_bg')}; color: {colors('badge_red_fg')}; }}
  .badge-blue {{ background: {colors('badge_blue_bg')}; color: {colors('badge_blue_fg')}; }}
  .badge-grey {{ background: {colors('badge_grey_bg')}; color: {colors('badge_grey_fg')}; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px; }}
  .grid-item label {{ font-weight: 600; color: #666; font-size: 11px; text-transform: uppercase; }}
  .grid-item span {{ display: block; font-size: 14px; }}
  .eligible {{ color: {colors('eligible_color')}; font-weight: 600; }}
  .not-eligible {{ color: {colors('not_eligible_color')}; font-weight: 600; }}
  .with-caveats {{ color: {colors('caveats_color')}; font-weight: 600; }}
  .small {{ font-size: 11px; color: #888; }}
  th {{ position: relative; }}
  th .resizer {{ position: absolute; top: 0; right: 0; width: 5px; height: 100%; cursor: col-resize; user-select: none; }}
  th .resizer:hover, th .resizer.resizing {{ border-right: 2px solid rgba(255,255,255,0.6); }}
  th.sortable {{ cursor: pointer; user-select: none; padding-right: 20px; }}
  th.sortable:hover {{ background: {colors('sortable_hover_bg')}; }}
  th.sortable::after {{ content: '⇅'; position: absolute; right: 8px; top: 50%; transform: translateY(-50%); opacity: 0.5; font-size: 11px; }}
  th.sortable.asc::after {{ content: '▲'; opacity: 1; }}
  th.sortable.desc::after {{ content: '▼'; opacity: 1; }}
  table {{ table-layout: auto; }}
  .back-top {{ position: fixed; bottom: 20px; right: 20px; background: {PRIMARY}; color: white; border: none; padding: 10px 15px; border-radius: 50%; cursor: pointer; font-size: 18px; text-decoration: none; box-shadow: 0 2px 5px rgba(0,0,0,0.3); z-index: 50; }}
  @media print {{ .sidebar, .sidebar-toggle {{ display: none; }} .main {{ margin-left: 0; }} body {{ background: white; }} .card {{ box-shadow: none; border: 1px solid #ddd; }} .header-logo {{ display: block; }} }}
</style>
</head>
<body>
<nav class="sidebar" id="sidebar">
  <div class="sidebar-logo">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 388 250"><defs><style>.rhl2{{fill:#fff;}}</style></defs><path class="rhl2" d="M225.8,83.49c12.51,0,30.62-2.62,30.6-17.5a14,14,0,0,0-.31-3.42l-7.48-32.36c-1.73-7.12-3.25-10.35-15.76-16.59C223.14,8.67,202,.49,195.75.5c-5.82,0-7.54,7.55-14.44,7.56-6.68,0-11.65-5.6-17.9-5.59-6,0-9.92,4.11-12.93,12.52,0,0-8.39,23.72-9.46,27.17a6.15,6.15,0,0,0-.22,2c0,9.22,36.34,39.42,85,39.38M258.35,72c1.73,8.19,1.73,9.06,1.73,10.13,0,14-15.72,21.8-36.42,21.82-46.79,0-87.78-27.31-87.8-45.42a18.46,18.46,0,0,1,1.5-7.33c-16.82.87-38.59,3.91-38.58,23.1,0,31.48,74.68,70.23,133.76,70.18,45.28,0,56.69-20.54,56.68-36.71,0-12.73-11-27.16-30.87-35.77"/><path class="rhl2" d="M354.56,231.52c0,11.88,7.15,17.66,20.19,17.66a52,52,0,0,0,11.89-1.68V233.72a24.55,24.55,0,0,1-7.68,1.16c-5.37,0-7.36-1.68-7.36-6.73V207h15.56v-14.2H371.6v-18l-17,3.68v14.3H343.31V207h11.25Zm-52.94.31c0-3.68,3.68-5.47,9.25-5.47a43.12,43.12,0,0,1,10.1,1.26v7.16a21.62,21.62,0,0,1-10.63,2.63c-5.46,0-8.72-2.11-8.72-5.58m5.19,17.56c6,0,10.84-1.26,15.36-4.31v3.37H339V212.8c0-13.57-9.15-21-24.4-21-8.52,0-16.94,2-26,6.1l6.1,12.52c6.52-2.74,12-4.42,16.83-4.42,7,0,10.62,2.73,10.62,8.31V217a49.48,49.48,0,0,0-12.62-1.57c-14.3,0-22.93,6-22.93,16.72,0,9.78,7.78,17.24,20.19,17.24m-92.44-.94h18.09V219.63h30.29v28.82h18.09V174.83H262.75v28.29H232.46V174.83H214.37Zm-68.93-27.87c0-8,6.31-14.09,14.62-14.09a17.22,17.22,0,0,1,11.78,4.31v19.45a16.36,16.36,0,0,1-11.78,4.42c-8.2,0-14.62-6.1-14.62-14.09m26.61,27.87h16.83v-77.3l-17,3.68v20.93a28.27,28.27,0,0,0-14.2-3.68c-16.19,0-28.92,12.51-28.92,28.5a28.26,28.26,0,0,0,28.4,28.6,25.12,25.12,0,0,0,14.93-4.83Zm-77.19-42.7c5.36,0,9.88,3.47,11.67,8.83H83.29c1.68-5.57,5.89-8.83,11.57-8.83M66.15,220.68c0,16.2,13.25,28.82,30.29,28.82,9.36,0,16.19-2.52,23.24-8.41l-11.26-10c-2.62,2.73-6.52,4.2-11.14,4.2a14.39,14.39,0,0,1-13.68-8.83h39.65v-4.21c0-17.67-11.88-30.39-28.08-30.39a28.57,28.57,0,0,0-29,28.81M36.81,190.29c6,0,9.36,3.79,9.36,8.31s-3.37,8.31-9.36,8.31H18.93V190.29Zm-36,58.16H18.93V221.63H32.7l13.89,26.82H66.78L50.58,219a22.27,22.27,0,0,0,13.89-20.72c0-13.25-10.42-23.45-26-23.45H.84Z"/></svg>
  </div>
  <div class="sidebar-search">
    <input type="text" id="sidebarFilter" placeholder="{esc(sb('filter_placeholder'))}" autocomplete="off">
  </div>
  <div class="sidebar-section">{esc(sb('section_overview'))}</div>
  <a href="#overview" class="s-section">{esc(nav('overview'))}</a>
  <a href="#sec-1-1" class="s-sub">{esc(nav('sec_1_1'))}</a>
  <a href="#sec-1-2" class="s-sub">{esc(nav('sec_1_2'))}</a>
  <a href="#sec-1-2-1" class="s-sub">{esc(nav('sec_1_2_1'))}</a>
  <a href="#sec-1-2-2" class="s-sub">{esc(nav('sec_1_2_2'))}</a>
  {'<a href="#sec-1-3" class="s-sub">' + esc(nav('sec_1_3')) + '</a>' if has_namespace else ''}
  <a href="#conclusion" class="s-sub">{esc(nav('sec_1_4'))}</a>
  <div class="sidebar-section">{esc(sb('section_inventory'))}</div>
  <a href="#inventory" class="s-section">{esc(nav('inventory'))}</a>
  <div class="sidebar-section">{esc(sb('section_servers'))}</div>
''')

for h in hosts:
    html_parts.append(f'  <a href="#host-{h["vm"]}" class="s-host" data-vm="{h["vm"]}">{esc(h["vm"])}</a>')

html_parts.append(f'''
</nav>
<button class="sidebar-toggle" id="sidebarToggle" title="{esc(sb('toggle_title'))}">&#9776;</button>
<div class="main" id="mainContent">
<div class="container">
<div class="header">
  <div class="header-logo">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 388 250"><defs><style>.rhl{{fill:#fff;}}</style></defs><path class="rhl" d="M225.8,83.49c12.51,0,30.62-2.62,30.6-17.5a14,14,0,0,0-.31-3.42l-7.48-32.36c-1.73-7.12-3.25-10.35-15.76-16.59C223.14,8.67,202,.49,195.75.5c-5.82,0-7.54,7.55-14.44,7.56-6.68,0-11.65-5.6-17.9-5.59-6,0-9.92,4.11-12.93,12.52,0,0-8.39,23.72-9.46,27.17a6.15,6.15,0,0,0-.22,2c0,9.22,36.34,39.42,85,39.38M258.35,72c1.73,8.19,1.73,9.06,1.73,10.13,0,14-15.72,21.8-36.42,21.82-46.79,0-87.78-27.31-87.8-45.42a18.46,18.46,0,0,1,1.5-7.33c-16.82.87-38.59,3.91-38.58,23.1,0,31.48,74.68,70.23,133.76,70.18,45.28,0,56.69-20.54,56.68-36.71,0-12.73-11-27.16-30.87-35.77"/><path class="rhl" d="M354.56,231.52c0,11.88,7.15,17.66,20.19,17.66a52,52,0,0,0,11.89-1.68V233.72a24.55,24.55,0,0,1-7.68,1.16c-5.37,0-7.36-1.68-7.36-6.73V207h15.56v-14.2H371.6v-18l-17,3.68v14.3H343.31V207h11.25Zm-52.94.31c0-3.68,3.68-5.47,9.25-5.47a43.12,43.12,0,0,1,10.1,1.26v7.16a21.62,21.62,0,0,1-10.63,2.63c-5.46,0-8.72-2.11-8.72-5.58m5.19,17.56c6,0,10.84-1.26,15.36-4.31v3.37H339V212.8c0-13.57-9.15-21-24.4-21-8.52,0-16.94,2-26,6.1l6.1,12.52c6.52-2.74,12-4.42,16.83-4.42,7,0,10.62,2.73,10.62,8.31V217a49.48,49.48,0,0,0-12.62-1.57c-14.3,0-22.93,6-22.93,16.72,0,9.78,7.78,17.24,20.19,17.24m-92.44-.94h18.09V219.63h30.29v28.82h18.09V174.83H262.75v28.29H232.46V174.83H214.37Zm-68.93-27.87c0-8,6.31-14.09,14.62-14.09a17.22,17.22,0,0,1,11.78,4.31v19.45a16.36,16.36,0,0,1-11.78,4.42c-8.2,0-14.62-6.1-14.62-14.09m26.61,27.87h16.83v-77.3l-17,3.68v20.93a28.27,28.27,0,0,0-14.2-3.68c-16.19,0-28.92,12.51-28.92,28.5a28.26,28.26,0,0,0,28.4,28.6,25.12,25.12,0,0,0,14.93-4.83Zm-77.19-42.7c5.36,0,9.88,3.47,11.67,8.83H83.29c1.68-5.57,5.89-8.83,11.57-8.83M66.15,220.68c0,16.2,13.25,28.82,30.29,28.82,9.36,0,16.19-2.52,23.24-8.41l-11.26-10c-2.62,2.73-6.52,4.2-11.14,4.2a14.39,14.39,0,0,1-13.68-8.83h39.65v-4.21c0-17.67-11.88-30.39-28.08-30.39a28.57,28.57,0,0,0-29,28.81M36.81,190.29c6,0,9.36,3.79,9.36,8.31s-3.37,8.31-9.36,8.31H18.93V190.29Zm-36,58.16H18.93V221.63H32.7l13.89,26.82H66.78L50.58,219a22.27,22.27,0,0,0,13.89-20.72c0-13.25-10.42-23.45-26-23.45H.84Z"/></svg>
  </div>
  <div class="header-text">
    <h1>{esc(rep('title'))}</h1>
    <p style="font-size:20px;font-weight:700;margin-bottom:6px">{esc(rep('customer'))}</p>
    <p>{esc(rep('subtitle'))} &bull; {esc(rep('collection_date_label'))}: {esc(DATE_FORMAT)} &bull; {esc(rep('total_vms_label'))}: {len(hosts)}</p>
  </div>
</div>
''')

# ─── 1) Overview ─────────────────────────────────────────────────
html_parts.append(f'<h2 id="overview">{esc(hd("h_overview"))}</h2>')

# 1.1
html_parts.append(f'<h3 id="sec-1-1">{esc(hd("h_os_distribution"))}</h3>')
os_counter = Counter()
for h in hosts:
    os_counter[f'{h["distro"]} {h["distro_ver"]}'] += 1

html_parts.append(f'<table><thead><tr><th>{esc(th("os"))}</th><th>{esc(th("version"))}</th><th>{esc(th("quantity"))}</th><th>{esc(th("percent"))}</th></tr></thead><tbody>')
for os_name, count in os_counter.most_common():
    pct = f'{count/len(hosts)*100:.1f}%'
    html_parts.append(f'<tr><td>{esc(os_name)}</td><td>{esc(os_name.split()[-1])}</td><td>{count}</td><td>{pct}</td></tr>')
html_parts.append(f'</tbody><tfoot><tr style="font-weight:bold;background:#f5f5f5"><td colspan="2">{esc(th("total"))}</td><td>{len(hosts)}</td><td>100%</td></tr></tfoot>')
html_parts.append('</table>')

# 1.2
html_parts.append(f'<h3 id="sec-1-2">{esc(hd("h_app_distribution"))}</h3>')
app_counter = Counter()
for h in hosts:
    for at in h['app_type']:
        app_counter[at] += 1

html_parts.append(f'<table><thead><tr><th>{esc(th("app_type"))}</th><th>{esc(th("vm_count"))}</th></tr></thead><tbody>')
for app_name, count in app_counter.most_common():
    html_parts.append(f'<tr><td>{esc(app_name)}</td><td>{count}</td></tr>')
html_parts.append('</tbody></table>')

# 1.2.1
java_hosts = [h for h in hosts if h['has_java'] or h['installed_jboss'] or h['java_version']]
if java_hosts:
    html_parts.append(f'<h3 id="sec-1-2-1">{esc(hd("h_java_servers"))}</h3>')
    html_parts.append(f'<table><thead><tr><th>{esc(th("server"))}</th>{ns_th()}<th>{esc(th("type"))}</th><th>{esc(th("java_version"))}</th><th>{esc(th("app_server"))}</th><th>{esc(th("ports"))}</th><th>{esc(th("jar_app"))}</th></tr></thead><tbody>')
    for h in java_hosts:
        jpd = h['java_processes_detail']
        if jpd:
            for jp in jpd:
                jtype = jp.get('type', '?')
                java_ver = jp.get('java_version', '?')
                jboss = jp.get('jboss_info', {})
                app_srv = ''
                ports = ''
                if jboss:
                    jb_ver = jboss.get('version', 'unknown')
                    ports = jboss.get('ports', '')
                    if jb_ver and jb_ver != 'unknown':
                        app_srv = jb_ver
                    else:
                        app_srv = h['installed_jboss'] or f'JBoss ({jboss.get("type","")})'
                elif jtype == 'java-app':
                    app_srv = lb('jar_standalone')
                jar_file = jp.get('jar_file', '')
                if jar_file:
                    jar_file = jar_file.split('/')[-1] if '/' in jar_file else jar_file
                html_parts.append(f'<tr><td><a href="#host-{h["vm"]}">{esc(h["vm"])}</a></td>{ns_td(h)}<td><span class="badge badge-blue">{esc(jtype)}</span></td><td><strong>{esc(java_ver)}</strong></td><td>{esc(app_srv)}</td><td>{esc(ports)}</td><td>{esc(jar_file)}</td></tr>')
        else:
            jver = h['java_version'] or '?'
            app_srv = h['running_jboss'] or h['installed_jboss'] or 'Java standalone'
            html_parts.append(f'<tr><td><a href="#host-{h["vm"]}">{esc(h["vm"])}</a></td>{ns_td(h)}<td>—</td><td>{esc(jver)}</td><td>{esc(app_srv)}</td><td>—</td><td>—</td></tr>')
    html_parts.append('</tbody></table>')

# 1.2.2
php_hosts = [h for h in hosts if h['php_ver'] or h['apache_has_php']]
if php_hosts:
    html_parts.append(f'<h3 id="sec-1-2-2">{esc(hd("h_php_servers"))}</h3>')
    html_parts.append(f'<table><thead><tr><th>{esc(th("server"))}</th>{ns_th()}<th>{esc(th("web_server"))}</th><th>{esc(th("php_version"))}</th><th>{esc(th("document_root"))}</th><th>{esc(lb("memcached"))}</th></tr></thead><tbody>')
    for h in php_hosts:
        web_srv = ''
        if h['httpd_ver']:
            web_srv = f'Apache HTTPD {h["httpd_ver"]}'
        elif h['nginx_ver']:
            web_srv = f'Nginx {h["nginx_ver"]}'
        elif h['port_80']:
            web_srv = h['port_80']
        php_v = h['php_ver'] or '—'
        doc_root = '—'
        for ap in h['apache_processes_detail']:
            config = ap.get('config', {})
            config_data = config.get('config_data', {}) if isinstance(config, dict) else {}
            vhosts = config_data.get('VirtualHost', {})
            if vhosts and isinstance(vhosts, dict):
                for vh_name, vh_data in vhosts.items():
                    if isinstance(vh_data, dict) and vh_data.get('documentroot'):
                        doc_root = vh_data['documentroot']
                        break
            if doc_root == '—':
                dr = config_data.get('documentroot', '')
                if dr:
                    doc_root = dr
            if doc_root != '—':
                break
        memc = h['memcached_ver'] if h['memcached_ver'] else '—'
        html_parts.append(f'<tr><td><a href="#host-{h["vm"]}">{esc(h["vm"])}</a></td>{ns_td(h)}<td>{esc(web_srv)}</td><td>{esc(php_v)}</td><td>{esc(doc_root)}</td><td>{esc(memc)}</td></tr>')
    html_parts.append('</tbody></table>')

# 1.3 — only show if namespace data exists
if has_namespace:
    html_parts.append(f'<h3 id="sec-1-3">{esc(hd("h_namespace_distribution"))}</h3>')
    ns_counter = Counter()
    for h in hosts:
        ns_counter[h['namespace']] += 1
    html_parts.append(f'<table><thead><tr><th>{esc(th("namespace"))}</th><th>{esc(th("vms"))}</th></tr></thead><tbody>')
    for ns, count in ns_counter.most_common():
        html_parts.append(f'<tr><td>{esc(ns)}</td><td>{count}</td></tr>')
    html_parts.append('</tbody></table>')


# ─── 1.4) Conclusion ─────────────────────────────────────────────
html_parts.append(f'<h3 id="conclusion">{esc(hd("h_conclusion"))}</h3>')

total = len(hosts)
elig_clean = sum(1 for h in hosts if upgrade_analysis(h)[0] and not upgrade_analysis(h)[3])
elig_warn = sum(1 for h in hosts if upgrade_analysis(h)[0] and upgrade_analysis(h)[3])
not_elig = sum(1 for h in hosts if not upgrade_analysis(h)[0])

html_parts.append(f'''
<div class="card">
<h4>{esc(hd("h_eligibility_summary"))}</h4>
<table>
<tr><td><span class="badge badge-green">{esc(el("eligible_clean"))}</span></td><td><strong>{elig_clean}</strong> VMs</td></tr>
<tr><td><span class="badge badge-yellow">{esc(el("eligible_caveats"))}</span></td><td><strong>{elig_warn}</strong> VMs</td></tr>
<tr><td><span class="badge badge-red">{esc(el("not_eligible"))}</span></td><td><strong>{not_elig}</strong> VMs</td></tr>
<tr style="font-weight:bold"><td>{esc(th("total"))}</td><td>{total} VMs</td></tr>
</table>
</div>
''')

html_parts.append(f'<table><thead><tr><th>{esc(th("row_num"))}</th><th>{esc(th("server"))}</th>{ns_th()}<th>{esc(th("current_os"))}</th><th>{esc(th("upgrade_path"))}</th><th>{esc(th("eligible_q"))}</th><th>{esc(th("observations"))}</th></tr></thead><tbody>')

for i, h in enumerate(hosts, 1):
    eligible, status, blockers, warnings = upgrade_analysis(h)
    distro_label = f'{h["distro"]} {h["distro_ver"]}'
    css_class = 'eligible' if eligible and not warnings else ('with-caveats' if eligible else 'not-eligible')

    is_rhel = h['distro'] == 'RedHat'
    is_el = h['distro'] in EL_COMPATIBLE_DISTROS
    try:
        major_int = int(h['distro_major'])
    except (ValueError, TypeError):
        major_int = 0

    if major_int <= 6:
        path = el('path_migration')
    elif major_int == 7 and is_rhel:
        path = el('path_leapp')
    elif major_int == 7:
        path = el('path_convert_leapp')
    elif major_int >= 8 and is_rhel:
        path = el('path_already_rhel8')
    elif major_int >= 8 and is_el:
        path = el('path_convert')
    else:
        path = '—'

    obs = '; '.join(blockers + warnings) if (blockers or warnings) else '—'
    icon = el('icon_eligible') if eligible and not warnings else (el('icon_caveats') if eligible else el('icon_not_eligible'))
    html_parts.append(f'<tr><td>{i}</td><td><a href="#host-{h["vm"]}">{esc(h["vm"])}</a></td>{ns_td(h)}<td>{esc(distro_label)}</td><td>{esc(path)}</td><td class="{css_class}">{icon} {esc(status)}</td><td style="font-size:11px">{esc(obs)}</td></tr>')

html_parts.append('</tbody></table>')


# ─── 2) Detailed inventory ───────────────────────────────────────
html_parts.append(f'<h2 id="inventory">{esc(hd("h_inventory"))}</h2>')

for h in hosts:
    vm = h['vm']
    eligible, status, blockers, warnings = upgrade_analysis(h)

    badge_class = 'badge-green' if eligible and not warnings else ('badge-yellow' if eligible else 'badge-red')
    distro_label = f'{h["distro"]} {h["distro_ver"]}'

    html_parts.append(f'''
<div class="card" id="host-{vm}">
<div class="card-header">
  <h3>{esc(vm)} <span style="font-weight:normal;font-size:13px;opacity:0.8">— {esc(h["fqdn"])}{" — " + esc(h["namespace"]) if has_namespace else ""}</span></h3>
</div>
''')

    # 2.1
    html_parts.append(f'<h4>{esc(hd("h_server_info"))}</h4>')
    html_parts.append('<div class="grid">')
    html_parts.append(f'<div class="grid-item"><label>{esc(th("hostname_fqdn"))}</label><span>{esc(h["fqdn"])}</span></div>')
    html_parts.append(f'<div class="grid-item"><label>{esc(th("operating_system"))}</label><span>{esc(distro_label)} ({esc(h["os_family"])})</span></div>')
    html_parts.append(f'<div class="grid-item"><label>{esc(th("kernel"))}</label><span>{esc(h["kernel"])}</span></div>')
    html_parts.append(f'<div class="grid-item"><label>{esc(th("architecture"))}</label><span>{esc(h["arch"])}</span></div>')
    html_parts.append(f'<div class="grid-item"><label>{esc(th("platform"))}</label><span>{esc(h["product"])} {esc(h["product_ver"])}</span></div>')
    if has_namespace:
        html_parts.append(f'<div class="grid-item"><label>{esc(th("namespace"))}</label><span>{esc(h["namespace"])}</span></div>')
    html_parts.append('</div>')

    # Network
    html_parts.append(f'<h4>{esc(hd("h_network_config"))}</h4>')
    html_parts.append(f'<table><thead><tr><th>{esc(th("default_iface"))}</th><th>{esc(th("ip"))}</th><th>{esc(th("gateway"))}</th><th>{esc(th("netmask"))}</th><th>{esc(th("mac"))}</th></tr></thead><tbody>')
    dip = h['default_ipv4']
    html_parts.append(f'<tr><td>{esc(dip.get("interface",""))}</td><td>{esc(dip.get("address",""))}</td><td>{esc(dip.get("gateway",""))}</td><td>{esc(dip.get("netmask",""))}</td><td>{esc(dip.get("macaddress",""))}</td></tr>')
    html_parts.append('</tbody></table>')
    if h['ipv4_all']:
        html_parts.append(f'<p class="small">{esc(th("all_ipv4"))}: {", ".join(h["ipv4_all"])}</p>')

    # Resources
    html_parts.append(f'<h4>{esc(hd("h_resources"))}</h4>')
    html_parts.append(f'<table><thead><tr><th>{esc(th("vcpus"))}</th><th>{esc(th("ram"))}</th><th>{esc(th("swap"))}</th><th>{esc(th("uptime"))}</th></tr></thead><tbody>')
    uptime_days = h['uptime'] // 86400 if h['uptime'] else 0
    html_parts.append(f'<tr><td>{h["vcpus"]}</td><td>{h["ram_mb"]} MB ({h["ram_mb"]/1024:.1f} GB)</td><td>{h["swap_mb"]} MB</td><td>{uptime_days} {lb("days")}</td></tr>')
    html_parts.append('</tbody></table>')

    # Disks
    html_parts.append(f'<h4>{esc(hd("h_disks"))}</h4>')
    html_parts.append(f'<table><thead><tr><th>{esc(th("device"))}</th><th>{esc(th("size"))}</th><th>{esc(th("model"))}</th></tr></thead><tbody>')
    for dk, dv in h['devices'].items():
        if dk.startswith(('dm-', 'ram', 'loop')):
            continue
        html_parts.append(f'<tr><td>/dev/{esc(dk)}</td><td>{esc(dv.get("size","?"))}</td><td>{esc(dv.get("model","") or lb("virtual_disk"))}</td></tr>')
    html_parts.append('</tbody></table>')

    # LVM
    lvs = h['lvm'].get('lvs', {})
    if lvs:
        html_parts.append(f'<h4>{esc(hd("h_lvm"))}</h4>')
        html_parts.append(f'<table><thead><tr><th>{esc(th("lv"))}</th><th>{esc(th("vg"))}</th><th>{esc(th("size"))}</th></tr></thead><tbody>')
        for lv_name, lv_info in lvs.items():
            html_parts.append(f'<tr><td>{esc(lv_name)}</td><td>{esc(lv_info.get("vg",""))}</td><td>{esc(lv_info.get("size_g",""))} GB</td></tr>')
        html_parts.append('</tbody></table>')

    # Filesystems
    html_parts.append(f'<h4>{esc(hd("h_filesystems"))}</h4>')
    html_parts.append(f'<table><thead><tr><th>{esc(th("device"))}</th><th>{esc(th("mount_point"))}</th><th>{esc(th("fs_type"))}</th><th>{esc(th("size"))}</th><th>{esc(th("used"))}</th><th>{esc(th("available"))}</th><th>{esc(th("usage_pct"))}</th></tr></thead><tbody>')
    for m in h['mounts']:
        t = m.get('size_total', 0)
        avail = m.get('size_available', 0)
        if not isinstance(t, (int, float)):
            t = 0
        if not isinstance(avail, (int, float)):
            avail = 0
        used = t - avail if t else 0
        html_parts.append(f'<tr><td>{esc(m.get("device",""))}</td><td>{esc(m.get("mount",""))}</td><td>{esc(m.get("fstype",""))}</td><td>{fmt_bytes(t)}</td><td>{fmt_bytes(used)}</td><td>{fmt_bytes(avail)}</td><td>{pct_used(t, avail)}</td></tr>')
    html_parts.append('</tbody></table>')

    # 2.2 Processes
    html_parts.append(f'<h4>{esc(hd("h_processes"))}</h4>')

    skip_cmds = {'systemd', 'systemd-journald', 'systemd-udevd', 'systemd-logind', 'systemd-resolve',
                 'lvmetad', 'auditd', 'dbus-daemon', 'polkitd', 'gssproxy',
                 'irqbalance', 'kthreadd', 'agetty', 'login', 'bash', 'sh',
                 'sedispatch', 'rhsmcertd', 'tuned'}
    relevant_procs = [p for p in h['processes'] if p.get('command','') not in skip_cmds and not p.get('command','').startswith(('kworker','migration','ksoftirq','watchdog','rcu_'))]

    port_map = defaultdict(list)
    for t in h['tcp_listen']:
        pid = t.get('pid')
        if pid:
            port_map[str(pid)].append(f'TCP/{t["port"]} ({t.get("address","")})')
    for u in h['udp_listen']:
        pid = u.get('pid')
        if pid:
            port_map[str(pid)].append(f'UDP/{u["port"]} ({u.get("address","")})')

    html_parts.append(f'<table><thead><tr><th>{esc(th("pid"))}</th><th>{esc(th("user"))}</th><th>{esc(th("process"))}</th><th>{esc(th("memory"))}</th><th>{esc(th("ports"))}</th></tr></thead><tbody>')
    shown = set()
    for p in relevant_procs:
        pid = p.get('pid', '')
        cmd = p.get('command', '')
        if cmd in shown:
            continue
        shown.add(cmd)
        ports_str = ', '.join(port_map.get(str(pid), []))
        mem_kb = p.get('memory_kb', 0)
        mem_str = f'{mem_kb/1024:.1f} MB' if mem_kb and mem_kb > 1024 else f'{mem_kb} KB' if mem_kb else ''
        html_parts.append(f'<tr><td>{esc(pid)}</td><td>{esc(p.get("user",""))}</td><td>{esc(cmd)}</td><td>{esc(mem_str)}</td><td>{esc(ports_str)}</td></tr>')
    html_parts.append('</tbody></table>')

    # 2.3 Java
    html_parts.append(f'<h4>{esc(hd("h_java"))}</h4>')
    jpd = h['java_processes_detail']
    if jpd:
        html_parts.append(f'<table><thead><tr><th>{esc(th("pid"))}</th><th>{esc(th("type"))}</th><th>{esc(th("java_version"))}</th><th>{esc(th("app_server"))}</th><th>{esc(th("mode"))}</th><th>{esc(th("ports"))}</th><th>{esc(th("jar_app"))}</th></tr></thead><tbody>')
        for jp in jpd:
            pid = jp.get('pid', '?')
            jtype = jp.get('type', '?')
            java_ver = jp.get('java_version', '?')

            jboss = jp.get('jboss_info', {})
            tomcat_info = jp.get('tomcat_info', {})

            app_server = ''
            mode = ''
            ports = ''

            if jboss:
                jb_ver = jboss.get('version', 'unknown')
                jb_type = jboss.get('type', '')
                mode = jboss.get('mode', '')
                ports = jboss.get('ports', '')
                if jb_ver and jb_ver != 'unknown':
                    app_server = jb_ver
                else:
                    app_server = f'{h["installed_jboss"]}' if h['installed_jboss'] else f'JBoss ({jb_type})'
            elif tomcat_info:
                app_server = lb('tomcat')
                if isinstance(tomcat_info, dict):
                    app_server = f'{lb("tomcat")} {tomcat_info.get("version","")}'.strip()
            elif jtype == 'java-app':
                app_server = lb('jar_standalone')

            jar_file = jp.get('jar_file', '')
            if jar_file:
                jar_file = jar_file.split('/')[-1] if '/' in jar_file else jar_file

            html_parts.append(f'<tr><td>{esc(pid)}</td><td><span class="badge badge-blue">{esc(jtype)}</span></td><td><strong>{esc(java_ver)}</strong></td><td>{esc(app_server)}</td><td>{esc(mode)}</td><td>{esc(ports)}</td><td>{esc(jar_file)}</td></tr>')
        html_parts.append('</tbody></table>')
    elif h['has_java'] or h['installed_jboss'] or h['java_version']:
        html_parts.append(f'<table><thead><tr><th>{esc(th("item"))}</th><th>{esc(th("value"))}</th></tr></thead><tbody>')
        if h['java_version']:
            html_parts.append(f'<tr><td>{esc(lb("java_version_package"))}</td><td>{esc(h["java_version"])}</td></tr>')
        if h['installed_jboss']:
            html_parts.append(f'<tr><td>{esc(lb("jboss_installed"))}</td><td>{esc(h["installed_jboss"])}</td></tr>')
        if h['running_jboss']:
            html_parts.append(f'<tr><td>{esc(lb("jboss_running"))}</td><td>{esc(h["running_jboss"])}</td></tr>')
        html_parts.append('</tbody></table>')
    else:
        html_parts.append(f'<p class="small">{esc(msg("no_java"))}</p>')

    # 2.4 Web
    html_parts.append(f'<h4>{esc(hd("h_webserver"))}</h4>')
    apd = h['apache_processes_detail']
    has_web = apd or h['httpd_ver'] or h['nginx_ver'] or h['port_80']
    if has_web:
        html_parts.append(f'<table><thead><tr><th>{esc(th("item"))}</th><th>{esc(th("value"))}</th></tr></thead><tbody>')
        if h['httpd_ver']:
            html_parts.append(f'<tr><td>{esc(lb("apache_httpd_package"))}</td><td>{esc(h["httpd_ver"])}</td></tr>')
        if h['nginx_ver']:
            html_parts.append(f'<tr><td>{esc(lb("nginx_package"))}</td><td>{esc(h["nginx_ver"])}</td></tr>')
        if h['port_80'] and h['port_80'] not in ('httpd',):
            html_parts.append(f'<tr><td>{esc(lb("port_80_service"))}</td><td>{esc(h["port_80"])}</td></tr>')
        if h['php_ver']:
            html_parts.append(f'<tr><td>{esc(lb("php"))}</td><td>{esc(h["php_ver"])}</td></tr>')
        if h['apache_has_php']:
            html_parts.append(f'<tr><td>{esc(lb("apache_with_php"))}</td><td>{esc(lb("yes"))}</td></tr>')
        if h['memcached_ver']:
            html_parts.append(f'<tr><td>{esc(lb("memcached"))}</td><td>{esc(h["memcached_ver"])}</td></tr>')
        web_ports = [t for t in h['tcp_listen'] if t.get('name') in ('httpd', 'nginx', 'lighttpd') or t.get('port') in (80, 443)]
        if web_ports:
            ports_str = ', '.join(sorted(set([f'TCP/{t["port"]}' for t in web_ports])))
            html_parts.append(f'<tr><td>{esc(lb("web_ports_tcp"))}</td><td>{esc(ports_str)}</td></tr>')
        html_parts.append('</tbody></table>')

        if apd:
            html_parts.append(f'<h4 style="font-size:13px;margin-top:10px">{esc(hd("h_apache_instances"))}</h4>')
            for ap in apd:
                binary = ap.get('binary', '?')
                config_file = ap.get('default_config_file', '?')
                config = ap.get('config', {})
                config_data = config.get('config_data', {}) if isinstance(config, dict) else {}
                listen = config_data.get('listen', '?')
                server_admin = config_data.get('serveradmin', '')
                doc_root = config_data.get('documentroot', '')

                html_parts.append(f'<table><thead><tr><th>Binary</th><th>Config</th><th>Listen</th><th>ServerAdmin</th><th>{esc(th("document_root"))}</th></tr></thead><tbody>')
                html_parts.append(f'<tr><td>{esc(binary)}</td><td>{esc(config_file)}</td><td>{esc(listen)}</td><td>{esc(server_admin)}</td><td>{esc(doc_root)}</td></tr>')
                html_parts.append('</tbody></table>')

                vhosts = config_data.get('VirtualHost', {})
                if vhosts and isinstance(vhosts, dict):
                    html_parts.append(f'<table><thead><tr><th>VirtualHost</th><th>ServerName</th><th>{esc(th("document_root"))}</th></tr></thead><tbody>')
                    for vh_name, vh_data in vhosts.items():
                        if isinstance(vh_data, dict):
                            sn = vh_data.get('servername', '—')
                            dr = vh_data.get('documentroot', '—')
                        else:
                            sn = '—'
                            dr = '—'
                        html_parts.append(f'<tr><td>{esc(vh_name)}</td><td>{esc(sn)}</td><td>{esc(dr)}</td></tr>')
                    html_parts.append('</tbody></table>')
    else:
        html_parts.append(f'<p class="small">{esc(msg("no_webserver"))}</p>')

    # 2.5 Database
    html_parts.append(f'<h4>{esc(hd("h_database"))}</h4>')
    has_db = h['memcached_ver']
    db_ports = [t for t in h['tcp_listen'] if t.get('port') in (5432, 3306, 27017, 6379, 1521)]
    if has_db or db_ports:
        html_parts.append(f'<table><thead><tr><th>{esc(th("item"))}</th><th>{esc(th("value"))}</th></tr></thead><tbody>')
        if h['memcached_ver']:
            html_parts.append(f'<tr><td>{esc(lb("memcached"))}</td><td>{esc(h["memcached_ver"])}</td></tr>')
        for dp in db_ports:
            html_parts.append(f'<tr><td>{esc(lb("port_label"))} {dp["port"]}</td><td>{esc(dp.get("name","?"))} (user: {esc(dp.get("user","?"))})</td></tr>')
        html_parts.append('</tbody></table>')
    else:
        html_parts.append(f'<p class="small">{esc(msg("no_database"))}</p>')

    # 2.6 Services
    html_parts.append(f'<h4>{esc(hd("h_services"))}</h4>')
    relevant_svc_names = ['httpd', 'nginx', 'jboss', 'wildfly', 'tomcat', 'java', 'sshd',
                          'postfix', 'crond', 'zabbix', 'glpi', 'memcached', 'redis',
                          'postgresql', 'mysql', 'mariadb', 'mongod', 'firewalld',
                          'iptables', 'rsyslog', 'chronyd', 'ntpd', 'lighttpd']
    running_svcs = []
    for svc_name, svc_info in h['services'].items():
        if svc_info.get('state') == 'running':
            base = svc_name.replace('.service', '')
            if any(r in base.lower() for r in relevant_svc_names):
                running_svcs.append((base, svc_info.get('status', '?'), svc_info.get('source', '?')))

    if running_svcs:
        html_parts.append(f'<table><thead><tr><th>{esc(th("service"))}</th><th>{esc(th("status"))}</th><th>{esc(th("source"))}</th></tr></thead><tbody>')
        for sn, ss, so in sorted(running_svcs):
            html_parts.append(f'<tr><td>{esc(sn)}</td><td>{esc(ss)}</td><td>{esc(so)}</td></tr>')
        html_parts.append('</tbody></table>')
    else:
        html_parts.append(f'<p class="small">{esc(msg("no_services"))}</p>')

    # Firewall/SELinux
    fw_status = h['fw'].get('status', '?')
    se_status = h['se'].get('status', '?')
    html_parts.append(f'<p class="small">{esc(lb("firewall"))}: <strong>{esc(h["fw"].get("firewall","?"))}</strong> ({esc(fw_status)}) | {esc(lb("selinux"))}: <strong>{esc(se_status)}</strong></p>')

    # 2.7/2.8 Upgrade
    html_parts.append(f'<h4>{esc(hd("h_upgrade"))}</h4>')
    css_class = 'eligible' if eligible and not warnings else ('with-caveats' if eligible else 'not-eligible')
    html_parts.append(f'<p class="{css_class}">{esc(status)}</p>')
    if blockers:
        html_parts.append('<ul>')
        for b in blockers:
            html_parts.append(f'<li style="color:{colors("blocker_color")}">{esc(b)}</li>')
        html_parts.append('</ul>')
    if warnings:
        html_parts.append('<ul>')
        for w in warnings:
            html_parts.append(f'<li style="color:{colors("warning_color")}">{esc(w)}</li>')
        html_parts.append('</ul>')

    html_parts.append('</div>')


html_parts.append(f'''
<a href="#" class="back-top" title="{esc(sb('back_to_top_title'))}">↑</a>
</div>
</div>
<script>
var _resizing = false;
document.addEventListener("DOMContentLoaded", function() {{
  document.querySelectorAll("table").forEach(function(table) {{
    var thead = table.querySelector("thead");
    var tbody = table.querySelector("tbody");
    if (!thead || !tbody || tbody.rows.length < 2) return;
    var headers = thead.querySelectorAll("th");
    headers.forEach(function(th, idx) {{
      th.classList.add("sortable");
      th.addEventListener("click", function() {{
        if (_resizing) return;
        var rows = Array.from(tbody.rows);
        var asc = !th.classList.contains("asc");
        headers.forEach(function(h) {{ h.classList.remove("asc","desc"); }});
        th.classList.add(asc ? "asc" : "desc");
        rows.sort(function(a, b) {{
          var av = (a.cells[idx] || {{}}).textContent || "";
          var bv = (b.cells[idx] || {{}}).textContent || "";
          var an = parseFloat(av.replace(/[^\\d.\\-]/g, ""));
          var bn = parseFloat(bv.replace(/[^\\d.\\-]/g, ""));
          if (!isNaN(an) && !isNaN(bn)) return asc ? an - bn : bn - an;
          return asc ? av.localeCompare(bv, "{LOCALE_SORT}") : bv.localeCompare(av, "{LOCALE_SORT}");
        }});
        rows.forEach(function(r) {{ tbody.appendChild(r); }});
      }});
    }});
  }});
}});

  var filterInput = document.getElementById("sidebarFilter");
  var hostLinks = document.querySelectorAll(".sidebar a.s-host");
  if (filterInput) {{
    filterInput.addEventListener("input", function() {{
      var q = this.value.toLowerCase();
      hostLinks.forEach(function(a) {{
        var vm = (a.getAttribute("data-vm") || "").toLowerCase();
        a.classList.toggle("hidden", q.length > 0 && vm.indexOf(q) === -1);
      }});
    }});
  }}

  // Column resize
  document.querySelectorAll("table thead").forEach(function(thead) {{
    var ths = thead.querySelectorAll("th");
    ths.forEach(function(th) {{
      var resizer = document.createElement("div");
      resizer.className = "resizer";
      th.appendChild(resizer);
      var startX, startW;
      resizer.addEventListener("mousedown", function(e) {{
        e.stopPropagation();
        e.preventDefault();
        startX = e.pageX;
        startW = th.offsetWidth;
        _resizing = true;
        resizer.classList.add("resizing");
        th.closest("table").style.tableLayout = "fixed";
        var onMove = function(e2) {{
          th.style.width = (startW + e2.pageX - startX) + "px";
        }};
        var onUp = function() {{
          resizer.classList.remove("resizing");
          document.removeEventListener("mousemove", onMove);
          document.removeEventListener("mouseup", onUp);
          setTimeout(function() {{ _resizing = false; }}, 50);
        }};
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
      }});
    }});
  }});

  // Sidebar toggle
  var sidebarEl = document.getElementById("sidebar");
  var toggleBtn = document.getElementById("sidebarToggle");
  var mainEl = document.getElementById("mainContent");
  if (toggleBtn && sidebarEl && mainEl) {{
    toggleBtn.addEventListener("click", function() {{
      sidebarEl.classList.toggle("collapsed");
      toggleBtn.classList.toggle("collapsed");
      mainEl.classList.toggle("expanded");
    }});
  }}

  var allNavLinks = document.querySelectorAll(".sidebar a[href^=\\"#\\"]");
  var targets = [];
  allNavLinks.forEach(function(a) {{
    var id = a.getAttribute("href").substring(1);
    var el = document.getElementById(id);
    if (el) targets.push({{link: a, el: el}});
  }});
  var ticking = false;
  window.addEventListener("scroll", function() {{
    if (!ticking) {{
      ticking = true;
      requestAnimationFrame(function() {{
        var scrollY = window.scrollY + 120;
        var current = null;
        for (var i = 0; i < targets.length; i++) {{
          if (targets[i].el.offsetTop <= scrollY) current = targets[i].link;
        }}
        allNavLinks.forEach(function(a) {{ a.classList.remove("active"); }});
        if (current) current.classList.add("active");
        ticking = false;
      }});
    }}
  }});
</script>
</body>
</html>
''')

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(''.join(html_parts))

print(f'Report generated: {OUTPUT_FILE} ({len(hosts)} hosts)')
