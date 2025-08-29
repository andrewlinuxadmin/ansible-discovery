#!/bin/bash

# Selective MongoDB Cache Cleanup Script for Ansible Discovery
# This script can clear cache for specific hosts or all hosts

set -euo pipefail

# Configuration
MONGODB_CONNECTION="mongodb://localhost:27017/ansible"
COLLECTION="cache"

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS] [HOSTNAME...]

Selective MongoDB Cache Cleanup for Ansible Discovery

OPTIONS:
    -l, --list          List all cached hosts
    -a, --all           Clear all cache entries (same as clear-cache-simple.sh)
    -f, --force         Skip confirmation prompt
    -h, --help          Show this help message

ARGUMENTS:
    HOSTNAME...         One or more hostnames to clear from cache

EXAMPLES:
    $0 -l                           # List all cached hosts
    $0 server1.example.com          # Clear cache for specific host
    $0 server1 server2 server3      # Clear cache for multiple hosts
    $0 -f server1.example.com       # Force clear without confirmation
    $0 -a                           # Clear all cache
    $0 --all --force                # Force clear all cache

EOF
}

check_mongodb() {
    if ! command -v mongosh &> /dev/null; then
        echo "ERROR: mongosh command not found. Please install MongoDB Shell."
        exit 1
    fi

    if ! mongosh --quiet --eval "db.runCommand({ping: 1})" "$MONGODB_CONNECTION" &> /dev/null; then
        echo "ERROR: Cannot connect to MongoDB at $MONGODB_CONNECTION"
        exit 1
    fi
}

list_cached_hosts() {
    echo "Cached hosts in MongoDB:"
    echo "========================"
    
    mongosh --quiet --eval "
        db.$COLLECTION.find({}, {_id: 1}).sort({_id: 1}).forEach(function(doc) {
            var hostname = doc._id.replace('ansible_facts', '');
            print(hostname);
        });
    " "$MONGODB_CONNECTION" 2>/dev/null || echo "No cached hosts found"
}

clear_all_cache() {
    local force_mode="$1"
    
    cache_count=$(mongosh --quiet --eval "db.$COLLECTION.countDocuments()" "$MONGODB_CONNECTION" 2>/dev/null || echo "0")
    
    if [ "$cache_count" -eq 0 ]; then
        echo "Cache is already empty."
        return 0
    fi
    
    echo "Found $cache_count cache entries to delete."
    
    if [ "$force_mode" != "true" ]; then
        echo
        echo "⚠️  This will DELETE ALL cached facts!"
        read -p "Are you sure? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Operation cancelled."
            return 0
        fi
    fi
    
    echo "Clearing all cache entries..."
    result=$(mongosh --quiet --eval "
        var deleteResult = db.$COLLECTION.deleteMany({});
        print('✅ Deleted ' + deleteResult.deletedCount + ' cache entries');
    " "$MONGODB_CONNECTION" 2>/dev/null)
    
    echo "$result"
}

clear_host_cache() {
    local hostname="$1"
    local force_mode="$2"
    
    # Build the cache key (ansible_facts + hostname)
    local cache_key="ansible_facts${hostname}"
    
    # Check if host exists in cache
    exists=$(mongosh --quiet --eval "db.$COLLECTION.countDocuments({_id: '$cache_key'})" "$MONGODB_CONNECTION" 2>/dev/null || echo "0")
    
    if [ "$exists" -eq 0 ]; then
        echo "❌ Host '$hostname' not found in cache"
        return 1
    fi
    
    if [ "$force_mode" != "true" ]; then
        echo "Found cache entry for host: $hostname"
        read -p "Clear cache for '$hostname'? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            echo "Skipped $hostname"
            return 0
        fi
    fi
    
    # Delete the cache entry
    result=$(mongosh --quiet --eval "
        var deleteResult = db.$COLLECTION.deleteOne({_id: '$cache_key'});
        if (deleteResult.deletedCount > 0) {
            print('✅ Cleared cache for $hostname');
        } else {
            print('❌ Failed to clear cache for $hostname');
        }
    " "$MONGODB_CONNECTION" 2>/dev/null)
    
    echo "$result"
}

# Parse command line arguments
LIST_HOSTS=false
CLEAR_ALL=false
FORCE=false
HOSTNAMES=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -l|--list)
            LIST_HOSTS=true
            shift
            ;;
        -a|--all)
            CLEAR_ALL=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -*)
            echo "ERROR: Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            HOSTNAMES+=("$1")
            shift
            ;;
    esac
done

# Main execution
main() {
    echo "====================================="
    echo "  Selective Cache Cleanup for Ansible"
    echo "====================================="
    echo
    
    check_mongodb
    
    if [ "$LIST_HOSTS" = "true" ]; then
        list_cached_hosts
        exit 0
    fi
    
    if [ "$CLEAR_ALL" = "true" ]; then
        clear_all_cache "$FORCE"
        exit 0
    fi
    
    if [ ${#HOSTNAMES[@]} -eq 0 ]; then
        echo "ERROR: No hostnames provided and no action specified."
        echo
        show_usage
        exit 1
    fi
    
    echo "Selective cache cleanup for ${#HOSTNAMES[@]} host(s):"
    for hostname in "${HOSTNAMES[@]}"; do
        echo "- $hostname"
    done
    echo
    
    success_count=0
    for hostname in "${HOSTNAMES[@]}"; do
        if clear_host_cache "$hostname" "$FORCE"; then
            ((success_count++))
        fi
    done
    
    echo
    echo "Summary: Successfully cleared cache for $success_count/${#HOSTNAMES[@]} hosts"
}

main "$@"
