# MongoDB Dashboard Scripts

Este diretório contém scripts Python para gerenciar o dashboard Grafana com queries MongoDB de descoberta de infraestrutura.

## 📁 Arquivos Principais

| Arquivo | Descrição | Tamanho |
|---------|-----------|---------|
| `enhanced-queries.html` | 27 queries MongoDB organizadas em HTML | ~24KB |
| `dashboard-explorer.json` | Dashboard Grafana com queries integradas | ~32KB |
| `test_all_queries.py` | Ferramenta de teste das queries MongoDB | ~19KB |
| `update_dashboard.py` | Atualiza dashboard com conteúdo HTML | ~7KB |

## 🚀 Quick Start

### 1. Deploy the Complete Stack
```bash
# From project root directory
cd /path/to/ansible-discovery
podman-compose up -d

# Check services status
podman-compose ps
```

### 2. Teste Básico
```bash
# Teste rápido (primeiras 5 queries)
python3 test_all_queries.py --quick --verbose

# Teste completo (todas as 27 queries)
python3 test_all_queries.py --verbose
```

### 3. Atualizar Dashboard

```bash
# Atualizar com backup automático
python3 update_dashboard.py --backup

# Atualizar sem backup
python3 update_dashboard.py
```

## 🧪 Scripts de Teste

### test_all_queries.py
Testa todas as queries MongoDB contra a API do proxy.

**Uso:**
```bash
# Teste rápido (5 queries)
python3 test_all_queries.py --quick

# Teste completo com saída verbosa
python3 test_all_queries.py --verbose

# Salvar resultados em JSON
python3 test_all_queries.py --json results.json
```

**Funcionalidades:**
- ✅ Testa 27 queries em 9 categorias
- ✅ Verifica conectividade da API
- ✅ Relatórios detalhados em console e JSON
- ✅ Medição de performance
- ✅ Categorização automática

## � Scripts de Atualização

### update_dashboard.py
Integra o conteúdo HTML das queries no dashboard Grafana.

**Uso:**
```bash
# Com backup automático (recomendado)
python3 update_dashboard.py --backup

# Arquivos customizados
python3 update_dashboard.py --dashboard custom.json --html custom.html
```

**Funcionalidades:**
- ✅ Backup automático antes de atualizar
- ✅ Detecta painel HTML automaticamente
- ✅ Atualiza versão do dashboard
- ✅ Validação de arquivos

## 📊 Estrutura das Queries

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GF_SECURITY_ADMIN_USER` | `admin` | Grafana admin username |
| `GF_SECURITY_ADMIN_PASSWORD` | `admin` | Grafana admin password |
| `GF_USERS_ALLOW_SIGN_UP` | `false` | Allow user registration |
| `GF_AUTH_ANONYMOUS_ENABLED` | `true` | Enable anonymous access |
| `GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS` | `grafana-json-tree-panel` | Allow custom plugin |
| `MONGODB_PROXY_URL` | `http://localhost:8000` | MongoDB Proxy API base URL |

### Plugin Configuration

The custom plugin is automatically:
- Built during container build process
- Installed in `/var/lib/grafana/plugins/`
- Enabled in Grafana configuration
- Marked as trusted (unsigned plugin allowed)

## 🌐 Access

### Grafana Web Interface
- **URL**: http://localhost:3000
- **Default Login**: admin/admin
- **Anonymous Access**: Enabled (Viewer role)

### API Endpoints

- **MongoDB Proxy**: Configurable via `MONGODB_PROXY_URL` (default: http://localhost:8000)
- **Health Check**: http://localhost:3000/api/health

## 🔌 Plugin Details

### JSON Tree Panel Plugin

**Features:**
- Interactive JSON tree visualization
- Expandable/collapsible nodes
- Search functionality
- Syntax highlighting
- Copy to clipboard
- Responsive design

**Usage:**
1. Create new dashboard
2. Add panel
3. Select "JSON Tree Panel" from visualizations
4. Configure data source (MongoDB Proxy API)
5. Set query to fetch Ansible facts

## 🏗️ Build Process

### Multi-Stage Build

```dockerfile
# Stage 1: Build plugin
FROM nodejs:18 AS plugin-builder
# Install dependencies and build plugin

# Stage 2: Grafana runtime
FROM ubi9:9.3
# Install Grafana and copy built plugin
```

### Build Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `GRAFANA_VERSION` | `10.2.2` | Grafana version to install |

### Custom Build

```bash
# Build with specific Grafana version
podman build --build-arg GRAFANA_VERSION=10.1.0 -t grafana-custom .

# Build with custom tags
podman build -t quay.io/myorg/ansible-discovery-grafana:v1.0 .
```

## 📊 Data Integration

### Connecting to Ansible Discovery

1. **Configure Data Source**:
   - Type: JSON API
   - URL: http://grafana-api:8000
   - Access: Server (default)

2. **Create Queries**:
   ```json
   {
     "pipeline": [
       {"$match": {"_id": {"$regex": "ansible_facts"}}},
       {"$limit": 10}
     ]
   }
   ```

3. **Use JSON Tree Panel**:
   - Add panel to dashboard
   - Select JSON Tree Panel visualization
   - Configure data source and query

## 🩺 Health Checks

### Container Health

```bash
# Check Grafana health
curl http://localhost:3000/api/health

# Check plugin status
curl http://localhost:3000/api/plugins

# Check specific plugin
curl http://localhost:3000/api/plugins/grafana-json-tree-panel
```

### Troubleshooting

**Plugin not loading:**
```bash
# Check plugin directory
podman exec -it ansible-discovery-grafana ls -la /var/lib/grafana/plugins/

# Check Grafana logs
podman logs ansible-discovery-grafana

# Verify plugin configuration
podman exec -it ansible-discovery-grafana cat /etc/grafana/grafana.ini | grep plugins
```

**Build failures:**
```bash
# Check build logs
podman build --no-cache .

# Verify Node.js in builder stage
podman run --rm ubi9/nodejs-18 node --version

# Test plugin build manually
cd grafana-json-tree-panel && npm run build
```

## 🔒 Security

### Production Recommendations

1. **Change default passwords**:
   ```bash
   -e GF_SECURITY_ADMIN_PASSWORD=secure_password
   ```

2. **Disable anonymous access**:
   ```bash
   -e GF_AUTH_ANONYMOUS_ENABLED=false
   ```

3. **Use HTTPS**:
   - Configure reverse proxy (nginx/traefik)
   - Set `GF_SERVER_PROTOCOL=https`

4. **Network security**:
   - Use custom networks
   - Restrict port exposure
   - Enable container firewall

## 📁 File Structure

```text
grafana/
├── Containerfile              # Multi-stage build definition
├── .containerignore          # Build optimization
├── grafana.ini              # Grafana configuration
├── README.md               # This file
├── provisioning/           # Grafana provisioning configs
│   ├── datasources/       # Data source configurations
│   └── dashboards/        # Dashboard provisioning configs
├── dashboard-*.json       # Dashboard JSON definitions
└── grafana-json-tree-panel/ # Custom plugin source
    ├── src/                 # Plugin source code
    ├── package.json        # Node.js dependencies
    ├── webpack.config.js   # Build configuration
    └── plugin.json        # Plugin metadata
```

## 🤝 Integration with Ansible Discovery

This Grafana setup integrates with:

1. **Ansible Discovery Playbooks** → MongoDB Cache
2. **MongoDB Proxy API** (Sanic) → Grafana Data Source
3. **JSON Tree Panel** → Data Visualization
4. **Grafana Dashboards** → Analytics & Reporting

Complete workflow:
```
Ansible Discovery → MongoDB → Sanic API → Grafana → Dashboards
```

## 📝 License

Part of the Ansible Discovery project. See main project LICENSE file.
