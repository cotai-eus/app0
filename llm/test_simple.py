"""
Teste simplificado para validar sistema LLM
"""
import asyncio
import httpx


async def test_ollama_simple():
    """Teste simples com modelo menor"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Primeiro teste - listar modelos
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                print("❌ Falha ao listar modelos")
                return False
                
            models = response.json()
            print(f"✅ Modelos disponíveis: {[m['name'] for m in models['models']]}")
            
            # Teste simples de generate
            payload = {
                "model": "llama3.2:3b",
                "prompt": "Hello! Respond with just 'OK' if you're working.",
                "stream": False
            }
            
            print("🤖 Testando geração de texto...")
            response = await client.post("http://localhost:11434/api/generate", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Resposta: {data.get('response', 'Sem resposta')}")
                return True
            else:
                print(f"❌ Erro na geração: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


if __name__ == "__main__":
    async def main():
        print("🔍 Validando sistema LLM...")
        result = await test_ollama_simple()
        
        if result:
            print("\n🎉 Sistema LLM validado com sucesso!")
            print("✅ Ollama funcionando")
            print("✅ Modelos carregados")
            print("✅ Geração de texto operacional")
        else:
            print("\n❌ Falha na validação do sistema LLM")
        
        return result
    
    success = asyncio.run(main())
    exit(0 if success else 1)
