# Java Application Discovery Documentation

## Overview

The Java discovery system implements a multi-stage process classification pipeline for detecting and analyzing Java-based applications running on the system.

## Architecture

### Discovery Pipeline

```text
java.yaml (main orchestrator)
├── Process Collection (via process_facts module)
├── Java Process Classification
├── Conditional Application Discovery
│   ├── tomcat.yaml (Apache Tomcat)
│   ├── jboss.yaml (JBoss/WildFly/EAP)
│   └── jar.yaml (Standalone JAR applications)
└── Data Consolidation
```

### Process Classification Logic

```yaml
# Primary classification based on command line arguments
app_type: >-
  {{
    'tomcat' if 'catalina' in args or 'tomcat' in args else
    'jboss' if 'jboss' in args or 'wildfly' in args or 'eap' in args else
    'springboot' if 'spring-boot' in args or 'spring.boot' in args else
    'quarkus' if 'quarkus' in args else
    'java-app'
  }}
```

## Main Java Module

**File**: `java/java.yaml`

### Purpose

Main orchestrator that:

1. Collects all Java processes from system
2. Classifies processes by application type
3. Sets detection flags for specific application types
4. Includes appropriate specialized modules
5. Consolidates results into unified structure

### Key Variables

```yaml
# Detection flags set by java.yaml
has_tomcat_processes: boolean    # True if Tomcat detected
has_jboss_processes: boolean     # True if JBoss/WildFly detected
has_jar_processes: boolean       # True if standalone JARs detected

# Main data structure
java_processes: [
  {
    pid: 1234,
    user: "tomcat",
    command: "/usr/bin/java -Dcatalina.base=/opt/tomcat ...",
    app_type: "tomcat",
    java_version: "11.0.16",
    tomcat_info: { ... },    # Set by tomcat.yaml
    jboss_info: { ... },     # Set by jboss.yaml
    jar_info: { ... }        # Set by jar.yaml
  }
]
```

### Process Classification

```yaml
# Enhanced classification with detailed patterns
- name: Classify Java processes
  set_fact:
    classified_processes: "{{ classified_processes | default([]) + [item | combine(classification)] }}"
  vars:
    classification:
      app_type: >-
        {{
          'tomcat' if (
            'catalina' in item.command.lower() or
            'tomcat' in item.command.lower() or
            'bootstrap.jar' in item.command.lower()
          ) else
          'jboss' if (
            'jboss' in item.command.lower() or
            'wildfly' in item.command.lower() or
            'eap' in item.command.lower() or
            'standalone.sh' in item.command.lower()
          ) else
          'springboot' if (
            'spring-boot' in item.command.lower() or
            'spring.boot' in item.command.lower() or
            item.command | regex_search('\.jar.*spring')
          ) else
          'quarkus' if (
            'quarkus' in item.command.lower() or
            'quarkus-run.jar' in item.command.lower()
          ) else
          'jar' if '.jar' in item.command.lower() else
          'java-app'
        }}
  loop: "{{ java_processes }}"
```

---

## Tomcat Module

**File**: `java/tomcat.yaml`

### Tomcat Purpose

Specialized discovery for Apache Tomcat instances with detailed configuration analysis.

### Tomcat Detection Strategy

```yaml
# Multi-method Tomcat detection
tomcat_patterns:
  - "catalina"
  - "tomcat"
  - "bootstrap.jar"
  - "CATALINA_HOME"
  - "CATALINA_BASE"
```

### Configuration Discovery

```yaml
# Tomcat home detection
- name: Extract Tomcat paths from command line
  set_fact:
    tomcat_paths: "{{ tomcat_paths | default({}) | combine({
      'catalina_home': item | regex_search('-Dcatalina.home=([^\\s]+)', '\\1') | first | default('unknown'),
      'catalina_base': item | regex_search('-Dcatalina.base=([^\\s]+)', '\\1') | first | default('unknown'),
      'java_home': item | regex_search('-Djava.home=([^\\s]+)', '\\1') | first | default('unknown')
    }) }}"
  when: "'catalina' in item.lower()"
```

### Server Configuration Analysis

```yaml
# Parse server.xml for configuration details
- name: Analyze Tomcat server.xml
  xml:
    path: "{{ catalina_base }}/conf/server.xml"
    xpath: "//Connector"
    content: attribute
  register: tomcat_connectors
  when: "{{ catalina_base }}/conf/server.xml" | file_readable

# Extract connector information
- name: Parse Tomcat connectors
  set_fact:
    connector_info:
      port: "{{ item.attrib.port | default('unknown') }}"
      protocol: "{{ item.attrib.protocol | default('HTTP/1.1') }}"
      ssl_enabled: "{{ item.attrib.SSLEnabled | default('false') | bool }}"
      max_threads: "{{ item.attrib.maxThreads | default('200') }}"
  loop: "{{ tomcat_connectors.matches | default([]) }}"
```

### Web Application Discovery

```yaml
# Discover deployed web applications
- name: Find Tomcat web applications
  find:
    paths: "{{ catalina_base }}/webapps"
    file_type: directory
  register: tomcat_webapps
  when: "{{ catalina_base }}/webapps" | path_exists

- name: Analyze web applications
  set_fact:
    webapp_info: "{{ webapp_info | default([]) + [webapp_detail] }}"
  vars:
    webapp_detail:
      name: "{{ item.path | basename }}"
      path: "{{ item.path }}"
      war_file: "{{ item.path }}.war"
      web_xml: "{{ item.path }}/WEB-INF/web.xml"
      context_xml: "{{ item.path }}/META-INF/context.xml"
      size: "{{ item.size | default(0) }}"
      modified: "{{ item.mtime | default(0) }}"
  loop: "{{ tomcat_webapps.files | default([]) }}"
```

### Tomcat Output Structure

```json
{
  "tomcat_info": {
    "version": "9.0.65",
    "catalina_home": "/opt/tomcat",
    "catalina_base": "/opt/tomcat",
    "java_opts": "-Xmx2048m -XX:+UseG1GC",
    "connectors": [
      {
        "port": "8080",
        "protocol": "HTTP/1.1",
        "ssl_enabled": false,
        "max_threads": "200"
      },
      {
        "port": "8443",
        "protocol": "HTTP/1.1",
        "ssl_enabled": true,
        "keystore": "/opt/tomcat/conf/keystore.jks"
      }
    ],
    "webapps": [
      {
        "name": "manager",
        "path": "/opt/tomcat/webapps/manager",
        "war_file": "/opt/tomcat/webapps/manager.war",
        "context_path": "/manager",
        "status": "deployed"
      }
    ],
    "libraries": [
      {
        "name": "mysql-connector.jar",
        "version": "8.0.30",
        "path": "/opt/tomcat/lib/mysql-connector.jar"
      }
    ]
  }
}
```

---

## JBoss Module

**File**: `java/jboss.yaml`

### JBoss Purpose

Specialized discovery for JBoss/WildFly/EAP instances with domain and standalone configurations.

### JBoss Detection Strategy

```yaml
# JBoss detection patterns
jboss_patterns:
  - "jboss"
  - "wildfly"
  - "eap"
  - "standalone.sh"
  - "domain.sh"
  - "jboss-modules.jar"
```

### Instance Type Detection

```yaml
# Determine JBoss operation mode
- name: Detect JBoss operation mode
  set_fact:
    jboss_mode: >-
      {{
        'domain' if 'domain' in item.command.lower() else
        'standalone' if 'standalone' in item.command.lower() else
        'unknown'
      }}
    jboss_home: "{{ item.command | regex_search('-Djboss.home.dir=([^\\s]+)', '\\1') | first | default('unknown') }}"
    jboss_base: "{{ item.command | regex_search('-Djboss.server.base.dir=([^\\s]+)', '\\1') | first | default('unknown') }}"
  when: "'jboss' in item.command.lower() or 'wildfly' in item.command.lower()"
```

### Configuration Analysis

```yaml
# Parse standalone.xml or domain.xml
- name: Analyze JBoss configuration
  xml:
    path: "{{ config_file }}"
    xpath: "//socket-binding[@name='http']"
    content: attribute
  register: jboss_http_binding
  vars:
    config_file: >-
      {{
        jboss_base + '/configuration/standalone.xml' if jboss_mode == 'standalone'
        else jboss_base + '/configuration/domain.xml'
      }}
  when: config_file | file_readable

# Extract deployment information
- name: Find JBoss deployments
  find:
    paths: "{{ jboss_base }}/deployments"
    patterns: "*.war,*.ear,*.jar"
  register: jboss_deployments
  when: "{{ jboss_base }}/deployments" | path_exists
```

### JBoss Output Structure

```json
{
  "jboss_info": {
    "product": "WildFly|JBoss EAP|JBoss AS",
    "version": "26.1.2.Final",
    "mode": "standalone|domain",
    "jboss_home": "/opt/wildfly",
    "jboss_base": "/opt/wildfly/standalone",
    "configuration": "standalone.xml",
    "socket_bindings": {
      "http": {
        "port": "8080",
        "interface": "public"
      },
      "https": {
        "port": "8443",
        "interface": "public"
      }
    },
    "subsystems": [
      "undertow",
      "ejb3",
      "jpa",
      "security-manager"
    ],
    "deployments": [
      {
        "name": "application.war",
        "path": "/opt/wildfly/standalone/deployments/application.war",
        "status": "deployed",
        "context_root": "/application"
      }
    ],
    "datasources": [
      {
        "jndi_name": "java:jboss/datasources/ExampleDS",
        "driver": "h2",
        "connection_url": "jdbc:h2:mem:test"
      }
    ]
  }
}
```

---

## JAR Module

**File**: `java/jar.yaml`

### JAR Purpose

Discovery for standalone JAR applications including Spring Boot, Quarkus, and custom applications.

### JAR Classification

```yaml
# Detailed JAR application classification
- name: Classify JAR applications
  set_fact:
    jar_classification: >-
      {{
        'spring-boot' if (
          'spring-boot' in item.command.lower() or
          'spring.boot' in item.command.lower() or
          item.command | regex_search('spring-boot-.*\.jar')
        ) else
        'quarkus' if (
          'quarkus' in item.command.lower() or
          'quarkus-run.jar' in item.command.lower() or
          item.command | regex_search('quarkus-app')
        ) else
        'executable-jar' if item.command | regex_search('-jar\\s+([^\\s]+\\.jar)') else
        'classpath-jar'
      }}
```

### Spring Boot Detection

```yaml
# Spring Boot specific analysis
- name: Analyze Spring Boot applications
  block:
    - name: Extract Spring Boot JAR path
      set_fact:
        spring_jar_path: "{{ item.command | regex_search('-jar\\s+([^\\s]+\\.jar)', '\\1') | first }}"

    - name: Check for Spring Boot properties
      stat:
        path: "{{ spring_jar_path | dirname }}/application.properties"
      register: spring_properties

    - name: Read Spring Boot configuration
      slurp:
        src: "{{ spring_jar_path | dirname }}/application.properties"
      register: spring_config
      when: spring_properties.stat.exists

  when: jar_classification == 'spring-boot'
```

### Quarkus Detection

```yaml
# Quarkus specific analysis
- name: Analyze Quarkus applications
  block:
    - name: Find Quarkus application directory
      set_fact:
        quarkus_app_dir: "{{ item.command | regex_search('quarkus-app') }}"

    - name: Check for Quarkus configuration
      find:
        paths: "{{ quarkus_app_dir | dirname }}"
        patterns: "application.properties,application.yml,application.yaml"
      register: quarkus_config_files

  when: jar_classification == 'quarkus'
```

### Generic JAR Analysis

```yaml
# Generic JAR file analysis
- name: Analyze JAR manifest
  shell: |
    jar_file="{{ jar_path }}"
    if [ -f "$jar_file" ]; then
      # Extract manifest information
      unzip -q -c "$jar_file" META-INF/MANIFEST.MF 2>/dev/null | \
      awk '
        /^Main-Class:/ { main_class = $2 }
        /^Implementation-Version:/ { version = $2 }
        /^Implementation-Title:/ { title = $2 }
        END {
          printf "{\"main_class\":\"%s\",\"version\":\"%s\",\"title\":\"%s\"}\n", 
                 main_class, version, title
        }'
    else
      echo '{"error": "jar_file_not_found"}'
    fi
  register: jar_manifest
  when: jar_path is defined and jar_path != 'unknown'
```

### JAR Output Structure

```json
{
  "jar_info": {
    "type": "spring-boot|quarkus|executable-jar|classpath-jar",
    "jar_path": "/opt/app/application.jar",
    "manifest": {
      "main_class": "com.example.Application",
      "version": "1.0.0",
      "title": "Example Application"
    },
    "spring_boot": {
      "version": "2.7.3",
      "configuration": {
        "server.port": "8080",
        "spring.datasource.url": "jdbc:h2:mem:testdb"
      },
      "profiles": ["prod", "database"]
    },
    "quarkus": {
      "version": "2.13.3.Final",
      "build_mode": "native|jvm",
      "configuration": {
        "quarkus.http.port": "8080",
        "quarkus.datasource.db-kind": "postgresql"
      }
    },
    "dependencies": [
      {
        "group": "org.springframework.boot",
        "artifact": "spring-boot-starter-web",
        "version": "2.7.3"
      }
    ],
    "heap_settings": {
      "xmx": "2048m",
      "xms": "512m",
      "gc_algorithm": "G1GC"
    }
  }
}
```

---

## Java Version Detection

### JVM Information Extraction

```yaml
# Extract Java version and JVM details
- name: Detect Java version
  shell: |
    # Try to get Java version from process
    pid="{{ item.pid }}"
    if [ -d "/proc/$pid" ]; then
      # Get Java executable path
      java_exe=$(readlink /proc/$pid/exe 2>/dev/null)
      if [ -n "$java_exe" ]; then
        # Get version information
        "$java_exe" -version 2>&1 | head -1 | \
        awk -F'"' '{print $2}' | \
        awk '{
          version = $1
          if (match(version, /^1\.([0-9]+)/)) {
            major = substr(version, RSTART+2, RLENGTH-2)
          } else if (match(version, /^([0-9]+)/)) {
            major = substr(version, RSTART, RLENGTH)
          }
          printf "{\"version\":\"%s\",\"major\":\"%s\",\"executable\":\"%s\"}\n", 
                 version, major, java_exe
        }' java_exe="$java_exe"
      fi
    fi
  register: java_version_result
  failed_when: false
```

### JVM Arguments Analysis

```yaml
# Parse JVM arguments for memory and GC settings
- name: Analyze JVM arguments
  set_fact:
    jvm_analysis:
      heap_max: "{{ item.command | regex_search('-Xmx([0-9]+[kmgKMG]?)', '\\1') | first | default('unknown') }}"
      heap_min: "{{ item.command | regex_search('-Xms([0-9]+[kmgKMG]?)', '\\1') | first | default('unknown') }}"
      gc_algorithm: >-
        {{
          'G1GC' if '-XX:+UseG1GC' in item.command else
          'ParallelGC' if '-XX:+UseParallelGC' in item.command else
          'ConcMarkSweepGC' if '-XX:+UseConcMarkSweepGC' in item.command else
          'SerialGC' if '-XX:+UseSerialGC' in item.command else
          'default'
        }}
      debug_enabled: "{{ '-agentlib:jdwp' in item.command }}"
      jmx_enabled: "{{ 'com.sun.management.jmxremote' in item.command }}"
      system_properties: "{{ item.command | regex_findall('-D([^=]+)=([^\\s]+)') | items2dict }}"
```

---

## Data Consolidation

### Final Structure Assembly

```yaml
# Consolidate all Java application information
- name: Consolidate Java process information
  set_fact:
    consolidated_java_processes: "{{ consolidated_java_processes | default([]) + [consolidated_process] }}"
  vars:
    consolidated_process:
      pid: "{{ item.pid }}"
      user: "{{ item.user }}"
      command: "{{ item.command }}"
      app_type: "{{ item.app_type }}"
      java_version: "{{ java_versions[item.pid] | default({}) }}"
      jvm_arguments: "{{ jvm_analyses[item.pid] | default({}) }}"
      tomcat_info: "{{ tomcat_data[item.pid] | default({}) if item.app_type == 'tomcat' else {} }}"
      jboss_info: "{{ jboss_data[item.pid] | default({}) if item.app_type == 'jboss' else {} }}"
      jar_info: "{{ jar_data[item.pid] | default({}) if item.app_type in ['jar', 'spring-boot', 'quarkus'] else {} }}"
  loop: "{{ classified_java_processes }}"
```

### Cache Strategy

```yaml
# Set cacheable facts for persistent storage
- name: Cache Java discovery results
  set_fact:
    java_processes: "{{ consolidated_java_processes }}"
    java_discovery_timestamp: "{{ ansible_date_time.epoch }}"
    java_discovery_summary:
      total_processes: "{{ consolidated_java_processes | length }}"
      tomcat_count: "{{ consolidated_java_processes | selectattr('app_type', 'equalto', 'tomcat') | list | length }}"
      jboss_count: "{{ consolidated_java_processes | selectattr('app_type', 'equalto', 'jboss') | list | length }}"
      springboot_count: "{{ consolidated_java_processes | selectattr('app_type', 'equalto', 'spring-boot') | list | length }}"
      quarkus_count: "{{ consolidated_java_processes | selectattr('app_type', 'equalto', 'quarkus') | list | length }}"
      jar_count: "{{ consolidated_java_processes | selectattr('app_type', 'equalto', 'jar') | list | length }}"
    cacheable: true
```

## Usage Examples

### Single Application Testing

```bash
# Test only Java discovery
ansible-playbook discovery.yaml -e collector_only=java -e debug=true

# Test specific Java application type
ansible-playbook discovery.yaml -e collector_only=java -e java_app_filter=tomcat
```

### Manual Testing

```bash
# Test Java process classification
ansible localhost -m shell -a "ps aux | grep java | grep -v grep"

# Test specific Tomcat detection
ansible localhost -m shell -a "ps aux | grep catalina"

# Verify Java versions
ansible localhost -m shell -a "java -version"
```

### Debugging

```bash
# Check Java process details
ansible-playbook discovery.yaml -e collector_only=java -e log=true | grep -A 20 "java_processes"

# Test configuration file reading
ansible localhost -m stat -a "path=/opt/tomcat/conf/server.xml"
```

## Common Issues

### Permission Problems

- Configuration files may require elevated privileges
- Process information might be limited for other users
- JAR file analysis needs read access

### Path Detection Issues

- Dynamic classpath configurations
- Symbolic links in installation paths
- Container-specific path mappings

### Version Detection Challenges

- Multiple Java versions on same system
- Custom JVM distributions
- Container runtime differences

## Container Considerations

### Containerized Java Applications

```yaml
# Container-specific adjustments
- name: Detect container environment for Java
  set_fact:
    java_container_context:
      is_container: "{{ ansible_virtualization_type == 'docker' or ansible_virtualization_type == 'container' }}"
      java_home: "{{ ansible_env.JAVA_HOME | default('/opt/java/openjdk') }}"
      app_home: "{{ ansible_env.APP_HOME | default('/app') }}"
  when: java_processes | length > 0
```

### Docker-Specific Handling

- Environment variable based configuration
- Volume-mounted configuration files
- Limited process visibility
- Different file system layouts
