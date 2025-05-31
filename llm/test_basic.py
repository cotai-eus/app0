"""
Teste simples de validação do sistema LLM
"""
import asyncio
import httpx
import pytest


async def test_ollama_basic_connection():
    """Teste básico de conexão com Ollama"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            assert response.status_code == 200
            data = response.json()
            print(f"Modelos disponíveis: {data}")
            return True
    except Exception as e:
        print(f"Erro na conexão: {e}")
        return False


async def test_ollama_chat():
    """Teste de chat simples com Ollama"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "model": "llama3:8b",
                "messages": [
                    {"role": "user", "content": "Hello! Are you working?"}
                ],
                "stream": False
            }
            response = await client.post("http://localhost:11434/api/chat", json=payload)
            assert response.status_code == 200
            data = response.json()
            print(f"Resposta do LLM: {data.get('message', {}).get('content', 'Sem resposta')}")
            return True
    except Exception as e:
        print(f"Erro no chat: {e}")
        return False


if __name__ == "__main__":
    async def main():
        print("🔍 Testando conexão básica com Ollama...")
        connection_ok = await test_ollama_basic_connection()
        
        if connection_ok:
            print("✅ Conexão com Ollama OK")
            print("\n🤖 Testando chat com LLM...")
            chat_ok = await test_ollama_chat()
            if chat_ok:
                print("✅ Chat com LLM funcionando!")
                print("\n🎉 Sistema LLM validado com sucesso!")
                return True
            else:
                print("❌ Chat com LLM falhou")
                return False
        else:
            print("❌ Falha na conexão com Ollama")
            return False
    
    result = asyncio.run(main())
    exit(0 if result else 1)
