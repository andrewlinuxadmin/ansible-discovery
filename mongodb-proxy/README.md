# Ansible Discovery MongoDB Proxy

A web service that provides a Grafana data source interface for the Ansible Discovery MongoDB cache.

## 🚀 Quick Start

### Using Podman Compose (Recommended)

```bash
# Build and start the services
podman-compose up -d

# Check the logs
podman-compose logs -f grafana-api

# Test the API
curl http://localhost:8000/search
```

### Using Docker Compose

```bash
# Build and start the services
docker-compose -f compose.yaml up -d

# Check the logs
docker-compose -f compose.yaml logs -f grafana-api

# Test the API
curl http://localhost:8000/search
```

### Using Podman/Docker

```bash
# Build the container
podman build -t ansible-discovery-grafana .

# Run with MongoDB
podman run -d --name mongodb -p 27017:27017 mongo:7.0

# Run the Grafana API
podman run -d --name grafana-api \
  -p 8000:8000 \
  -e MONGODB_URI=mongodb://localhost:27017 \
  ansible-discovery-grafana
```

## 📋 Prerequisites

- Container runtime (Docker/Podman)
- MongoDB (included in docker-compose.yaml)
- Network access to MongoDB from the container

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `ANSIBLE_DB` | `ansible` | Database name |
| `CACHE_COLLECTION` | `cache` | Collection name |
| `WORKERS` | `4` | Number of worker processes |
| `PYTHONUNBUFFERED` | `1` | Python output buffering |

### MongoDB Setup

The service expects MongoDB with:

- Database: `ansible`
- Collection: `cache`
- Documents in Ansible facts cache format

## 🌐 API Endpoints

### POST /search

Returns list of available hostnames from the cache.

**Response:**

```json
["server1.example.com", "server2.example.com"]
```

### GET /annotations

Returns empty annotations array (Grafana compatibility).

**Response:**

```json
[]
```

### POST /query

Executes MongoDB aggregation pipeline for data queries.

**Request:**

```json
{
  "pipeline": [...],
  "range": {
    "from": "1640995200000",
    "to": "1641081600000"
  }
}
```

### 📝 Collection Parameter

All endpoints support a `collection` parameter to specify which MongoDB collection to query:

**Default behavior** (uses collection from `CACHE_COLLECTION` environment variable):

```json
{
  "pipeline": [{"$match": {"data.java_processes": {"$exists": true}}}]
}
```

**Custom collection** (specify in request body for `/search`, `/query`, and `/host`):

**Applies to all POST endpoints**:

- `/search` - Find documents from specified collection
- `/query` - Aggregation queries from specified collection  
- `/host` - Pretty formatted host details from specified collection

## 🏗️ Building

### Container Build

```bash
# Build with Podman
podman build -t ansible-discovery-grafana .

# Build with Docker
docker build -t ansible-discovery-grafana .
```

### Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run in debug mode
python3 mongodb-proxy.py
```

## 🩺 Health Checks

The container includes health checks:

```bash
# Check container health
podman healthcheck run grafana-api

# Manual health check
curl http://localhost:8000/search
```

## 🔒 Security Features

- Non-root user execution
- UBI9 base image with security updates
- Minimal attack surface
- No unnecessary packages

## 📊 Monitoring

### Logs

```bash
# Container logs (Podman)
podman logs -f grafana-api

# Podman Compose logs
podman-compose logs -f grafana-api

# Docker Compose logs
docker-compose -f compose.yaml logs -f grafana-api
```

### Metrics

- HTTP endpoint: `http://localhost:8000`
- Health check: Container health status
- MongoDB connection: Via application logs

## 🛠️ Troubleshooting

### Common Issues

1. **Connection refused**: Check MongoDB connectivity
2. **Empty search results**: Verify Ansible facts are cached in MongoDB
3. **Permission errors**: Ensure non-root user has proper permissions

### Debug Commands

```bash
# Test MongoDB connection
podman exec -it mongodb mongosh ansible --eval "db.cache.count()"

# Check application logs
podman logs grafana-api

# Test API endpoints
curl -X POST http://localhost:8000/search
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"pipeline":[]}'
```

## 🏷️ Container Labels

The container includes OpenShift/Kubernetes compatible labels:

- `io.k8s.description`
- `io.k8s.display-name`
- `io.openshift.tags`

## 📦 Files Structure

```text
mongodb-proxy/
├── Containerfile              # Container build definition
├── .containerignore          # Container build ignore patterns
├── requirements.txt          # Python dependencies (pinned versions)
├── init-mongo.js            # MongoDB initialization script
├── mongodb-proxy.py         # Main application
└── README.md               # This file
```

## 🤝 Integration with Ansible Discovery

This service is designed to work with the main Ansible Discovery playbooks:

1. Run Ansible Discovery to populate MongoDB cache
2. Start this Grafana data source service
3. Configure Grafana to use this service as a data source
4. Create dashboards using the aggregation pipeline queries

## 📝 License

Part of the Ansible Discovery project. See main project LICENSE file.
