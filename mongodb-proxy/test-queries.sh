#!/bin/bash

# Script para testar todas as consultas MongoDB e identificar problemas
# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8000/query"
FAILED_QUERIES=()
CORRECTED_QUERIES=()

echo -e "${BLUE}🔍 Testando todas as consultas MongoDB...${NC}\n"

# Função para testar consulta
test_query() {
    local name="$1"
    local query="$2"
    local expected_fields="$3"
    
    echo -e "${YELLOW}Testando:${NC} $name"
    
    # Executar consulta
    result=$(curl -s -X POST -H "Content-Type: application/json" -d "$query" "$API_URL")
    
    # Verificar se há erro
    if echo "$result" | grep -q "error"; then
        echo -e "${RED}❌ ERRO:${NC} $result"
        FAILED_QUERIES+=("$name")
        return 1
    fi
    
    # Verificar se retornou array vazio
    if [ "$result" = "[]" ]; then
        echo -e "${RED}❌ VAZIO:${NC} Nenhum resultado retornado"
        FAILED_QUERIES+=("$name")
        return 1
    fi
    
    # Mostrar primeiro resultado
    first_result=$(echo "$result" | jq '.[0] // empty' 2>/dev/null)
    if [ -n "$first_result" ]; then
        echo -e "${GREEN}✅ OK:${NC} $(echo "$first_result" | jq -c .)"
    else
        echo -e "${RED}❌ FORMATO:${NC} Resultado inválido"
        FAILED_QUERIES+=("$name")
        return 1
    fi
    
    echo ""
    return 0
}

# ========================================
# 🖥️ INFORMAÇÕES DE SISTEMA
# ========================================

echo -e "${BLUE}=== 🖥️ Informações de Sistema ===${NC}"

# 1. Lista de todos os hosts descobertos
test_query "Lista de hosts" \
'{"pipeline":[{"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "_id": 0}}, {"$sort": {"hostname": 1}}]}'

# 2. Hosts com informações de CPU (CORRIGIDA)
test_query "Informações de CPU" \
'{"pipeline":[{"$match": {"data.ansible_processor_count": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "cpu_count": "$data.ansible_processor_count", "cpu_model": {"$arrayElemAt": ["$data.ansible_processor", 2]}, "_id": 0}}]}'

# 3. Distribuições Linux e versões
test_query "Distribuições Linux" \
'{"pipeline":[{"$match": {"data.ansible_distribution": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "os": "$data.ansible_distribution", "version": "$data.ansible_distribution_version", "_id": 0}}, {"$sort": {"os": 1, "version": 1}}]}'

# 4. Memória total por host
test_query "Memória total" \
'{"pipeline":[{"$match": {"data.ansible_memtotal_mb": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "memory_gb": {"$round": [{"$divide": ["$data.ansible_memtotal_mb", 1024]}, 2]}, "_id": 0}}, {"$sort": {"memory_gb": -1}}]}'

# 5. Uptime dos servidores
test_query "Uptime dos servidores" \
'{"pipeline":[{"$match": {"data.ansible_uptime_seconds": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "uptime_days": {"$round": [{"$divide": ["$data.ansible_uptime_seconds", 86400]}, 1]}, "_id": 0}}, {"$sort": {"uptime_days": -1}}]}'

# ========================================
# ☕ DESCOBERTA JAVA
# ========================================

echo -e "${BLUE}=== ☕ Descoberta Java ===${NC}"

# 6. Aplicações Java por tipo (CORRIGIDA)
test_query "Aplicações Java por tipo" \
'{"pipeline":[{"$match": {"data.java_processes": {"$exists": true, "$ne": []}}}, {"$unwind": "$data.java_processes"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "app_type": "$data.java_processes.type", "pid": "$data.java_processes.pid", "_id": 0}}, {"$sort": {"app_type": 1, "hostname": 1}}]}'

# 7. Versões do Java instaladas
test_query "Versões do Java" \
'{"pipeline":[{"$match": {"data.java_processes": {"$exists": true, "$ne": []}}}, {"$unwind": "$data.java_processes"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "java_version": "$data.java_processes.java_version", "_id": 0}}, {"$group": {"_id": {"hostname": "$hostname", "java_version": "$java_version"}}}, {"$sort": {"_id.hostname": 1}}]}'

# 8. Aplicações Tomcat com versões (VERIFICAR ESTRUTURA)
test_query "Aplicações Tomcat" \
'{"pipeline":[{"$match": {"data.java_processes": {"$exists": true}}}, {"$unwind": "$data.java_processes"}, {"$match": {"data.java_processes.type": "tomcat"}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "tomcat_version": "$data.java_processes.tomcat_version", "port": "$data.java_processes.port", "_id": 0}}]}'

# 9. Aplicações JBoss/Wildfly (CORRIGIDA)
test_query "Aplicações JBoss/Wildfly" \
'{"pipeline":[{"$match": {"data.java_processes": {"$exists": true}}}, {"$unwind": "$data.java_processes"}, {"$match": {"data.java_processes.type": {"$in": ["jboss", "wildfly"]}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "app_type": "$data.java_processes.type", "version": "$data.java_processes.jboss_info.version", "_id": 0}}]}'

# 10. JARs executáveis descobertos
test_query "JARs executáveis" \
'{"pipeline":[{"$match": {"data.java_processes": {"$exists": true}}}, {"$unwind": "$data.java_processes"}, {"$match": {"data.java_processes.jar_path": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "jar_path": "$data.java_processes.jar_path", "jar_version": "$data.java_processes.jar_version", "_id": 0}}]}'

# ========================================
# 🌐 SERVIDORES WEB
# ========================================

echo -e "${BLUE}=== 🌐 Servidores Web ===${NC}"

# 11. Servidores Apache descobertos (VERIFICAR ESTRUTURA)
test_query "Servidores Apache" \
'{"pipeline":[{"$match": {"data.apache_processes": {"$exists": true, "$ne": []}}}, {"$unwind": "$data.apache_processes"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "apache_version": "$data.apache_processes.version", "config_file": "$data.apache_processes.config_file", "_id": 0}}]}'

# 12. Virtual Hosts do Apache
test_query "Virtual Hosts Apache" \
'{"pipeline":[{"$match": {"data.apache_processes": {"$exists": true}}}, {"$unwind": "$data.apache_processes"}, {"$unwind": "$data.apache_processes.virtual_hosts"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "server_name": "$data.apache_processes.virtual_hosts.ServerName", "document_root": "$data.apache_processes.virtual_hosts.DocumentRoot", "_id": 0}}]}'

# 13. Servidores NGINX
test_query "Servidores NGINX" \
'{"pipeline":[{"$match": {"data.nginx_processes": {"$exists": true, "$ne": []}}}, {"$unwind": "$data.nginx_processes"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "nginx_version": "$data.nginx_processes.version", "config_file": "$data.nginx_processes.config_file", "_id": 0}}]}'

# 14. Configurações PHP
test_query "Configurações PHP" \
'{"pipeline":[{"$match": {"data.php_processes": {"$exists": true, "$ne": []}}}, {"$unwind": "$data.php_processes"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "php_version": "$data.php_processes.version", "php_ini": "$data.php_processes.config_files", "_id": 0}}]}'

# ========================================
# 🔌 REDE E PORTAS
# ========================================

echo -e "${BLUE}=== 🔌 Rede e Portas ===${NC}"

# 15. Portas abertas por serviço (VERIFICAR CAMPO)
test_query "Portas abertas" \
'{"pipeline":[{"$match": {"data.listening_ports": {"$exists": true, "$ne": []}}}, {"$unwind": "$data.listening_ports"}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "port": "$data.listening_ports.port", "protocol": "$data.listening_ports.protocol", "service": "$data.listening_ports.name", "_id": 0}}, {"$sort": {"port": 1}}]}'

# 16. Serviços web por porta
test_query "Serviços web por porta" \
'{"pipeline":[{"$match": {"data.listening_ports": {"$exists": true}}}, {"$unwind": "$data.listening_ports"}, {"$match": {"data.listening_ports.port": {"$in": [80, 8080, 443, 8443, 8000, 9000]}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "port": "$data.listening_ports.port", "protocol": "$data.listening_ports.protocol", "_id": 0}}]}'

# ========================================
# 📦 PACOTES E SERVIÇOS  
# ========================================

echo -e "${BLUE}=== 📦 Pacotes e Serviços ===${NC}"

# 17. Serviços ativos no sistema (VERIFICAR ESTRUTURA)
test_query "Serviços ativos" \
'{"pipeline":[{"$match": {"data.services": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "active_services": {"$filter": {"input": {"$objectToArray": "$data.services"}, "cond": {"$eq": ["$$this.v.state", "running"]}}}, "_id": 0}}, {"$unwind": "$active_services"}, {"$project": {"hostname": 1, "service_name": "$active_services.k", "service_state": "$active_services.v.state"}}]}'

# 18. Pacotes críticos instalados
test_query "Pacotes críticos" \
'{"pipeline":[{"$match": {"data.packages": {"$exists": true}}}, {"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "critical_packages": {"$filter": {"input": {"$objectToArray": "$data.packages"}, "cond": {"$in": ["$$this.k", ["httpd", "nginx", "tomcat", "java", "mysql", "postgresql", "docker", "podman"]]}}}, "_id": 0}}, {"$unwind": "$critical_packages"}, {"$project": {"hostname": 1, "package": "$critical_packages.k", "version": "$critical_packages.v"}}]}'

# ========================================
# 📊 ANÁLISES AGREGADAS
# ========================================

echo -e "${BLUE}=== 📊 Análises Agregadas ===${NC}"

# 19. Resumo de infraestrutura por host
test_query "Resumo de infraestrutura" \
'{"pipeline":[{"$project": {"hostname": {"$replaceAll": {"input": "$_id", "find": "ansible_facts", "replacement": ""}}, "os": "$data.ansible_distribution", "java_apps": {"$size": {"$ifNull": ["$data.java_processes", []]}}, "web_servers": {"$add": [{"$size": {"$ifNull": ["$data.apache_processes", []]}}, {"$size": {"$ifNull": ["$data.nginx_processes", []]}}]}, "open_ports": {"$size": {"$ifNull": ["$data.listening_ports", []]}}, "_id": 0}}, {"$sort": {"hostname": 1}}]}'

# 20. Estatísticas globais do ambiente
test_query "Estatísticas globais" \
'{"pipeline":[{"$group": {"_id": null, "total_hosts": {"$sum": 1}, "java_hosts": {"$sum": {"$cond": [{"$gt": [{"$size": {"$ifNull": ["$data.java_processes", []]}}, 0]}, 1, 0]}}, "web_hosts": {"$sum": {"$cond": [{"$or": [{"$gt": [{"$size": {"$ifNull": ["$data.apache_processes", []]}}, 0]}, {"$gt": [{"$size": {"$ifNull": ["$data.nginx_processes", []]}}, 0]}]}, 1, 0]}}, "avg_memory_gb": {"$avg": {"$divide": [{"$ifNull": ["$data.ansible_memtotal_mb", 0]}, 1024]}}}}, {"$project": {"_id": 0, "total_hosts": 1, "java_hosts": 1, "web_hosts": 1, "avg_memory_gb": {"$round": ["$avg_memory_gb", 2]}}}]}'

# ========================================
# RELATÓRIO FINAL
# ========================================

echo -e "\n${BLUE}===========================================${NC}"
echo -e "${BLUE}📊 RELATÓRIO FINAL${NC}"
echo -e "${BLUE}===========================================${NC}\n"

total_queries=20
failed_count=${#FAILED_QUERIES[@]}
success_count=$((total_queries - failed_count))

echo -e "${GREEN}✅ Consultas funcionando:${NC} $success_count/$total_queries"
echo -e "${RED}❌ Consultas com problema:${NC} $failed_count/$total_queries"

if [ $failed_count -gt 0 ]; then
    echo -e "\n${RED}Consultas que precisam de correção:${NC}"
    for query in "${FAILED_QUERIES[@]}"; do
        echo -e "${RED}  • $query${NC}"
    done
fi

echo -e "\n${YELLOW}💡 Próximos passos:${NC}"
echo "1. Investigar estrutura real dos dados para consultas que falharam"
echo "2. Corrigir campos inexistentes ou com nomes diferentes"
echo "3. Adaptar consultas para estrutura atual dos dados"
echo "4. Testar novamente após correções"

echo -e "\n${BLUE}Script concluído!${NC}"
