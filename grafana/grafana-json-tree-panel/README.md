# JSON Tree Panel for Grafana

A Grafana panel plugin that displays JSON data in an interactive, expandable tree view.

## Features

- 🌳 **Interactive Tree View**: Click to expand/collapse JSON nodes
- 🎨 **Syntax Highlighting**: Color-coded values by data type
- ⚙️ **Configurable**: Auto-expand levels, string length limits
- 📱 **Responsive**: Works on different screen sizes
- 🔍 **Data Type Indicators**: Shows data types for each value

## Installation

### Development Setup

1. Clone this repository into your Grafana plugins directory:
```bash
cd /var/lib/grafana/plugins  # or your custom plugins directory
git clone https://github.com/andrewlinuxadmin/ansible-discovery
cd ansible-discovery/grafana-json-tree-panel
```

2. Install dependencies:
```bash
npm install
```

3. Build the plugin:
```bash
npm run build
```

4. Restart Grafana server

### Production Installation

1. Download the plugin zip file
2. Extract to your Grafana plugins directory
3. Restart Grafana server

## Usage

1. **Add Panel**: Create a new panel and select "JSON Tree Panel"

2. **Configure Data Source**: 
   - Redis with RedisJSON: `JSON.GET your_key '$'`
   - HTTP API: Any endpoint returning JSON
   - MongoDB: Query returning JSON documents

3. **Panel Options**:
   - **Show data types**: Display type indicators next to values
   - **Auto-expand levels**: Number of tree levels to expand automatically
   - **Max string preview length**: Limit for string value previews

## Data Source Examples

### Redis with RedisJSON
```bash
# Query
JSON.GET ansible_facts_localhost '$'

# Example result structure
{
  "host_info": {
    "hostname": "localhost",
    "os_family": "RedHat",
    "distribution": "Fedora"
  },
  "ansible_facts": {
    "ansible_hostname": "localhost",
    "ansible_os_family": "RedHat"
  },
  "stats": {
    "last_updated": "1757093867"
  }
}
```

### HTTP API
```bash
# Configure HTTP data source pointing to:
http://your-api/hosts/localhost/facts

# Or any REST API returning JSON
```

## Color Scheme

- **Keys**: Blue
- **Strings**: Green  
- **Numbers**: Yellow
- **Booleans**: Orange
- **Null values**: Gray (italic)
- **Objects/Arrays**: Default text color with expand/collapse icons

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Development

```bash
# Watch mode for development
npm run dev

# Run tests
npm run test

# Build for production
npm run build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

Apache 2.0 License - see LICENSE file for details

## Support

- 📧 Email: andre.carlos@redhat.com
- 🐛 Issues: [GitHub Issues](https://github.com/andrewlinuxadmin/ansible-discovery/issues)
- 📖 Documentation: [Project Wiki](https://github.com/andrewlinuxadmin/ansible-discovery/wiki)
