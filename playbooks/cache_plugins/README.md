# Redis JSON Cache Plugin

Um plugin de cache personalizado para Ansible que armazena facts diretamente como estruturas RedisJSON, otimizado para consultas em dashboards Grafana.

## Características

### ✨ Funcionalidades Principais

- **Armazenamento RedisJSON Nativo**: Dados estruturados navegáveis com JSONPath
- **Compatibilidade Completa**: Fallback automático para Redis padrão se RedisJSON não estiver disponível
- **Estrutura Otimizada**: Organização hierárquica ideal para dashboards
- **Genérico e Reutilizável**: Funciona com qualquer tipo de dados do Ansible
- **Metadados Automáticos**: Timestamps, versões e informações de transformação

### 🏗️ Estrutura dos Dados

```json
{
  "host_info": {
    "hostname": "server01",
    "distribution": "Ubuntu",
    "architecture": "x86_64",
    "uptime": 86400
  },
  "ansible_facts": {
    "ansible_hostname": "server01",
    "ansible_distribution": "Ubuntu",
    "ansible_interfaces": ["eth0", "lo"]
  },
  "custom_facts": {
    "java_processes": [...],
    "apache_processes": [...],
    "any_custom_variable": "value"
  },
  "network": {
    "interfaces": ["eth0", "lo"],
    "default_ipv4": {...},
    "interface_details": {...}
  },
  "services": {...},
  "stats": {
    "ansible_facts_count": 45,
    "custom_facts_count": 12,
    "memory_total_mb": 8192,
    "cpu_count": 4,
    "last_updated": "1757082742"
  },
  "_metadata": {
    "timestamp": 1757082742,
    "format_version": "1.0",
    "source": "ansible_cache_redis_json"
  },
  "_raw": { ... }
}
```

## Instalação

### Pré-requisitos

1. **Redis Stack** com módulo RedisJSON:
   ```bash
   # Verificar se RedisJSON está disponível
   redis-cli MODULE LIST | grep -i json
   ```

2. **Biblioteca Python Redis**:
   ```bash
   pip install redis>=3.0.0
   ```

### Configuração

1. **Copie o plugin** para o diretório `cache_plugins/` do seu projeto Ansible:
   ```
   playbooks/
   ├── cache_plugins/
   │   └── redis_json.py
   └── ansible.cfg
   ```

2. **Configure ansible.cfg**:
   ```ini
   [defaults]
   fact_caching = redis_json
   fact_caching_timeout = 0
   fact_caching_connection = redis://localhost:6379/0
   ```

### Opções de Configuração

| Opção | Descrição | Padrão | Variável de Ambiente |
|-------|-----------|--------|---------------------|
| `fact_caching_connection` | String de conexão Redis | `redis://localhost:6379/0` | `ANSIBLE_CACHE_PLUGIN_CONNECTION` |
| `fact_caching_timeout` | Timeout em segundos (0 = nunca expira) | `0` | `ANSIBLE_CACHE_PLUGIN_TIMEOUT` |
| `fact_caching_prefix` | Prefixo para chaves Redis | `ansible_facts` | `ANSIBLE_CACHE_PLUGIN_PREFIX` |

## Uso

### Consultas JSONPath para Grafana

```bash
# Informações básicas do host
redis-cli JSON.GET ansible_factsserver01 $.host_info

# Contadores para métricas
redis-cli JSON.GET ansible_factsserver01 $.stats.memory_total_mb

# Facts customizados específicos
redis-cli JSON.GET ansible_factsserver01 $.custom_facts.java_processes

# Interfaces de rede
redis-cli JSON.GET ansible_factsserver01 $.network.interfaces

# Todos os facts Ansible nativos
redis-cli JSON.GET ansible_factsserver01 $.ansible_facts
```

### Exemplos para Dashboards

#### Painel de Sistema
```json
{
  "query": "JSON.GET ansible_facts* $.stats",
  "metric": "memory_total_mb",
  "aggregation": "sum"
}
```

#### Painel de Serviços
```json
{
  "query": "JSON.GET ansible_facts* $.stats.services_running",
  "metric": "services_running",
  "aggregation": "avg"
}
```

#### Painel de Rede
```json
{
  "query": "JSON.GET ansible_facts* $.stats.interface_count",
  "metric": "interface_count",
  "aggregation": "max"
}
```

## Vantagens vs Cache Padrão

### Cache Redis Tradicional
```json
"serialized_json_string_with_all_data_flat"
```

### Cache RedisJSON (Este Plugin)
```json
{
  "navegável": true,
  "queries_eficientes": "JSONPath",
  "dashboard_friendly": true,
  "agregações": "possíveis"
}
```

## Troubleshooting

### RedisJSON não disponível
```bash
# Verificar módulos Redis
redis-cli MODULE LIST

# Se RedisJSON não estiver carregado
redis-cli MODULE LOAD /path/to/redisjson.so
```

### Fallback para Redis padrão
O plugin automaticamente faz fallback para Redis padrão se RedisJSON falhar:
```
WARNING: RedisJSON not available, using standard Redis storage
```

### Debug de conexão
```bash
# Testar conectividade
redis-cli -h localhost -p 6379 PING

# Verificar chaves do cache
redis-cli KEYS "ansible_facts*"
```

## Limitações

1. **Requer Redis Stack** ou módulo RedisJSON carregado
2. **Compatibilidade**: Python 2.7+ e 3.x
3. **Tamanho**: Dados grandes podem ser limitados pela memória Redis

## Desenvolvimento

### Estrutura do Código
- `_transform_to_redisjson()`: Transforma dados Ansible em estrutura otimizada
- `set()`: Armazena dados como RedisJSON
- `get()`: Recupera dados com fallback automático
- Métodos padrão: `delete()`, `flush()`, `keys()`, etc.

### Extensões Futuras
- Compressão automática para dados grandes
- Múltiplas estratégias de particionamento
- Índices automáticos para consultas frequentes
- Integração com Redis Search

## Licença

GNU General Public License v3.0+
