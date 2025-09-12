#!/usr/bin/env python3
"""
MongoDB Dashboard Updater

Este script atualiza o dashboard JSON do Grafana com o conteúdo HTML
das queries MongoDB do arquivo enhanced-queries.html.

Usage:
    python3 update_dashboard.py [--backup] [--dashboard DASHBOARD_FILE] [--html HTML_FILE]
"""

import json
import sys
import os
import argparse
from datetime import datetime


def create_backup(file_path):
    """Cria backup do arquivo original"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        print(f"✅ Backup criado: {backup_path}")
        print(f"   ℹ️  Arquivo ignorado pelo Git (conforme .gitignore)")
        return backup_path
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return None


def read_html_content(html_file):
    """Lê o conteúdo do arquivo HTML"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✅ HTML carregado: {html_file} ({len(content)} chars)")
        return content
    except FileNotFoundError:
        print(f"❌ Arquivo HTML não encontrado: {html_file}")
        return None
    except Exception as e:
        print(f"❌ Erro ao ler HTML: {e}")
        return None


def load_dashboard_json(dashboard_file):
    """Carrega o arquivo JSON do dashboard"""
    try:
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            dashboard = json.load(f)
        print(f"✅ Dashboard carregado: {dashboard_file}")
        return dashboard
    except FileNotFoundError:
        print(f"❌ Arquivo dashboard não encontrado: {dashboard_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Erro de JSON no dashboard: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar dashboard: {e}")
        return None


def find_html_panel(dashboard):
    """Encontra o painel HTML no dashboard"""
    panels = dashboard.get('panels', [])
    
    for panel in panels:
        # Verifica se é um painel de texto/HTML
        if panel.get('type') == 'text':
            options = panel.get('options', {})
            content = options.get('content', '')
            
            # Verifica se contém conteúdo relacionado ao MongoDB
            if 'mongodb' in content.lower() or 'queries' in content.lower() or 'enhanced-queries' in content.lower():
                print(f"✅ Painel HTML encontrado: '{panel.get('title', 'Sem título')}' (ID: {panel.get('id')})")
                return panel
    
    print("❌ Painel HTML não encontrado")
    return None


def update_html_panel(panel, html_content):
    """Atualiza o conteúdo HTML do painel"""
    if 'options' not in panel:
        panel['options'] = {}
    
    # Atualiza o conteúdo HTML
    panel['options']['content'] = html_content
    panel['options']['mode'] = 'html'  # Garantir que está em modo HTML
    
    # Atualiza informações do painel
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if 'title' not in panel or not panel['title']:
        panel['title'] = 'MongoDB Infrastructure Queries'
    
    print(f"✅ Painel HTML atualizado: {len(html_content)} caracteres")
    print(f"   Título: {panel.get('title')}")
    print(f"   Atualizado em: {current_time}")


def save_dashboard(dashboard, dashboard_file):
    """Salva o dashboard atualizado"""
    try:
        # Atualiza o timestamp do dashboard
        dashboard['time']['from'] = 'now-24h'
        dashboard['time']['to'] = 'now'
        dashboard['refresh'] = '1m'
        
        # Incrementa a versão se existir
        if 'version' in dashboard:
            dashboard['version'] += 1
        else:
            dashboard['version'] = 1
            
        with open(dashboard_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Dashboard salvo com sucesso: {dashboard_file}")
        print(f"   Versão: {dashboard.get('version', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar dashboard: {e}")
        return False


def validate_files(*files):
    """Valida se os arquivos existem"""
    for file_path in files:
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não encontrado: {file_path}")
            return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Atualiza dashboard Grafana com queries MongoDB',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python3 update_dashboard.py
    python3 update_dashboard.py --backup
    python3 update_dashboard.py --dashboard custom-dashboard.json --html custom-queries.html
        """
    )
    
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Criar backup do dashboard antes de atualizar'
    )
    
    parser.add_argument(
        '--dashboard',
        default='dashboard-explorer.json',
        help='Arquivo do dashboard Grafana (padrão: dashboard-explorer.json)'
    )
    
    parser.add_argument(
        '--html',
        default='enhanced-queries.html',
        help='Arquivo HTML com as queries (padrão: enhanced-queries.html)'
    )
    
    args = parser.parse_args()
    
    print("🔄 MongoDB Dashboard Updater")
    print("=" * 50)
    print(f"Dashboard: {args.dashboard}")
    print(f"HTML: {args.html}")
    print(f"Backup: {'Sim' if args.backup else 'Não'}")
    print("=" * 50)
    
    # Validar arquivos
    if not validate_files(args.dashboard, args.html):
        sys.exit(1)
    
    # Criar backup se solicitado
    if args.backup:
        backup_path = create_backup(args.dashboard)
        if not backup_path:
            sys.exit(1)
    
    # Carregar arquivos
    html_content = read_html_content(args.html)
    if not html_content:
        sys.exit(1)
    
    dashboard = load_dashboard_json(args.dashboard)
    if not dashboard:
        sys.exit(1)
    
    # Encontrar e atualizar painel HTML
    html_panel = find_html_panel(dashboard)
    if not html_panel:
        print("\n💡 Dica: Certifique-se de que existe um painel de texto no dashboard")
        print("   com conteúdo relacionado ao MongoDB ou queries")
        sys.exit(1)
    
    # Atualizar conteúdo
    update_html_panel(html_panel, html_content)
    
    # Salvar dashboard
    if save_dashboard(dashboard, args.dashboard):
        print("\n🎉 Dashboard atualizado com sucesso!")
        print("\nPróximos passos:")
        print("1. Recarregue o dashboard no Grafana")
        print("2. Verifique se as queries estão funcionando")
        print("3. Teste os links para o MongoDB Proxy")
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
