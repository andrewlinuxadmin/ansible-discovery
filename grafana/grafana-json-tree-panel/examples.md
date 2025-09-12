# Example Grafana Dashboard Configuration

This directory contains examples of how to use the JSON Tree Panel with different data sources.

## Redis Example

```json
{
  "dashboard": {
    "title": "Ansible Discovery - JSON Tree View",
    "panels": [
      {
        "title": "Host Facts Tree",
        "type": "json-tree-panel",
        "targets": [
          {
            "datasource": "Redis",
            "command": "JSON.GET",
            "key": "ansible_facts_localhost",
            "path": "$"
          }
        ],
        "options": {
          "showTypes": true,
          "expandLevel": 2,
          "maxStringLength": 50
        }
      }
    ]
  }
}
```

## Example Redis Queries

### Single Host Facts
```bash
JSON.GET ansible_facts_localhost '$'
```

### Host Info Only
```bash
JSON.GET ansible_facts_localhost '$.host_info'
```

### Statistics
```bash
JSON.GET ansible_facts_localhost '$.stats'
```

### Network Information
```bash
JSON.GET ansible_facts_localhost '$.network'
```

## HTTP API Example

If you have an HTTP endpoint serving JSON:

```json
{
  "targets": [
    {
      "datasource": "HTTP",
      "url": "http://your-api/hosts/localhost/facts",
      "method": "GET"
    }
  ]
}
```

## MongoDB Example

For MongoDB data source:

```javascript
db.cache.findOne(
  {"_id": "ansible_factslocalhost"}, 
  {"data": 1}
)
```
