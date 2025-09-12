# Ansible Discovery - Container Environment

Este documento descreve como gerenciar o ambiente de containers do Ansible Discovery usando Podman Compose.

## 🏗️ Arquitetura dos Containers

```text
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│     Grafana         │    │   MongoDB Proxy     │    │     MongoDB         │
│   (Port 3000)       │    │   (Port 8000)       │    │   (Port 27017)      │
│                     │    │                     │    │                     │
│ • Admin: admin      │◄──►│ • REST API          │◄──►│ • Database Storage  │
│ • Pass: redhat      │    │ • Health checks     │    │ • Ansible Facts     │
│ • JSON Tree Panel   │    │ • Query interface   │    │ • Collection cache  │
│ • Infinity Plugin   │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         │                           │                           │
         └─────────────────────────────────────────────────────────┘
                              ansible-discovery-net
```

## 📋 Pré-requisitos

- **Podman**: Container runtime
- **podman-compose**: Orquestração de containers
- **Curl**: Para health checks (opcional)

### Instalação do podman-compose

```bash
pip install podman-compose
```

## 🚀 Uso Rápido

### Iniciar todos os serviços

```bash
./manage-stack.sh up
```

### Parar todos os serviços

```bash
./manage-stack.sh down
```

### Ver status dos serviços

```bash
./manage-stack.sh status
```

## 📁 Estrutura de Volumes

Os dados são persistidos em diretórios do host no `$HOME` do usuário:

```text
$HOME/ansible-discovery-volumes/
├── mongodb-data/     # Dados do MongoDB
├── grafana-data/     # Dados do Grafana (dashboards, plugins)
└── grafana-logs/     # Logs do Grafana
```

## 🔧 Comandos Disponíveis

| Comando | Descrição |
|---------|-----------|
| `./manage-stack.sh up` | Inicia todos os serviços |
| `./manage-stack.sh down` | Para todos os serviços |
| `./manage-stack.sh restart` | Reinicia todos os serviços |
| `./manage-stack.sh status` | Mostra status dos containers |
| `./manage-stack.sh logs` | Mostra logs de todos os serviços |
| `./manage-stack.sh logs grafana` | Mostra logs apenas do Grafana |
| `./manage-stack.sh clean` | Remove containers e redes (mantém dados) |
| `./manage-stack.sh setup` | Cria apenas os diretórios de volumes |

## 🌐 Pontos de Acesso

### Grafana

- **URL**: <http://localhost:3000>
- **Usuário**: admin
- **Senha**: redhat
- **Plugins disponíveis**:
  - `andrewlinuxadmin-json-tree-panel` (customizado)
  - `yesoreyeram-infinity-datasource` (oficial)

### MongoDB

- **URL**: `mongodb://localhost:27017`
- **Banco**: ansible (usado pelo cache do Ansible)
- **Coleção**: cache (facts dos hosts)

### MongoDB Proxy

- **URL**: <http://localhost:8000>
- **Health Check**: <http://localhost:8000>
- **API REST**: Interface para consultas ao MongoDB

## 📊 Monitoramento

### Health Checks

Todos os serviços têm health checks configurados:

```bash
# Verificar saúde individual
podman exec ansible-discovery-grafana curl -f http://localhost:3000/api/health
podman exec ansible-discovery-mongodb mongosh --eval "db.adminCommand('ping')"
podman exec ansible-discovery-mongodb-proxy curl -f http://localhost:8000/
```

### Logs em Tempo Real

```bash
# Todos os serviços
./manage-stack.sh logs

# Serviço específico
./manage-stack.sh logs mongodb
./manage-stack.sh logs grafana
./manage-stack.sh logs mongodb-proxy
```

## 🔧 Troubleshooting

### Problema: Container não inicia

```bash
# Verificar logs
./manage-stack.sh logs <service-name>

# Verificar status
./manage-stack.sh status

# Reiniciar serviços
./manage-stack.sh restart
```

### Problema: Volumes com permissões incorretas

```bash
# Recriar volumes com permissões corretas
./manage-stack.sh setup

# Verificar permissões
ls -la $HOME/ansible-discovery-volumes/
```

### Problema: Porta já em uso

```bash
# Verificar portas em uso
ss -tlnp | grep -E ":(3000|8000|27017)"

# Parar conflitos
./manage-stack.sh down
```

## 🧹 Limpeza

### Limpeza Completa (preserva dados)

```bash
./manage-stack.sh clean
```

### Limpeza de Dados (CUIDADO!)

```bash
# Para tudo
./manage-stack.sh down

# Remove dados (NÃO REVERSÍVEL)
rm -rf $HOME/ansible-discovery-volumes/

# Recria estrutura
./manage-stack.sh setup
```

## 🐛 Debug

### Entrar nos containers

```bash
# MongoDB
podman exec -it ansible-discovery-mongodb mongosh

# Grafana
podman exec -it ansible-discovery-grafana /bin/bash

# MongoDB Proxy
podman exec -it ansible-discovery-mongodb-proxy /bin/bash
```

### Verificar rede

```bash
# Listar redes
podman network ls

# Inspecionar rede
podman network inspect ansible-discovery_ansible-discovery-net
```

## 📝 Configuração Personalizada

### Variáveis de Ambiente

Edite o arquivo `podman-compose.yaml` para personalizar:

```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=suasenha    # Senha do Grafana
  - MONGO_INITDB_ROOT_USERNAME=usuario     # Usuário MongoDB
  - MONGO_INITDB_ROOT_PASSWORD=senha       # Senha MongoDB
```

### Portas Customizadas

```yaml
ports:
  - "3001:3000"  # Grafana na porta 3001
  - "27018:27017"  # MongoDB na porta 27018
  - "8001:8000"  # Proxy na porta 8001
```

## 🔗 Integração com Ansible

Para usar este ambiente com o playbook de descoberta:

1. **Configure o cache do MongoDB** no `ansible.cfg`:

   ```ini
   [defaults]
   fact_caching = mongodb
   fact_caching_connection = mongodb://localhost:27017/ansible
   fact_caching_timeout = 0
   ```

2. **Execute a descoberta**:

   ```bash
   cd playbooks/
   ansible-playbook -i inventory discovery.yaml
   ```

3. **Verifique os dados no Grafana**:
   - Acesse <http://localhost:3000>
   - Configure data source para MongoDB
   - Importe dashboards do projeto
