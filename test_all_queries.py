#!/usr/bin/env python3
"""
Test All MongoDB Queries from HTML Dashboard
============================================

This script reads the enhanced-queries.html file, extracts all MongoDB queries,
and tests them against the MongoDB proxy API to ensure they work correctly.

Features:
- Extracts queries from HTML dashboard
- Tests all queries against MongoDB proxy API
- Provides detailed reporting with statistics
- Supports different output formats (console, file, JSON)
- Includes API health checks and error handling
- Allows testing specific queries or categories

Usage:
    python test_all_queries.py [OPTIONS]
    
Examples:
    python test_all_queries.py                           # Basic test
    python test_all_queries.py --verbose                 # Detailed output
    python test_all_queries.py --quick                   # Quick test (first 5 queries)
    python test_all_queries.py --category "Java"         # Test only Java queries
    python test_all_queries.py --output report.txt       # Save report to file
    python test_all_queries.py --json --output results.json  # JSON output
"""

import re
import json
import urllib.parse
import requests
import argparse
import sys
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import time


@dataclass
class QueryResult:
    """Represents the result of testing a MongoDB query."""
    name: str
    query: List[Dict[str, Any]]
    success: bool
    error_message: str = ""
    response_data: Any = None
    execution_time: float = 0.0
    document_count: int = 0
    category: str = "Unknown"


class MongoDBQueryTester:
    """Tests MongoDB queries extracted from HTML dashboard."""
    
    def __init__(self, api_host: str = "localhost", api_port: int = 45678, verbose: bool = False):
        self.api_base_url = f"http://{api_host}:{api_port}"
        self.verbose = verbose
        self.session = requests.Session()
        self.session.timeout = 30
        self.categories = {
            "Sistema": ["Lista de todos os hosts", "Recursos de Hardware", "Sistema Operacional", "Portas Abertas"],
            "Java": ["Processos Java", "Servidores Tomcat", "Servidores JBoss", "JARs Executáveis", "Versões Java"],
            "Web": ["Servidores Apache", "Virtual Hosts Apache", "Servidores NGINX", "Configurações PHP"],
            "Rede": ["Portas abertas", "Serviços web por porta", "Uso de Portas"],
            "Serviços": ["Serviços Mais Comuns", "Bancos de Dados"],
            "Segurança": ["Status SELinux", "Portas de Risco", "Análise de Uptime"],
            "Performance": ["Classificação de Recursos", "Distribuição por SO"],
            "Arquitetura": ["Análise de Stack", "Pacotes de Desenvolvimento"],
            "Análises": ["Análise de Capacidade", "Resumo de Hosts por Tipo"]
        }
        
    def get_category_for_query(self, query_name: str) -> str:
        """Determine the category of a query based on its name."""
        for category, keywords in self.categories.items():
            if any(keyword.lower() in query_name.lower() for keyword in keywords):
                return category
        return "Unknown"
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        if self.verbose or level in ["ERROR", "SUCCESS", "WARNING"]:
            print(f"[{timestamp}] {level}: {message}")
        
    def check_api_health(self) -> bool:
        """Check if MongoDB proxy API is available."""
        try:
            self.log("🔍 Checking MongoDB proxy API health...")
            response = self.session.get(f"{self.api_base_url}/healthz")
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'ok':
                    self.log("✅ MongoDB Proxy API is healthy", "SUCCESS")
                    return True
            self.log(f"❌ API health check failed: HTTP {response.status_code}", "ERROR")
            return False
        except requests.exceptions.ConnectionError:
            self.log(f"❌ Cannot connect to MongoDB proxy at {self.api_base_url}", "ERROR")
            self.log("💡 Make sure MongoDB proxy is running:", "INFO")
            self.log("   cd mongodb-proxy && python mongodb-proxy.py", "INFO")
            return False
        except Exception as e:
            self.log(f"❌ API health check failed: {e}", "ERROR")
            return False
    
    def extract_queries_from_html(self, html_file: str) -> List[Tuple[str, List[Dict]]]:
        """Extract MongoDB queries from HTML file."""
        html_path = Path(html_file)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file}")
        
        content = html_path.read_text(encoding='utf-8')
        queries = []
        
        # Pattern to match href attributes with mongodb_filter parameters
        # This pattern matches both encoded and non-encoded href attributes
        patterns = [
            r'href="[^"]*var-mongodb_filter=([^"]*?)"[^>]*>([^<]+)</a>',  # Standard pattern
            r'href=\\"[^"]*var-mongodb_filter=([^"]*?)\\"[^>]*>([^<]+)</a>',  # Escaped quotes
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            self.log(f"Pattern '{pattern[:30]}...' found {len(matches)} matches")
            
            for encoded_query, link_text in matches:
                try:
                    # URL decode the query
                    decoded_query = urllib.parse.unquote(encoded_query)
                    
                    # Replace HTML entities
                    decoded_query = decoded_query.replace('&quot;', '"').replace('&amp;', '&')
                    
                    # Parse JSON
                    query_json = json.loads(decoded_query)
                    
                    queries.append((link_text.strip(), query_json))
                    self.log(f"✅ Extracted query: {link_text.strip()}")
                    
                except json.JSONDecodeError as e:
                    self.log(f"❌ JSON decode error for '{link_text}': {e}", "ERROR")
                    continue
                except Exception as e:
                    self.log(f"❌ Failed to parse query for '{link_text}': {e}", "ERROR")
                    continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for name, query in queries:
            query_str = json.dumps(query, sort_keys=True)
            if query_str not in seen:
                seen.add(query_str)
                unique_queries.append((name, query))
            else:
                self.log(f"⚠️  Duplicate query removed: {name}", "WARNING")
        
        self.log(f"Total unique queries extracted: {len(unique_queries)}")
        
        if not unique_queries:
            self.log("⚠️  No valid queries found in HTML file", "WARNING")
        
        return unique_queries
    
    def test_query(self, name: str, query: List[Dict]) -> QueryResult:
        """Test a single MongoDB query."""
        self.log(f"Testing query: {name}")
        
        start_time = time.time()
        category = self.get_category_for_query(name)
        result = QueryResult(name=name, query=query, success=False, category=category)
        
        try:
            # Prepare request payload
            payload = {
                "collection": "cache",
                "pipeline": query
            }
            
            # Make request to MongoDB proxy
            response = self.session.post(
                f"{self.api_base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            if response.status_code == 200:
                response_data = response.json()
                result.success = True
                result.response_data = response_data
                
                if isinstance(response_data, list):
                    result.document_count = len(response_data)
                elif isinstance(response_data, dict) and 'data' in response_data:
                    result.document_count = len(response_data['data']) if isinstance(response_data['data'], list) else 1
                else:
                    result.document_count = 1 if response_data else 0
                
                self.log(f"✅ {name}: {result.document_count} docs, {execution_time:.2f}s [{category}]", "SUCCESS")
                
            else:
                result.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                self.log(f"❌ {name}: {result.error_message}", "ERROR")
                
        except requests.exceptions.Timeout:
            result.error_message = "Request timeout (>30s)"
            result.execution_time = time.time() - start_time
            self.log(f"❌ {name}: Query timeout", "ERROR")
        except requests.exceptions.ConnectionError:
            result.error_message = "Connection error"
            result.execution_time = time.time() - start_time
            self.log(f"❌ {name}: Connection error", "ERROR")
        except Exception as e:
            result.error_message = str(e)
            result.execution_time = time.time() - start_time
            self.log(f"❌ {name}: {result.error_message}", "ERROR")
        
        return result
    
    def test_all_queries(self, html_file: str, category_filter: str = None, quick_test: bool = False) -> List[QueryResult]:
        """Test all queries from HTML file."""
        self.log(f"Starting query testing from {html_file}")
        
        # Check API health first
        if not self.check_api_health():
            self.log("API health check failed, aborting tests", "ERROR")
            return []
        
        # Extract queries
        try:
            queries = self.extract_queries_from_html(html_file)
        except Exception as e:
            self.log(f"Failed to extract queries: {e}", "ERROR")
            return []
        
        if not queries:
            self.log("No queries found in HTML file", "ERROR")
            return []
        
        # Filter by category if specified
        if category_filter:
            original_count = len(queries)
            queries = [(name, query) for name, query in queries
                       if category_filter.lower() in self.get_category_for_query(name).lower()]
            self.log(f"Filtered to {len(queries)} queries (from {original_count}) matching category '{category_filter}'")
        
        # Quick test - only first 5 queries
        if quick_test:
            queries = queries[:5]
            self.log(f"Quick test mode: testing first {len(queries)} queries")
        
        # Test each query
        results = []
        for i, (name, query) in enumerate(queries, 1):
            self.log(f"Progress: {i}/{len(queries)}")
            result = self.test_query(name, query)
            results.append(result)
            
            # Brief pause between requests to avoid overwhelming the API
            time.sleep(0.1)
        
        return results
    
    def generate_report(self, results: List[QueryResult]) -> str:
        """Generate test report."""
        if not results:
            return "No results to report"
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_docs = sum(r.document_count for r in successful)
        avg_time = sum(r.execution_time for r in results) / len(results)
        
        report = []
        report.append("=" * 80)
        report.append("📊 MONGODB QUERY TEST REPORT")
        report.append("=" * 80)
        report.append("")
        report.append("📋 SUMMARY:")
        report.append(f"   • Total Queries: {len(results)}")
        report.append(f"   • ✅ Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        report.append(f"   • ❌ Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        report.append(f"   • 📄 Total Documents: {total_docs}")
        report.append(f"   • ⏱️  Average Time: {avg_time:.2f}s")
        report.append("")
        
        if successful:
            report.append("✅ SUCCESSFUL QUERIES:")
            report.append("-" * 40)
            for result in successful:
                report.append(f"   • {result.name}")
                report.append(f"     └─ {result.document_count} docs, {result.execution_time:.2f}s")
            report.append("")
        
        if failed:
            report.append("❌ FAILED QUERIES:")
            report.append("-" * 40)
            for result in failed:
                report.append(f"   • {result.name}")
                report.append(f"     └─ Error: {result.error_message}")
            report.append("")
        
        # Detailed query analysis
        if self.verbose and successful:
            report.append("🔍 DETAILED RESULTS:")
            report.append("-" * 40)
            for result in successful:
                report.append(f"Query: {result.name}")
                report.append(f"Documents: {result.document_count}")
                report.append(f"Time: {result.execution_time:.2f}s")
                if result.response_data and isinstance(result.response_data, list) and result.response_data:
                    sample = result.response_data[0]
                    if isinstance(sample, dict):
                        fields = list(sample.keys())[:5]  # Show first 5 fields
                        report.append(f"Sample Fields: {', '.join(fields)}")
                report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)

    def generate_json_report(self, results: List[QueryResult]) -> Dict[str, Any]:
        """Generate JSON report."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Group by category
        categories = {}
        for result in results:
            if result.category not in categories:
                categories[result.category] = {"total": 0, "successful": 0, "failed": 0, "documents": 0}
            categories[result.category]["total"] += 1
            if result.success:
                categories[result.category]["successful"] += 1
                categories[result.category]["documents"] += result.document_count
            else:
                categories[result.category]["failed"] += 1
        
        return {
            "summary": {
                "total_queries": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(results) * 100 if results else 0,
                "total_documents": sum(r.document_count for r in successful),
                "average_time": sum(r.execution_time for r in results) / len(results) if results else 0
            },
            "categories": categories,
            "successful_queries": [
                {
                    "name": r.name,
                    "category": r.category,
                    "document_count": r.document_count,
                    "execution_time": r.execution_time
                }
                for r in successful
            ],
            "failed_queries": [
                {
                    "name": r.name,
                    "category": r.category,
                    "error_message": r.error_message,
                    "execution_time": r.execution_time
                }
                for r in failed
            ]
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test MongoDB queries from HTML dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_all_queries.py
  python test_all_queries.py --host localhost --port 45678
  python test_all_queries.py --verbose
  python test_all_queries.py --html custom-queries.html
        """
    )
    
    parser.add_argument(
        '--host',
        default='localhost',
        help='MongoDB proxy API host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=45678,
        help='MongoDB proxy API port (default: 45678)'
    )
    parser.add_argument(
        '--html',
        default='enhanced-queries.html',
        help='HTML file containing queries (default: enhanced-queries.html)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output', '-o',
        help='Save report to file'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test - only test first 5 queries'
    )
    parser.add_argument(
        '--category',
        help='Test only queries from specific category (Java, Web, Sistema, etc.)'
    )
    
    args = parser.parse_args()
    
    # Create tester instance
    tester = MongoDBQueryTester(
        api_host=args.host,
        api_port=args.port,
        verbose=args.verbose
    )
    
    print("🧪 MongoDB Query Testing Tool")
    print("=" * 50)
    print(f"API Endpoint: {tester.api_base_url}")
    print(f"HTML File: {args.html}")
    if args.category:
        print(f"Category Filter: {args.category}")
    if args.quick:
        print("Mode: Quick test (first 5 queries)")
    print(f"Verbose: {args.verbose}")
    print("")
    
    # Test all queries
    results = tester.test_all_queries(
        html_file=args.html,
        category_filter=args.category,
        quick_test=args.quick
    )
    
    if not results:
        print("❌ No queries were tested")
        sys.exit(1)
    
    # Generate report
    if args.json:
        report_data = tester.generate_json_report(results)
        if args.output:
            Path(args.output).write_text(json.dumps(report_data, indent=2), encoding='utf-8')
            print(f"📄 JSON report saved to: {args.output}")
        else:
            print(json.dumps(report_data, indent=2))
    else:
        report = tester.generate_report(results)
        print(report)
        
        # Save report to file if requested
        if args.output:
            Path(args.output).write_text(report, encoding='utf-8')
            print(f"📄 Report saved to: {args.output}")
    
    # Exit with error code if any queries failed
    failed_count = len([r for r in results if not r.success])
    if failed_count > 0:
        print(f"\n⚠️  {failed_count} queries failed")
        sys.exit(1)
    else:
        print(f"\n🎉 All {len(results)} queries passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
