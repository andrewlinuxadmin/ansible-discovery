#!/bin/bash

# Script para executar testes unitários do módulo process_facts

cd "$(dirname "$0")" || exit

echo "🧪 Executando testes unitários do process_facts..."
echo "=============================================="

# Verificar se o ambiente virtual está ativo
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Ambiente virtual não ativo. Ativando..."
    cd ../../.. || exit
    # shellcheck disable=SC1091 # activate script is in parent directory
    source activate || exit
    cd playbooks/library/tests || exit
fi

# Executar testes com verbose
python3 -m unittest test_process_facts.py -v

# Verificar lint dos testes
echo ""
echo "🔍 Verificando qualidade do código dos testes..."
echo "================================================"
python3 -m flake8 test_process_facts.py

echo ""
echo "✅ Testes concluídos!"
