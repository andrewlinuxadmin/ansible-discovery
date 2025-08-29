#!/bin/bash

# Simple MongoDB Cache Cleanup Script for Ansible Discovery
# This script clears all cached facts from the MongoDB database

set -euo pipefail

# Configuration from ansible.cfg
MONGODB_CONNECTION="mongodb://localhost:27017/ansible"
COLLECTION="cache"

echo "=================================="
echo "  Ansible Discovery Cache Cleanup"
echo "=================================="
echo

# Check if mongosh is available
if ! command -v mongosh &> /dev/null; then
    echo "ERROR: mongosh command not found. Please install MongoDB Shell."
    exit 1
fi

# Test MongoDB connection
echo "Checking MongoDB connection..."
if ! mongosh --quiet --eval "db.runCommand({ping: 1})" "$MONGODB_CONNECTION" &> /dev/null; then
    echo "ERROR: Cannot connect to MongoDB at $MONGODB_CONNECTION"
    echo "Please ensure MongoDB is running and accessible."
    exit 1
fi
echo "✓ MongoDB connection successful"
echo

# Show current cache statistics
echo "Current cache statistics:"
cache_count=$(mongosh --quiet --eval "db.$COLLECTION.countDocuments()" "$MONGODB_CONNECTION" 2>/dev/null || echo "0")
echo "Cache entries: $cache_count"

if [ "$cache_count" -gt 0 ]; then
    echo "Sample cache entries:"
    mongosh --quiet --eval "
        db.$COLLECTION.find({}, {_id: 1}).limit(5).forEach(function(doc) {
            print('  - ' + doc._id.replace('ansible_facts', ''));
        });
    " "$MONGODB_CONNECTION" 2>/dev/null || echo "  Unable to list entries"
fi
echo

# Confirmation (unless --force is used)
if [[ "${1:-}" != "--force" && "${1:-}" != "-f" ]]; then
    echo "⚠️  This will DELETE ALL cached facts from the MongoDB database!"
    echo "Database: ansible"
    echo "Collection: $COLLECTION"
    echo
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi
fi

# Perform cleanup
echo "Deleting all cache entries..."
result=$(mongosh --quiet --eval "
    var deleteResult = db.$COLLECTION.deleteMany({});
    print('Deleted ' + deleteResult.deletedCount + ' documents');
" "$MONGODB_CONNECTION" 2>/dev/null || echo "Failed to delete documents")

echo "$result"

# Verify cleanup
final_count=$(mongosh --quiet --eval "db.$COLLECTION.countDocuments()" "$MONGODB_CONNECTION" 2>/dev/null || echo "unknown")
echo "Remaining cache entries: $final_count"
echo

if [ "$final_count" = "0" ]; then
    echo "✅ Cache cleanup completed successfully!"
    echo "You can now run 'ansible-playbook discovery.yaml' to rebuild the cache."
else
    echo "❌ Cache cleanup may have failed - $final_count entries remain"
    exit 1
fi
