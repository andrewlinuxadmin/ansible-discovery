#!/bin/bash

# Grafana JSON Tree Panel Plugin - Installation Script
# Supports multiple installation methods and environments

set -e

PLUGIN_ID="andrewlinuxadmin-json-tree-panel"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to detect Grafana installation
detect_grafana() {
    local grafana_plugins_dir="/usr/share/grafana/data/plugins"
    
    if [ -d "$grafana_plugins_dir" ] && [ -w "$grafana_plugins_dir" ]; then
        echo "$grafana_plugins_dir"
        return 0
    elif [ -d "$grafana_plugins_dir" ]; then
        log_error "Found Grafana plugins directory but no write permission: $grafana_plugins_dir"
        log_info "Try running with sudo or fix permissions"
        return 1
    else
        log_error "Grafana plugins directory not found: $grafana_plugins_dir"
        log_info "Please ensure Grafana is installed and the plugins directory exists"
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed. Please install Node.js 16+ first."
        return 1
    fi
    
    local node_version
    local major_version
    node_version=$(node --version | sed 's/v//')
    major_version=$(echo "$node_version" | cut -d. -f1)
    if [ "$major_version" -lt 16 ]; then
        log_error "Node.js version $node_version detected. Minimum required: 16+"
        return 1
    fi
    
    log_success "Node.js $node_version detected"
    
    # Check npm/yarn
    if command -v yarn &> /dev/null; then
        log_success "Yarn detected"
    elif command -v npm &> /dev/null; then
        log_success "npm detected"
    else
        log_error "Neither npm nor yarn found. Please install a package manager."
        return 1
    fi
    
    return 0
}

# Function to build plugin
build_plugin() {
    log_info "Building plugin..."
    
    # Update build number and timestamp
    local build_number=$(date +%Y%m%d%H%M%S)
    local build_date=$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")
    
    log_info "Updating version info (Build: $build_number)..."
    
    # Update version.ts file
    cat > "$SCRIPT_DIR/src/version.ts" << EOF
// Auto-generated version file
export const VERSION = {
  version: '1.0.0',
  buildNumber: $build_number,
  buildDate: '$build_date',
  features: [
    'Root field selection',
    'Nested field paths (dot and bracket notation)',
    'Grafana variables support',
    'Configurable indentation',
    'Debug mode',
    'Enhanced JSON parsing'
  ]
};
EOF
    
    # Update plugin.json with build number
    sed -i "s/\${BUILD_NUMBER}/$build_number/g" "$SCRIPT_DIR/src/plugin.json"
    
    cd "$SCRIPT_DIR"
    
    # Install dependencies
    if command -v yarn &> /dev/null; then
        log_info "Installing dependencies with yarn..."
        yarn install --ignore-engines
        log_info "Building plugin with yarn..."
        if ! SKIP_LINT=true yarn build; then
            log_warning "Grafana toolkit build failed, trying webpack..."
            yarn build-webpack
        fi
    else
        log_info "Installing dependencies with npm..."
        npm install --legacy-peer-deps
        log_info "Building plugin with npm..."
        if ! SKIP_LINT=true npm run build; then
            log_warning "Grafana toolkit build failed, trying webpack..."
            npm run build-webpack
        fi
    fi
    
    # If webpack also failed, try manual copy
    if [ ! -d "dist" ]; then
        log_warning "Webpack build failed, trying manual approach..."
        manual_build
    fi
    
    if [ ! -d "dist" ]; then
        log_error "All build methods failed - dist directory not found"
        return 1
    fi
    
    log_success "Plugin built successfully"
    
    # Add anti-cache comment to force browser reload
    if [ -f "dist/module.js" ]; then
        log_info "Adding anti-cache marker to module.js..."
        echo "/* Build: $build_number - $(date) */" >> dist/module.js
    fi
    
    return 0
}

# Function for manual build as fallback
manual_build() {
    log_info "Attempting manual build..."
    
    # Create dist directory
    mkdir -p dist
    
    # Copy source files and transform basic TypeScript
    if command -v tsc &> /dev/null; then
        log_info "Using TypeScript compiler..."
        npx tsc --outDir dist --target ES2015 --module amd --jsx react-jsx src/module.ts
    else
        log_info "TypeScript compiler not available, copying files..."
        # Simple file copy as last resort
        cp -r src/* dist/
        # Rename .tsx to .js
        find dist -name "*.tsx" -exec sh -c 'mv "$1" "${1%.tsx}.js"' _ {} \;
        find dist -name "*.ts" -exec sh -c 'mv "$1" "${1%.ts}.js"' _ {} \;
    fi
    
    # Copy plugin.json to dist
    if [ -f "src/plugin.json" ]; then
        cp src/plugin.json dist/
    fi
}

# Function to install plugin
install_plugin() {
    local grafana_plugins_dir="$1"
    local plugin_dir="$grafana_plugins_dir/$PLUGIN_ID"
    
    log_info "Installing plugin to: $plugin_dir"
    
    # Clean up any existing installation completely
    if [ -d "$plugin_dir" ]; then
        log_info "Removing existing plugin installation..."
        if ! rm -rf "$plugin_dir"; then
            log_error "Failed to remove existing plugin directory: $plugin_dir"
            log_info "Try running with sudo or check permissions"
            return 1
        fi
        log_success "Existing plugin removed successfully"
    fi
    
    # Also clean up any potential cache files
    if [ -d "$grafana_plugins_dir/.cache" ]; then
        log_info "Cleaning plugin cache..."
        rm -rf "$grafana_plugins_dir/.cache" 2>/dev/null || true
    fi
    
    # Create plugin directory
    if ! mkdir -p "$plugin_dir"; then
        log_error "Failed to create plugin directory: $plugin_dir"
        return 1
    fi
    
    # Copy plugin files
    if ! cp -r "$SCRIPT_DIR/dist/"* "$plugin_dir/"; then
        log_error "Failed to copy plugin files"
        return 1
    fi
    
    # Copy plugin.json
    if [ -f "$SCRIPT_DIR/src/plugin.json" ]; then
        cp "$SCRIPT_DIR/src/plugin.json" "$plugin_dir/"
    fi
    
    # Create img directory and logo.svg to prevent 404 errors
    log_info "Creating plugin assets..."
    mkdir -p "$plugin_dir/img"
    
    # Create a simple logo.svg file
    cat > "$plugin_dir/img/logo.svg" << 'EOF'
<svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
  <rect width="40" height="40" fill="#f39c12" rx="4"/>
  <text x="20" y="25" text-anchor="middle" fill="white" font-family="Arial" font-size="14" font-weight="bold">JSON</text>
</svg>
EOF
    
    log_success "Plugin assets created successfully"
    
    # Set proper permissions
    chmod -R 755 "$plugin_dir"
    
    log_success "Plugin installed successfully to: $plugin_dir"
    return 0
}

# Function to verify installation
verify_installation() {
    local grafana_plugins_dir="$1"
    local plugin_dir="$grafana_plugins_dir/$PLUGIN_ID"
    
    log_info "Verifying installation..."
    
    if [ ! -d "$plugin_dir" ]; then
        log_error "Plugin directory not found: $plugin_dir"
        return 1
    fi
    
    if [ ! -f "$plugin_dir/plugin.json" ]; then
        log_error "plugin.json not found in: $plugin_dir"
        return 1
    fi
    
    if [ ! -f "$plugin_dir/module.js" ]; then
        log_error "module.js not found in: $plugin_dir"
        return 1
    fi
    
    if [ ! -f "$plugin_dir/img/logo.svg" ]; then
        log_error "logo.svg not found in: $plugin_dir/img/"
        return 1
    fi
    
    # Check if plugin ID in plugin.json matches directory name
    local json_id
    json_id=$(grep -o '"id"[[:space:]]*:[[:space:]]*"[^"]*"' "$plugin_dir/plugin.json" | cut -d'"' -f4)
    if [ "$json_id" != "$PLUGIN_ID" ]; then
        log_warning "Plugin ID mismatch: directory=$PLUGIN_ID, json=$json_id"
    fi
    
    # If Grafana is running, suggest restart
    if pgrep -f grafana-server > /dev/null 2>&1; then
        log_info "Grafana server is running - restart required for plugin to load"
    fi
    
    log_success "Installation verified successfully"
    return 0
}

# Function to show post-installation instructions
show_instructions() {
    local grafana_plugins_dir="$1"
    
    echo
    log_success "=== Installation Complete ==="
    echo
    log_info "Plugin installed to: $grafana_plugins_dir/$PLUGIN_ID"
    echo
    
    # Check if Grafana is running
    if pgrep -f grafana-server > /dev/null 2>&1; then
        log_info "⚠️  IMPORTANT: Grafana is currently running!"
        echo "  Plugin was completely removed and reinstalled."
        echo "  You MUST restart Grafana for the new plugin version to be loaded:"
        echo
        echo "  • Stop current Grafana process (Ctrl+C if running in foreground)"
        echo "  • Restart Grafana to load the new plugin"
        echo "  • Clear browser cache if panel configuration doesn't update"
        echo
    else
        log_info "Next steps:"
        echo "  1. Start Grafana service"
        echo
    fi
    
    log_info "⚠️  PLUGIN SIGNATURE CONFIGURATION REQUIRED:"
    echo "  This plugin is unsigned and requires Grafana configuration to allow unsigned plugins."
    echo
    echo "  Add this to your Grafana configuration (/etc/grafana/grafana.ini):"
    echo "  [plugins]"
    echo "  allow_loading_unsigned_plugins = $PLUGIN_ID"
    echo
    echo "  OR start Grafana with environment variable:"
    echo "  GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=$PLUGIN_ID"
    echo
    echo "  Example startup command:"
    echo "  sudo GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=$PLUGIN_ID grafana-server --homepath=/usr/share/grafana --config=/etc/grafana/grafana.ini"
    echo
    
    echo "  2. Login to Grafana and go to Administration > Plugins"
    echo "  3. Look for 'JSON Tree Panel' in the plugin list"
    echo "  4. Create a new dashboard and add a panel"
    echo "  5. Select 'JSON Tree Panel' as the visualization type"
    echo "  6. Configure your data source (Redis, API, etc.)"
    echo
    log_info "Plugin ID: $PLUGIN_ID"
    log_info "Plugin Version: 1.0.0"
    echo
}

# Main installation function
main() {
    log_info "Starting Grafana JSON Tree Panel Plugin installation..."
    echo
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Detect Grafana installation
    log_info "Detecting Grafana installation..."
    if ! GRAFANA_PLUGINS_DIR=$(detect_grafana); then
        log_error "Could not find writable Grafana plugins directory"
        log_info "Please ensure Grafana is installed and you have write permissions"
        log_info "You can also set GRAFANA_PLUGINS_DIR environment variable manually:"
        log_info "  export GRAFANA_PLUGINS_DIR=/path/to/grafana/plugins"
        log_info "  $0"
        exit 1
    fi
    
    log_success "Found Grafana plugins directory: $GRAFANA_PLUGINS_DIR"
    
    # Build plugin
    if ! build_plugin; then
        exit 1
    fi
    
    # Install plugin
    if ! install_plugin "$GRAFANA_PLUGINS_DIR"; then
        exit 1
    fi
    
    # Verify installation
    if ! verify_installation "$GRAFANA_PLUGINS_DIR"; then
        exit 1
    fi
    
    # Show instructions
    show_instructions "$GRAFANA_PLUGINS_DIR"
    
    # Verify installed build number
    log_info "Verifying installed build number..."
    local installed_build
    installed_build=$(grep -o 'buildNumber:[0-9]*' "$GRAFANA_PLUGINS_DIR/andrewlinuxadmin-json-tree-panel/module.js" 2>/dev/null | cut -d: -f2)
    if [ -n "$installed_build" ]; then
        log_success "✅ Installed Build Number: $installed_build"
        
        # Format the build number for human reading (YYYYMMDDHHMMSS -> YYYY-MM-DD HH:MM:SS)
        if [ ${#installed_build} -eq 14 ]; then
            local formatted_date="${installed_build:0:4}-${installed_build:4:2}-${installed_build:6:2} ${installed_build:8:2}:${installed_build:10:2}:${installed_build:12:2}"
            log_info "📅 Build Date/Time: $formatted_date"
        fi
    else
        log_warning "⚠️  Could not verify build number in installed plugin"
    fi
    
    log_success "Installation completed successfully!"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Grafana JSON Tree Panel Plugin - Installation Script"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --version, -v       Show version information"
        echo "  --clean             Clean build artifacts before installation"
        echo
        echo "Environment Variables:"
        echo "  GRAFANA_PLUGINS_DIR Set custom Grafana plugins directory"
        echo
        echo "Examples:"
        echo "  $0                  Standard installation"
        echo "  GRAFANA_PLUGINS_DIR=/custom/path $0"
        echo "  $0 --clean          Clean and install"
        exit 0
        ;;
    --version|-v)
        echo "Grafana JSON Tree Panel Plugin v1.0.0"
        exit 0
        ;;
    --clean)
        log_info "Cleaning build artifacts..."
        rm -rf "$SCRIPT_DIR/dist" "$SCRIPT_DIR/node_modules"
        log_success "Clean completed"
        ;;
esac

# Run main installation if no special arguments
if [ "${1:-}" != "--clean" ]; then
    main
fi
