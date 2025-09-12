# Testes Unitários - Módulos Customizados

Este diretório contém testes unitários para os módulos customizados do projeto Ansible Discovery.

## Estrutura

- `test_process_facts.py` - Testes unitários do módulo process_facts ✅
- `test_nginx_config_parser.py` - Testes do módulo nginx_config_parser ✅ (formato standalone)
- `test_apache_config_parser.py` - **FALTANDO** ❌
- `test_php_config_parser.py` - **FALTANDO** ❌
- `run_tests.sh` - Script para executar todos os testes automaticamente
- `.flake8` - Configuração do flake8 para os testes
- `nginx.conf` - Arquivo de configuração NGINX para testes
- `mime.types` - Arquivo de tipos MIME para testes do NGINX
- `README.md` - Esta documentação

## Status dos Testes

| Módulo | Teste | Formato | Status | Cobertura |
|--------|--------|---------|---------|-----------|
| `process_facts` | ✅ `test_process_facts.py` | unittest | 28 testes OK | Excelente |
| `nginx_config_parser` | ✅ `test_nginx_config_parser.py` | standalone | 5 testes OK | Boa |
| `apache_config_parser` | ❌ **FALTANDO** | - | - | Nenhuma |
| `php_config_parser` | ❌ **FALTANDO** | - | - | Nenhuma |

## Como Executar

### Opção 1: Script Automatizado (Recomendado)

```bash
cd playbooks/library/tests
./run_tests.sh
```

### Opção 2: Execução Manual

```bash
cd playbooks/library/tests

# Ativar ambiente virtual (se necessário)
cd ../../.. && source activate && cd playbooks/library/tests

# Executar todos os testes unittest
python3 -m unittest test_process_facts.py -v

# Executar teste standalone do nginx
python3 test_nginx_config_parser.py

# Verificar lint de todos os testes
python3 -m flake8 test_*.py --ignore=E501,E203,W503,W504
```

## Cobertura dos Testes

### TestProcessCollectorPure

**Inicialização e Configuração:**
- ✅ `test_init` - Testa inicialização com parâmetros padrão
- ✅ `test_init_with_false_params` - Testa inicialização com parâmetros desabilitados

**Métodos Utilitários:**
- ✅ `test_get_boot_time_success` - Extração bem-sucedida do boot time
- ✅ `test_get_boot_time_failure` - Fallback em caso de erro
- ✅ `test_get_user_info_success` - Informações de usuário válidas
- ✅ `test_get_user_info_failure` - Fallback para UID desconhecido

**Detecção de Kernel Threads:**
- ✅ `test_is_kernel_thread_empty_cmdline` - Cmdline vazio (kernel thread)
- ✅ `test_is_kernel_thread_normal_process` - Processo normal
- ✅ `test_is_kernel_thread_no_cmdline_file` - Arquivo cmdline inexistente

**Detecção de Containers:**
- ✅ `test_is_containerized_docker` - Processo em container Docker
- ✅ `test_is_containerized_normal_process` - Processo não containerizado
- ✅ `test_is_containerized_disabled` - Detecção desabilitada

**Métricas de Performance:**
- ✅ `test_get_memory_usage_success` - Extração de uso de memória
- ✅ `test_get_memory_usage_no_rss` - VmRSS não encontrado
- ✅ `test_get_memory_usage_file_error` - Erro de arquivo
- ✅ `test_get_cpu_usage_success` - Cálculo de CPU
- ✅ `test_get_cpu_usage_file_error` - Erro no arquivo stat

**Parsing de Dados:**
- ✅ `test_parse_stat_file_success` - Parsing bem-sucedido do /proc/PID/stat
- ✅ `test_parse_stat_file_error` - Erro no parsing
- ✅ `test_get_cmdline_success` - Extração de argumentos
- ✅ `test_get_cmdline_empty` - Cmdline vazio
- ✅ `test_get_cmdline_error` - Erro na leitura
- ✅ `test_get_process_user_success` - Usuário do processo
- ✅ `test_get_process_user_error` - Erro na obtenção do usuário

### TestProcessFactsIntegration

**Testes de Integração:**
- ✅ `test_collect_processes_no_proc` - /proc filesystem indisponível
- ✅ `test_collect_processes_success` - Coleta bem-sucedida de processos

### TestMainFunction

**Função Principal do Módulo Ansible:**
- ✅ `test_main_success` - Execução bem-sucedida
- ✅ `test_main_exception` - Tratamento de exceções

## Tecnologias Utilizadas

- **unittest** - Framework de testes do Python
- **unittest.mock** - Mocking para isolamento de testes
- **flake8** - Verificação de qualidade de código
- **black** - Formatação de código (usado no desenvolvimento)

## Configuração de Qualidade

### Arquivo .flake8

O arquivo `.flake8` contém configurações específicas para os testes:

- **max-line-length**: 88 caracteres (compatível com black)
- **Ignora regras**: E501 (linha longa), E402 (import após sys.path)
- **Per-file ignores**: Regras específicas para arquivos de teste

### Regras Ignoradas

- `E501` - Linha muito longa (permitimos até 88 caracteres)
- `E402` - Import não no topo (necessário para manipulação do sys.path)
- `W503/W504` - Quebras de linha em operadores (compatibilidade com black)

## Padrões de Teste

### Mocking
- Usa `patch` para mockar chamadas de sistema (/proc, pwd, etc.)
- `mock_open` para simular leitura de arquivos
- `MagicMock` para objetos complexos

### Estrutura
- Cada método público tem pelo menos um teste de sucesso
- Casos de erro são testados separadamente
- Testes de integração verificam o fluxo completo

### Nomenclatura
- `test_[metodo]_success` - Caso de sucesso
- `test_[metodo]_failure` / `test_[metodo]_error` - Casos de erro
- `test_[metodo]_[cenario_especifico]` - Cenários específicos

## Executando Testes Específicos

```bash
# Testar apenas uma classe
python3 -m unittest test_process_facts.TestProcessCollectorPure -v

# Testar apenas um método
python3 -m unittest test_process_facts.TestProcessCollectorPure.test_init -v

# Executar com mais verbosidade
python3 -m unittest test_process_facts.py -v --failfast
```

## Verificação de Qualidade

Os testes seguem os padrões estabelecidos:
- Máximo 88 caracteres por linha (configurado no .flake8)
- Imports organizados corretamente
- Docstrings em português para métodos de teste
- Uso de `# noqa: E402` para imports após manipulação do sys.path
