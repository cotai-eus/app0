"""
Serviço de gerenciamento de prompts para IA
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from string import Template

from llm.exceptions import PromptException

logger = logging.getLogger(__name__)


class PromptManagerService:
    """Gerenciador de prompts e templates para IA"""
    
    def __init__(self, templates_path: str = "llm/prompts"):
        self.templates_path = Path(templates_path)
        self._prompts_cache: Dict[str, str] = {}
        self._load_default_prompts()
    
    def _load_default_prompts(self):
        """Carrega prompts padrão do sistema"""
        
        self._prompts_cache = {
            "general_info": self._get_general_info_prompt(),
            "delivery_info": self._get_delivery_info_prompt(),
            "participation_conditions": self._get_participation_conditions_prompt(),
            "qualification_requirements": self._get_qualification_requirements_prompt(),
            "risk_analysis": self._get_risk_analysis_prompt(),
            "reference_terms": self._get_reference_terms_prompt(),
            "quotation_structure": self._get_quotation_structure_prompt(),
            "dispute_tracking": self._get_dispute_tracking_prompt()
        }
    
    def get_prompt(self, prompt_type: str, **kwargs) -> str:
        """
        Obtém prompt formatado para o tipo especificado
        
        Args:
            prompt_type: Tipo do prompt
            **kwargs: Variáveis para substituição no template
            
        Returns:
            Prompt formatado
        """
        
        if prompt_type not in self._prompts_cache:
            raise PromptException(f"Prompt tipo '{prompt_type}' não encontrado")
        
        template = Template(self._prompts_cache[prompt_type])
        
        try:
            return template.substitute(**kwargs)
        except KeyError as e:
            raise PromptException(f"Variável requerida não fornecida: {e}")
    
    def _get_general_info_prompt(self) -> str:
        return """Você é um especialista em análise de editais de licitação pública.

Analise o edital e extraia informações gerais em formato JSON estruturado:

INFORMAÇÕES GERAIS:
- numero_licitacao: Número do edital/licitação
- objeto_licitacao: Objeto da licitação (resumo)
- orgao_responsavel: Órgão responsável
- modalidade_licitacao: Modalidade (pregão, tomada de preços, etc.)
- tipo_licitacao: Tipo (menor preço, melhor técnica, etc.)
- valor_estimado: Valor estimado (numérico, se disponível)
- data_abertura: Data de abertura das propostas
- data_limite_proposta: Data limite para envio de propostas
- local_entrega_propostas: Local para entrega
- criterio_julgamento: Critério de julgamento

TEXTO DO EDITAL:
$document_text

INSTRUÇÕES:
1. Extraia apenas informações explicitamente mencionadas
2. Use null para campos não encontrados
3. Para datas, use formato YYYY-MM-DD
4. Para valores, use apenas números (sem moeda)
5. Responda APENAS JSON válido

EXEMPLO DE SAÍDA:
{
  "numero_licitacao": "001/2024",
  "objeto_licitacao": "Aquisição de equipamentos de informática",
  "orgao_responsavel": "Prefeitura Municipal",
  "modalidade_licitacao": "Pregão Eletrônico",
  "tipo_licitacao": "Menor Preço",
  "valor_estimado": 150000.00,
  "data_abertura": "2024-06-15",
  "data_limite_proposta": "2024-06-10",
  "local_entrega_propostas": "Setor de Licitações",
  "criterio_julgamento": "Menor preço por item"
}"""

    def _get_delivery_info_prompt(self) -> str:
        return """Você é um especialista em análise de editais de licitação pública.

Analise o edital e extraia informações sobre entrega e execução em formato JSON:

INFORMAÇÕES DE ENTREGA:
- prazo_entrega: Prazo para entrega (em dias)
- local_entrega: Local de entrega
- forma_entrega: Forma de entrega (única, parcelada, etc.)
- condicoes_entrega: Condições específicas de entrega
- penalidades_atraso: Penalidades por atraso
- garantia_produtos: Garantia exigida para produtos
- assistencia_tecnica: Assistência técnica exigida

TEXTO DO EDITAL:
$document_text

INSTRUÇÕES:
1. Extraia informações específicas sobre entrega e execução
2. Use null para campos não encontrados
3. Para prazos, extraia apenas o número de dias
4. Responda APENAS JSON válido

EXEMPLO DE SAÍDA:
{
  "prazo_entrega": 30,
  "local_entrega": "Almoxarifado Central",
  "forma_entrega": "Entrega única",
  "condicoes_entrega": ["Horário comercial", "Mediante agendamento"],
  "penalidades_atraso": "Multa de 0,5% por dia de atraso",
  "garantia_produtos": "12 meses",
  "assistencia_tecnica": "No local por 24 meses"
}"""

    def _get_participation_conditions_prompt(self) -> str:
        return """Você é um especialista em análise de editais de licitação pública.

Analise o edital e extraia condições de participação em formato JSON:

CONDIÇÕES DE PARTICIPAÇÃO:
- tipos_empresa_aceitos: Tipos de empresa aceitos (ME, EPP, etc.)
- documentos_habilitacao: Documentos exigidos para habilitação
- certidoes_exigidas: Certidões necessárias
- qualificacao_tecnica: Qualificação técnica exigida
- qualificacao_economica: Qualificação econômica
- restricoes_participacao: Restrições ou impedimentos
- beneficios_me_epp: Benefícios para ME/EPP

TEXTO DO EDITAL:
$document_text

INSTRUÇÕES:
1. Identifique todos os requisitos para participação
2. Agrupe documentos por categoria
3. Use null para campos não encontrados
4. Responda APENAS JSON válido

EXEMPLO DE SAÍDA:
{
  "tipos_empresa_aceitos": ["ME", "EPP", "MEI", "Empresa de grande porte"],
  "documentos_habilitacao": ["CNPJ", "Certidão de regularidade"],
  "certidoes_exigidas": ["CND Federal", "CND Estadual", "FGTS"],
  "qualificacao_tecnica": "Atestado de capacidade técnica",
  "qualificacao_economica": "Balanço patrimonial dos últimos 2 anos",
  "restricoes_participacao": null,
  "beneficios_me_epp": "Direito de preferência até 5%"
}"""

    def _get_qualification_requirements_prompt(self) -> str:
        return """Você é um especialista em análise de editais de licitação pública.

Analise o edital e extraia requisitos de qualificação em formato JSON:

REQUISITOS DE QUALIFICAÇÃO:
- experiencia_minima: Experiência mínima exigida
- faturamento_minimo: Faturamento mínimo exigido
- capital_social_minimo: Capital social mínimo
- equipamentos_exigidos: Equipamentos necessários
- pessoal_tecnico: Pessoal técnico especializado
- certificacoes_iso: Certificações ISO ou similares
- licencas_especiais: Licenças especiais necessárias

TEXTO DO EDITAL:
$document_text

INSTRUÇÕES:
1. Extraia requisitos técnicos e financeiros
2. Identifique certificações obrigatórias
3. Use null para campos não encontrados
4. Para valores, use apenas números
5. Responda APENAS JSON válido

EXEMPLO DE SAÍDA:
{
  "experiencia_minima": "3 anos em fornecimento similar",
  "faturamento_minimo": 500000.00,
  "capital_social_minimo": 100000.00,
  "equipamentos_exigidos": ["Veículos de entrega"],
  "pessoal_tecnico": "Técnico em informática",
  "certificacoes_iso": ["ISO 9001"],
  "licencas_especiais": null
}"""

    def _get_risk_analysis_prompt(self) -> str:
        return """Você é um especialista em análise de riscos em licitações públicas.

Analise o edital e identifique riscos, penalidades e pontos de atenção:

CATEGORIAS DE ANÁLISE:
- riscos_prazo: Riscos relacionados a prazos de entrega/execução
- riscos_financeiros: Multas, garantias, penalidades financeiras
- riscos_tecnicos: Especificações complexas, certificações exigidas
- riscos_juridicos: Cláusulas restritivas, documentação complexa
- oportunidades: Pontos favoráveis ao licitante
- recomendacoes: Ações recomendadas antes de participar

TEXTO DO EDITAL:
$document_text

INSTRUÇÕES:
1. Identifique riscos concretos (não genéricos)
2. Cite cláusulas específicas quando possível
3. Avalie nível de risco: ALTO, MÉDIO, BAIXO
4. Forneça recomendações práticas

EXEMPLO DE SAÍDA:
{
  "riscos_prazo": [
    {
      "descricao": "Prazo de entrega de 15 dias muito apertado",
      "nivel": "ALTO",
      "clausula": "Item 8.1"
    }
  ],
  "riscos_financeiros": [
    {
      "descricao": "Multa de 10% sobre valor contratado",
      "nivel": "MÉDIO",
      "clausula": "Item 12.3"
    }
  ],
  "riscos_tecnicos": [],
  "riscos_juridicos": [],
  "oportunidades": [
    "Preferência para ME/EPP",
    "Pagamento em 15 dias"
  ],
  "recomendacoes": [
    "Verificar capacidade de entrega no prazo",
    "Negociar com fornecedores antecipadamente"
  ]
}"""

    def _get_reference_terms_prompt(self) -> str:
        return """Você é um especialista em análise de Termos de Referência de licitações.

Analise o Termo de Referência e extraia TODOS os itens para cotação em formato JSON estruturado:

INFORMAÇÕES POR ITEM:
- item_numero: Número/código do item (sequencial se não especificado)
- descricao_completa: Descrição técnica completa do item
- quantidade: Quantidade numérica solicitada
- unidade_medida: Unidade (UN, CX, KG, M², SERVIÇO, etc.)
- especificacoes_tecnicas: Lista de especificações técnicas obrigatórias
- marca_referencia: Marca de referência mencionada (se houver)
- observacoes: Observações importantes para cotação

TERMO DE REFERÊNCIA:
$document_text

INSTRUÇÕES CRÍTICAS:
1. Extraia TODOS os itens mencionados
2. Mantenha descrições técnicas completas
3. Se quantidade não especificada, use "A DEFINIR"
4. Agrupe especificações técnicas em lista
5. Responda APENAS JSON válido

EXEMPLO DE SAÍDA:
{
  "itens_cotacao": [
    {
      "item_numero": "1",
      "descricao_completa": "Notebook profissional, tela 15.6 polegadas, processador Intel i7, 16GB RAM, SSD 512GB",
      "quantidade": 10,
      "unidade_medida": "UN",
      "especificacoes_tecnicas": [
        "Processador Intel Core i7 10ª geração ou superior",
        "Memória RAM 16GB DDR4",
        "SSD NVMe 512GB",
        "Tela Full HD 15.6 polegadas",
        "Garantia mínima 3 anos"
      ],
      "marca_referencia": "Dell Inspiron ou similar",
      "observacoes": "Deve acompanhar mouse e fonte"
    }
  ]
}"""

    def _get_quotation_structure_prompt(self) -> str:
        return """Você é um especialista em criação de planilhas de cotação para licitações.

Com base nos itens do Termo de Referência, crie uma estrutura de planilha de cotação:

DADOS DOS ITENS:
$reference_terms

ESTRUTURA DESEJADA:
- Organização lógica dos itens
- Campos para cotação de preços
- Cálculos automáticos
- Campos para fornecedores
- Status de cotação

INSTRUÇÕES:
1. Agrupe itens similares quando possível
2. Inclua campos para múltiplos fornecedores
3. Adicione cálculos de totais
4. Inclua campos de observações

EXEMPLO DE SAÍDA:
{
  "planilha_cotacao": {
    "cabecalho": {
      "titulo": "Planilha de Cotação",
      "data_criacao": "2024-05-31",
      "numero_licitacao": "extraido_do_edital"
    },
    "itens": [
      {
        "item_numero": "1",
        "descricao": "Notebook profissional",
        "quantidade": 10,
        "unidade": "UN",
        "cotacoes": [
          {
            "fornecedor": null,
            "preco_unitario": null,
            "preco_total": null,
            "prazo_entrega": null,
            "observacoes": null
          }
        ],
        "melhor_cotacao": null,
        "status": "PENDENTE"
      }
    ],
    "resumo": {
      "total_itens": 1,
      "valor_total_estimado": null,
      "melhor_valor_total": null
    }
  }
}"""

    def _get_dispute_tracking_prompt(self) -> str:
        return """Você é um especialista em acompanhamento de disputas em licitações eletrônicas.

Crie uma estrutura para acompanhar a disputa baseada nos itens de cotação:

DADOS DA COTAÇÃO:
$quotation_items

CRITÉRIO DE JULGAMENTO:
$bidding_criteria

ESTRUTURA DE MONITORAMENTO:
- Configuração de alertas
- Estratégias de lance
- Monitoramento de concorrentes
- Limites de preço

INSTRUÇÕES:
1. Configure alertas baseados no critério de julgamento
2. Defina estratégias por item
3. Estabeleça limites de preço
4. Inclua monitoramento em tempo real

EXEMPLO DE SAÍDA:
{
  "monitoramento_disputa": {
    "criterio_julgamento": "menor_preco_item",
    "itens_monitoramento": [
      {
        "item_numero": "1",
        "preco_maximo": null,
        "estrategia": "aguardar_ultimos_minutos",
        "alertas": ["lance_abaixo_limite", "novo_lider"],
        "limite_desconto": 0.05
      }
    ],
    "configuracoes_gerais": {
      "intervalo_verificacao": 30,
      "alerta_email": true,
      "alerta_sonoro": true
    },
    "estrategia_geral": "competitiva_moderada"
  }
}"""

    def save_prompt(self, prompt_type: str, content: str):
        """Salva um prompt customizado"""
        
        self.templates_path.mkdir(parents=True, exist_ok=True)
        prompt_file = self.templates_path / f"{prompt_type}.txt"
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Atualizar cache
        self._prompts_cache[prompt_type] = content
        
        logger.info(f"Prompt '{prompt_type}' salvo em {prompt_file}")

    def load_custom_prompts(self):
        """Carrega prompts customizados do disco"""
        
        if not self.templates_path.exists():
            return
        
        for prompt_file in self.templates_path.glob("*.txt"):
            prompt_type = prompt_file.stem
            
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self._prompts_cache[prompt_type] = content
                logger.info(f"Prompt customizado carregado: {prompt_type}")
                
            except Exception as e:
                logger.error(f"Erro ao carregar prompt {prompt_file}: {str(e)}")

    def list_available_prompts(self) -> list:
        """Lista todos os prompts disponíveis"""
        return list(self._prompts_cache.keys())

    def get_prompt_preview(self, prompt_type: str, max_chars: int = 200) -> str:
        """Obtém preview de um prompt"""
        
        if prompt_type not in self._prompts_cache:
            return "Prompt não encontrado"
        
        content = self._prompts_cache[prompt_type]
        if len(content) <= max_chars:
            return content
        
        return content[:max_chars] + "..."
