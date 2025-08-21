# Custom Ansible Filters for File Operations

## Resumo

Foram criados três filters personalizados para verificação de existência e
acessibilidade de arquivos e caminhos no Ansible:

- `file_exists`: Verifica se um arquivo específico existe
- `path_exists`: Verifica se um caminho (arquivo ou diretório) existe
- `file_readable`: Verifica se um arquivo existe e pode ser lido pelo usuário atual

## Implementação

### Arquivo: `filter_plugins/file_utils.py`

```python
import os

class FilterModule(object):
    def filters(self):
        return {
            'file_exists': self.file_exists,
            'path_exists': self.path_exists,
            'file_readable': self.file_readable
        }

    def file_exists(self, path):
        """
        Check if a file exists and is a regular file
        Returns True if the path exists and is a file, False otherwise
        """
        if not path:
            return False
        return os.path.isfile(path)

    def path_exists(self, path):
        """
        Check if a path exists (file or directory)
        Returns True if the path exists, False otherwise
        """
        if not path:
            return False
        return os.path.exists(path)

    def file_readable(self, path):
        """
        Check if a file exists and is readable by current user
        Returns True if file exists and is readable, False otherwise
        """
        try:
            return os.path.isfile(path) and os.access(path, os.R_OK)
        except (TypeError, AttributeError, OSError):
            return False
```

## Uso Básico

### Verificação Individual

```yaml
- name: "Check if file exists"
  debug:
    msg: "File exists: {{ '/etc/passwd' | file_exists }}"

- name: "Check if directory exists"
  debug:
    msg: "Directory exists: {{ '/opt' | path_exists }}"

- name: "Check if file is readable"
  debug:
    msg: "File readable: {{ '/etc/passwd' | file_readable }}"

- name: "Check if protected file is readable"
  debug:
    msg: "Shadow readable: {{ '/etc/shadow' | file_readable }}"
```

### Usando com Condicionais

```yaml
- name: "Do something if file exists"
  debug:
    msg: "Processing file"
  when: "/path/to/file.jar" | file_exists

- name: "Create directory if it doesn't exist"
  file:
    path: "/opt/java"
    state: directory
  when: not ("/opt/java" | path_exists)

- name: "Process only readable config files"
  include_tasks: process_config.yaml
  when: item | file_readable
  loop: "{{ config_files }}"

- name: "Read file content safely"
  slurp:
    src: "{{ config_file }}"
  register: file_content
  when: config_file | file_readable
```

### Filtrando Listas

**Abordagem com Loop (Recomendada):**

```yaml
- name: "Find existing JAR files"
  set_fact:
    existing_jars: []

- name: "Check each JAR path"
  set_fact:
    existing_jars: "{{ existing_jars + [item] }}"
  loop: "{{ jar_paths }}"
  when: item | file_exists
```

**Nota:** O uso direto de `select('file_exists')` pode ter problemas de
compatibilidade. Use a abordagem com loop para resultados mais confiáveis.

## Exemplos Práticos

### Descoberta de JARs Java

```yaml
- name: "Define common JAR locations"
  set_fact:
    common_jar_paths:
      - "/opt/app.jar"
      - "/usr/local/bin/application.jar"
      - "/home/{{ ansible_user }}/app.jar"

- name: "Find existing JARs"
  set_fact:
    found_jars: []

- name: "Check each JAR location"
  set_fact:
    found_jars: "{{ found_jars + [item] }}"
  loop: "{{ common_jar_paths }}"
  when: item | file_exists

- name: "Display results"
  debug:
    msg: "Found {{ found_jars | length }} JAR files: {{ found_jars }}"
```

### Verificação de Acessibilidade de Arquivos

```yaml
- name: "Check config file accessibility"
  set_fact:
    accessible_configs: []

- name: "Test config file readability"
  set_fact:
    accessible_configs: "{{ accessible_configs + [item] }}"
  loop:
    - "/etc/myapp/config.xml"
    - "/opt/myapp/settings.conf"
    - "/var/lib/myapp/database.cfg"
  when: item | file_readable

- name: "Process only accessible configs"
  include_tasks: parse_config.yaml
  loop: "{{ accessible_configs }}"
```

### Validação de Configuração

```yaml
- name: "Validate required paths"
  set_fact:
    path_validation:
      - path: "/etc/java"
        required: true
        exists: "{{ '/etc/java' | path_exists }}"
      - path: "/opt/application.jar"
        required: true
        exists: "{{ '/opt/application.jar' | file_exists }}"

- name: "Report missing required paths"
  debug:
    msg: "Missing required path: {{ item.path }}"
  loop: "{{ path_validation }}"
  when: item.required and not item.exists
```

## Diferenças Entre os Filtros

| Filtro | Verifica Existência | Verifica Tipo | Verifica Permissão | Uso Recomendado |
|--------|:------------------:|:-------------:|:-----------------:|-----------------|
| `file_exists` | ✅ | ✅ (arquivo regular) | ❌ | Verificar se arquivo específico existe |
| `path_exists` | ✅ | ❌ (qualquer tipo) | ❌ | Verificar se caminho existe (arquivo/diretório) |
| `file_readable` | ✅ | ✅ (arquivo regular) | ✅ (leitura) | Verificar se arquivo pode ser processado |

### Exemplos Comparativos

```yaml
# Cenário: /etc/shadow existe mas não é legível pelo usuário comum
- debug: msg="{{ '/etc/shadow' | file_exists }}"     # True
- debug: msg="{{ '/etc/shadow' | path_exists }}"     # True  
- debug: msg="{{ '/etc/shadow' | file_readable }}"   # False

# Cenário: /etc é um diretório
- debug: msg="{{ '/etc' | file_exists }}"            # False
- debug: msg="{{ '/etc' | path_exists }}"            # True
- debug: msg="{{ '/etc' | file_readable }}"          # False

# Cenário: /etc/passwd é um arquivo legível
- debug: msg="{{ '/etc/passwd' | file_exists }}"     # True
- debug: msg="{{ '/etc/passwd' | path_exists }}"     # True
- debug: msg="{{ '/etc/passwd' | file_readable }}"   # True
```

## Vantagens dos Filters Personalizados

1. **Performance**: Evita múltiplas chamadas do módulo `stat`
2. **Simplicidade**: Sintaxe mais limpa nos templates
3. **Reutilização**: Pode ser usado em qualquer lugar do playbook
4. **Legibilidade**: Código mais fácil de entender

## Comparação com Abordagens Tradicionais

### Antes (usando stat)

```yaml
- name: "Check if file exists"
  stat:
    path: "/path/to/file"
  register: file_stat

- name: "Use file if exists"
  debug:
    msg: "File found"
  when: file_stat.stat.exists
```

### Depois (usando filter)

```yaml
- name: "Use file if exists"
  debug:
    msg: "File found"
  when: "/path/to/file" | file_exists
```

## Testes

Execute o teste completo:

```bash
ansible-playbook -i inventory test_jar_filter.yaml
```

Resultado esperado:

- Verificação de existência de arquivos JAR em locais comuns
- Validação de diretórios importantes
- Relatório de arquivos encontrados e não encontrados
