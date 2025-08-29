# Cache Management Scripts

This directory contains scripts for managing the MongoDB cache used by the Ansible Discovery system.

## Scripts Overview

### 1. clear-cache-simple.sh (Recommended)

**Purpose**: Simple and reliable script to clear all cache entries.

```bash
# Clear all cache (with confirmation)
./scripts/clear-cache-simple.sh

# Clear all cache (force, no confirmation)
./scripts/clear-cache-simple.sh --force
./scripts/clear-cache-simple.sh -f
```

**Features**:

- Simple and reliable
- Shows cache statistics before cleanup
- Confirmation prompt (unless --force)
- Clear success/failure feedback

### 2. clear-cache.sh (Advanced)

**Purpose**: Full-featured cache cleanup with advanced options.

```bash
# Interactive cleanup with statistics
./scripts/clear-cache.sh

# Force cleanup without confirmation
./scripts/clear-cache.sh --force

# Show statistics only (no cleanup)
./scripts/clear-cache.sh --stats-only

# Force cleanup and compact database
./scripts/clear-cache.sh --force --compact

# Show help
./scripts/clear-cache.sh --help
```

**Features**:

- Detailed cache statistics
- Database compaction option
- Environment variable configuration
- Stats-only mode
- Comprehensive error handling

### 3. manage-cache.sh (Selective)

**Purpose**: Selective cache management for specific hosts.

```bash
# List all cached hosts
./scripts/manage-cache.sh --list

# Clear cache for specific host
./scripts/manage-cache.sh server1.example.com

# Clear cache for multiple hosts
./scripts/manage-cache.sh server1 server2 server3

# Force clear specific host
./scripts/manage-cache.sh --force server1.example.com

# Clear all cache
./scripts/manage-cache.sh --all

# Show help
./scripts/manage-cache.sh --help
```

**Features**:

- List cached hosts
- Selective host cleanup
- Bulk host operations
- Force mode for automation

## Configuration

All scripts use the MongoDB configuration from `ansible.cfg`:

```ini
fact_caching_connection = mongodb://localhost:27017/ansible
```

### Environment Variables (clear-cache.sh only)

```bash
# Custom MongoDB settings
export MONGODB_HOST=remote-mongo
export MONGODB_PORT=27017
export MONGODB_DATABASE=ansible_prod
export MONGODB_COLLECTION=cache

./scripts/clear-cache.sh
```

## Usage Examples

### Development Workflow

```bash
# 1. Check what's in cache
./scripts/manage-cache.sh --list

# 2. Clear cache for development host
./scripts/manage-cache.sh localhost

# 3. Run discovery again
cd playbooks
ansible-playbook discovery.yaml -i "localhost," -e debug=true
```

### Production Maintenance

```bash
# 1. Show cache statistics
./scripts/clear-cache.sh --stats-only

# 2. Clear all cache and compact database
./scripts/clear-cache.sh --force --compact

# 3. Rebuild cache for all production hosts
cd playbooks
ansible-playbook discovery.yaml -i production
```

### Selective Cleanup

```bash
# List all cached hosts
./scripts/manage-cache.sh --list

# Clear cache for specific problematic hosts
./scripts/manage-cache.sh --force server1.prod server2.prod

# Rebuild cache for those hosts only
cd playbooks
ansible-playbook discovery.yaml -l "server1.prod,server2.prod"
```

### Automation Integration

```bash
#!/bin/bash
# Example: Clear cache before daily discovery run

# Clear all cache silently
./scripts/clear-cache-simple.sh --force

# Run full discovery
cd playbooks
ansible-playbook discovery.yaml -i production

# Check results
./scripts/manage-cache.sh --list | wc -l
```

## Troubleshooting

### MongoDB Connection Issues

```bash
# Test MongoDB connection manually
mongosh mongodb://localhost:27017/ansible --eval "db.runCommand({ping: 1})"

# Check if MongoDB is running
systemctl status mongod
# or
docker ps | grep mongo
```

### Permission Issues

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Check script permissions
ls -la scripts/
```

### Cache Location Verification

```bash
# Connect to MongoDB and inspect
mongosh ansible

# List collections
show collections

# Count cache entries
db.cache.countDocuments()

# Show sample entries
db.cache.find({}, {_id: 1}).limit(5)
```

### Script Debugging

```bash
# Enable bash debugging
bash -x ./scripts/clear-cache-simple.sh

# Check MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

## Best Practices

### Regular Maintenance

1. **Daily**: Use selective cleanup for problem hosts
2. **Weekly**: Clear all cache and rebuild
3. **Monthly**: Use database compaction option

### Development

1. **Use simple script** for quick cache clearing
2. **Use selective script** for testing specific hosts
3. **Check cache statistics** before major changes

### Production

1. **Always use --stats-only first** to assess impact
2. **Backup MongoDB** before major cache operations
3. **Use --force in automation** scripts only
4. **Monitor cache growth** with statistics

### Performance Tips

1. **Compact database** monthly in production
2. **Clear cache** before bulk discovery operations
3. **Use selective cleanup** instead of full clear when possible
4. **Monitor MongoDB disk usage** regularly

## Integration with Discovery System

### Cache Rebuild After Cleanup

```bash
# Full cache rebuild
./scripts/clear-cache-simple.sh --force
cd playbooks
ansible-playbook discovery.yaml

# Selective rebuild
./scripts/manage-cache.sh server1 server2
cd playbooks
ansible-playbook discovery.yaml -l "server1,server2"
```

### Verification

```bash
# Check cache was rebuilt
./scripts/manage-cache.sh --list

# Verify specific host data
mongosh ansible --eval "db.cache.findOne({_id: 'ansible_factsserver1.example.com'})"
```

## Security Considerations

### MongoDB Access

- Scripts assume local MongoDB access
- No authentication configured by default
- Use MongoDB authentication in production

### Script Security

- Scripts use `set -euo pipefail` for safety
- Input validation for hostnames
- Confirmation prompts for destructive operations

### Network Security

- MongoDB connection is local by default
- Configure firewall rules for remote MongoDB
- Use TLS for remote connections in production
