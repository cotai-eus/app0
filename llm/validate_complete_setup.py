"""
🎯 Validação Completa do Sistema LLM CotAi
============================================

Este script executa uma validação abrangente de todo o sistema LLM
implementado para o CotAi Backend, validando desde a infraestrutura 
até a funcionalidade completa dos serviços de IA.
"""

import asyncio
import sys
import httpx
import json
from pathlib import Path
from datetime import datetime


class LLMSystemValidator:
    """Validador completo do sistema LLM"""
    
    def __init__(self):
        self.results = {
            "infrastructure": {},
            "services": {},
            "models": {},
            "functionality": {},
            "performance": {}
        }
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def log_result(self, category: str, test_name: str, success: bool, details: str = ""):
        """Registra resultado de um teste"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        self.results[category][test_name] = {
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        print(f"{status} {test_name}: {details}")
    
    def validate_infrastructure(self):
        """Valida infraestrutura do sistema LLM"""
        print("\n🏗️  VALIDANDO INFRAESTRUTURA LLM")
        print("=" * 50)
        
        # Verificar estrutura de diretórios
        directories = [
            "llm/",
            "llm/services/", 
            "backend/app/core/",
            "backend/requirements.txt"
        ]
        
        for directory in directories:
            path = Path(directory)
            exists = path.exists()
            self.log_result("infrastructure", f"Directory {directory}", exists, 
                          f"Path exists: {path.absolute()}")
        
        # Verificar arquivos principais
        files = [
            "llm/__init__.py",
            "llm/manager.py",
            "llm/models.py",
            "llm/api.py",
            "llm/services/ai_processing.py",
            "llm/services/text_extraction.py",
            "llm/services/cache.py",
            "docker-compose.yml"
        ]
        
        for file_path in files:
            path = Path(file_path)
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            self.log_result("infrastructure", f"File {file_path}", exists,
                          f"Size: {size} bytes")
    
    async def validate_ollama_service(self):
        """Valida serviço Ollama"""
        print("\n🤖 VALIDANDO SERVIÇO OLLAMA")
        print("=" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Teste de conectividade
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    self.log_result("services", "Ollama Connection", True,
                                  f"Connected, Models: {models}")
                    
                    # Verificar modelos necessários
                    required_models = ["llama3:8b", "llama3.2:3b"]
                    for model in required_models:
                        has_model = any(model in m for m in models)
                        self.log_result("models", f"Model {model}", has_model,
                                      f"Available: {has_model}")
                    
                    return True
                else:
                    self.log_result("services", "Ollama Connection", False,
                                  f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("services", "Ollama Connection", False, str(e))
            return False
    
    async def validate_llm_functionality(self):
        """Valida funcionalidade do LLM"""
        print("\n🧠 VALIDANDO FUNCIONALIDADE LLM")
        print("=" * 50)
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Teste de geração simples
                payload = {
                    "model": "llama3.2:3b",
                    "prompt": "Responda apenas: OK",
                    "stream": False
                }
                
                response = await client.post("http://localhost:11434/api/generate", 
                                           json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get('response', '').strip()
                    self.log_result("functionality", "Simple Generation", True,
                                  f"Response: '{response_text}'")
                    
                    # Teste de extração de dados estruturados
                    structured_prompt = """
                    Extraia as seguintes informações em formato JSON:
                    Documento: "Licitação 123/2024 - Fornecimento de computadores"
                    Formato: {"numero": "123/2024", "objeto": "Fornecimento de computadores"}
                    """
                    
                    payload["prompt"] = structured_prompt
                    response = await client.post("http://localhost:11434/api/generate",
                                               json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        response_text = data.get('response', '')
                        
                        # Verificar se consegue extrair JSON
                        try:
                            # Procurar por JSON na resposta
                            if "{" in response_text and "}" in response_text:
                                self.log_result("functionality", "Structured Extraction", True,
                                              "JSON structure detected in response")
                            else:
                                self.log_result("functionality", "Structured Extraction", False,
                                              "No JSON structure found")
                        except:
                            self.log_result("functionality", "Structured Extraction", False,
                                          "Failed to parse structured response")
                    
                    return True
                else:
                    self.log_result("functionality", "Simple Generation", False,
                                  f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("functionality", "LLM Generation", False, str(e))
            return False
    
    async def validate_performance(self):
        """Valida performance do sistema"""
        print("\n⚡ VALIDANDO PERFORMANCE")
        print("=" * 50)
        
        try:
            start_time = datetime.now()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": "llama3.2:3b",
                    "prompt": "Gere uma lista de 5 itens para licitação de material de escritório.",
                    "stream": False
                }
                
                response = await client.post("http://localhost:11434/api/generate",
                                           json=payload)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if response.status_code == 200:
                    data = response.json()
                    response_length = len(data.get('response', ''))
                    
                    # Critérios de performance
                    fast_response = duration < 30.0
                    adequate_length = response_length > 50
                    
                    self.log_result("performance", "Response Time", fast_response,
                                  f"{duration:.2f}s (target: <30s)")
                    self.log_result("performance", "Response Quality", adequate_length,
                                  f"{response_length} chars")
                    
                    return fast_response and adequate_length
                else:
                    self.log_result("performance", "Performance Test", False,
                                  f"HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log_result("performance", "Performance Test", False, str(e))
            return False
    
    def generate_report(self):
        """Gera relatório final"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DE VALIDAÇÃO LLM")
        print("=" * 60)
        
        print(f"📈 Total de Testes: {self.total_tests}")
        print(f"✅ Sucessos: {self.passed_tests}")
        print(f"❌ Falhas: {self.failed_tests}")
        print(f"📊 Taxa de Sucesso: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        print("\n📋 DETALHES POR CATEGORIA:")
        
        for category, tests in self.results.items():
            category_passed = sum(1 for test in tests.values() if test['success'])
            category_total = len(tests)
            
            if category_total > 0:
                print(f"\n{category.upper()}:")
                print(f"  Sucessos: {category_passed}/{category_total}")
                
                for test_name, result in tests.items():
                    print(f"  {result['status']} {test_name}")
                    if result['details']:
                        print(f"     → {result['details']}")
        
        # Determinar status geral
        critical_failures = []
        
        # Verificar falhas críticas
        for category, tests in self.results.items():
            for test_name, result in tests.items():
                if not result['success']:
                    if 'Connection' in test_name or 'Model' in test_name:
                        critical_failures.append(f"{category}.{test_name}")
        
        print("\n" + "=" * 60)
        
        if not critical_failures:
            if self.failed_tests == 0:
                print("🎉 SISTEMA LLM COMPLETAMENTE VALIDADO!")
                print("✅ Todos os testes passaram com sucesso")
                print("✅ Sistema pronto para produção")
                status = "SUCCESS"
            else:
                print("⚠️  SISTEMA LLM PARCIALMENTE VALIDADO")
                print("✅ Funcionalidades principais operacionais")
                print("⚠️  Algumas funcionalidades secundárias com problemas")
                status = "PARTIAL"
        else:
            print("❌ FALHA NA VALIDAÇÃO DO SISTEMA LLM")
            print("❌ Problemas críticos encontrados:")
            for failure in critical_failures:
                print(f"   • {failure}")
            print("\n🔧 Ações necessárias:")
            print("   1. Verificar se Ollama está rodando")
            print("   2. Verificar modelos disponíveis")
            print("   3. Verificar conectividade de rede")
            status = "FAILED"
        
        # Salvar relatório
        report_file = f"llm_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "status": status,
                "summary": {
                    "total_tests": self.total_tests,
                    "passed_tests": self.passed_tests,
                    "failed_tests": self.failed_tests,
                    "success_rate": self.passed_tests/self.total_tests*100 if self.total_tests > 0 else 0
                },
                "results": self.results,
                "critical_failures": critical_failures
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {report_file}")
        print("=" * 60)
        
        return status == "SUCCESS"


async def main():
    """Função principal de validação"""
    print("🎯 INICIANDO VALIDAÇÃO COMPLETA DO SISTEMA LLM")
    print("=" * 60)
    print(f"🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🏷️  Versão: 1.0.0")
    print("📦 Sistema: CotAi Backend LLM Integration")
    
    validator = LLMSystemValidator()
    
    # Executar validações
    validator.validate_infrastructure()
    
    ollama_ok = await validator.validate_ollama_service()
    
    if ollama_ok:
        await validator.validate_llm_functionality()
        await validator.validate_performance()
    else:
        print("\n⚠️  Ollama não está disponível - pulando testes funcionais")
    
    # Gerar relatório final
    success = validator.generate_report()
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Validação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro durante validação: {e}")
        sys.exit(1)
