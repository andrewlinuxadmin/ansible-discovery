#!/bin/bash

# MongoDB Cache Cleanup Script for Ansible Discovery
# This script clears all cached facts from the MongoDB database

set -euo pipefail

# Configuration
MONGODB_HOST="${MONGODB_HOST:-localhost}"
MONGODB_PORT="${MONGODB_PORT:-27017}"
MONGODB_DATABASE="${MONGODB_DATABASE:-ansible}"
MONGODB_COLLECTION="${MONGODB_COLLECTION:-cache}"
MONGODB_CONNECTION="mongodb://${MONGODB_HOST}:${MONGODB_PORT}/${MONGODB_DATABASE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo "=================================="
    echo "  Ansible Discovery Cache Cleanup"
    echo "=================================="
    echo
}

check_mongodb_connection() {
    print_info "Checking MongoDB connection to ${MONGODB_CONNECTION}..."
    
    if ! command -v mongosh &> /dev/null; then
        print_error "mongosh command not found. Please install MongoDB Shell."
        exit 1
    fi
    
    # Test connection
    if ! mongosh --quiet --eval "db.runCommand({ping: 1})" "${MONGODB_CONNECTION}" &> /dev/null; then
        print_error "Cannot connect to MongoDB at ${MONGODB_CONNECTION}"
        print_error "Please ensure MongoDB is running and accessible."
        exit 1
    fi
    
    print_success "MongoDB connection successful"
}

show_cache_stats() {
    print_info "Current cache statistics:"
    
    # Get database stats
    local db_stats
    db_stats=$(mongosh --quiet --eval "
        var stats = db.stats();
        print('Database: ' + stats.db);
        print('Collections: ' + stats.collections);
        print('Data Size: ' + (stats.dataSize / 1024 / 1024).toFixed(2) + ' MB');
        print('Index Size: ' + (stats.indexSize / 1024 / 1024).toFixed(2) + ' MB');
    " "${MONGODB_CONNECTION}" 2>/dev/null || echo "Unable to get database stats")
    
    echo "$db_stats"
    echo
    
    # Get cache collection stats
    local cache_count
    cache_count=$(mongosh --quiet --eval "db.${MONGODB_COLLECTION}.countDocuments()" "${MONGODB_CONNECTION}" 2>/dev/null || echo "0")
    print_info "Cache entries: ${cache_count}"
    
    if [ "$cache_count" -gt 0 ]; then
        print_info "Sample cache entries:"
        mongosh --quiet --eval "
            db.${MONGODB_COLLECTION}.find({}, {_id: 1}).limit(5).forEach(function(doc) {
                print('  - ' + doc._id);
            });
        " "${MONGODB_CONNECTION}" 2>/dev/null || print_warning "Unable to list cache entries"
    fi
    echo
}

confirm_cleanup() {
    if [ "${FORCE:-false}" = "true" ]; then
        print_warning "Force mode enabled - skipping confirmation"
        return 0
    fi
    
    print_warning "This will DELETE ALL cached facts from the MongoDB database!"
    print_warning "Database: ${MONGODB_DATABASE}"
    print_warning "Collection: ${MONGODB_COLLECTION}"
    echo
    
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Operation cancelled by user."
        exit 0
    fi
}

cleanup_cache() {
    print_info "Starting cache cleanup..."
    
    # Count documents before deletion
    local count_before
    count_before=$(mongosh --quiet --eval "db.${MONGODB_COLLECTION}.countDocuments()" "${MONGODB_CONNECTION}" 2>/dev/null || echo "0")
    print_info "Documents to delete: ${count_before}"
    
    if [ "$count_before" -eq 0 ]; then
        print_success "Cache is already empty - nothing to delete"
        return 0
    fi
    
    # Perform the cleanup
    print_info "Dropping collection ${MONGODB_COLLECTION}..."
    
    local result
    result=$(mongosh --quiet --eval "
        var result = db.${MONGODB_COLLECTION}.drop();
        if (result) {
            print('SUCCESS: Collection dropped');
        } else {
            print('WARNING: Collection may not exist or could not be dropped');
        }
    " "${MONGODB_CONNECTION}" 2>/dev/null)
    
    echo "$result"
    
    # Verify cleanup
    local count_after
    count_after=$(mongosh --quiet --eval "db.${MONGODB_COLLECTION}.countDocuments()" "${MONGODB_CONNECTION}" 2>/dev/null || echo "0")
    
    if [ "$count_after" -eq 0 ]; then
        print_success "Cache cleanup completed successfully!"
        print_success "Deleted ${count_before} cache entries"
    else
        print_error "Cache cleanup may have failed - ${count_after} entries remain"
        exit 1
    fi
}

compact_database() {
    if [ "${COMPACT:-false}" = "true" ]; then
        print_info "Compacting database to reclaim disk space..."
        
        mongosh --quiet --eval "
            var result = db.runCommand({compact: '${MONGODB_COLLECTION}'});
            if (result.ok) {
                print('Database compaction completed');
            } else {
                print('Database compaction failed: ' + result.errmsg);
            }
        " "${MONGODB_CONNECTION}" 2>/dev/null || print_warning "Database compaction failed"
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

MongoDB Cache Cleanup Script for Ansible Discovery

OPTIONS:
    -f, --force         Skip confirmation prompt
    -c, --compact       Compact database after cleanup
    -s, --stats-only    Show cache statistics only (no cleanup)
    -h, --help          Show this help message

ENVIRONMENT VARIABLES:
    MONGODB_HOST        MongoDB host (default: localhost)
    MONGODB_PORT        MongoDB port (default: 27017)
    MONGODB_DATABASE    MongoDB database (default: ansible)
    MONGODB_COLLECTION  MongoDB collection (default: cache)

EXAMPLES:
    $0                  # Interactive cleanup
    $0 -f               # Force cleanup without confirmation
    $0 -f -c            # Force cleanup and compact database
    $0 -s               # Show statistics only
    
    # Use custom MongoDB settings
    MONGODB_HOST=remote-mongo $0 -f
    MONGODB_DATABASE=ansible_prod $0 -s

EOF
}

# Parse command line arguments
FORCE=false
COMPACT=false
STATS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -c|--compact)
            COMPACT=true
            shift
            ;;
        -s|--stats-only)
            STATS_ONLY=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_header
    
    check_mongodb_connection
    
    show_cache_stats
    
    if [ "${STATS_ONLY}" = "true" ]; then
        print_info "Stats-only mode - exiting without cleanup"
        exit 0
    fi
    
    confirm_cleanup
    
    cleanup_cache
    
    compact_database
    
    echo
    print_success "MongoDB cache cleanup completed!"
    print_info "You can now run ansible-playbook to rebuild the cache"
}

# Execute main function
main "$@"
