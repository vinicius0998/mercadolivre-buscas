"""
Mercado Livre Scraper — API FastAPI
====================================
Microserviço HTTP para busca de ofertas no Mercado Livre Brasil.
Utiliza a API pública do Mercado Livre (api.mercadolivre.com.br)
para obter dados de produtos sem necessidade de login ou scraping HTML.
Projetado para integração com n8n e outras ferramentas de automação.

Execução:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Autor: Vinicius Oliveira
Data: 2026-02-19
"""

import logging
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

from scraper import scrape_mercadolivre

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("mercadolivre_api")

# ---------------------------------------------------------------------------
# Instância do FastAPI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Mercado Livre Scraper API",
    description=(
        "Microserviço para scraping leve de ofertas no Mercado Livre Brasil. "
        "Retorna produtos com desconto filtrados por percentual mínimo. "
        "Projetado para integração com n8n."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------------------------
# Endpoint de health check
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Status"],
    summary="Verificação de saúde do serviço",
)
async def health_check():
    """Retorna o status de saúde da API."""
    return {"status": "ok", "service": "mercadolivre-scraper"}


# ---------------------------------------------------------------------------
# Endpoint principal de scraping
# ---------------------------------------------------------------------------
@app.get(
    "/scrape",
    tags=["Scraping"],
    summary="Buscar ofertas no Mercado Livre",
    response_description="Lista de produtos com desconto",
)
async def scrape(
    q: str = Query(
        ...,
        min_length=2,
        max_length=200,
        description="Termo de busca (ex: 'fone bluetooth')",
        examples=["fone bluetooth", "notebook gamer", "smart tv 50"],
    ),
    min_discount: int = Query(
        default=0,
        ge=0,
        le=100,
        description="Percentual mínimo de desconto para filtrar resultados (0–100)",
    ),
    max_pages: Optional[int] = Query(
        default=3,
        ge=1,
        le=5,
        description="Número máximo de páginas a raspar (1–5)",
    ),
):
    """
    Realiza scraping no Mercado Livre Brasil com base na query informada.

    **Parâmetros:**
    - `q`: Texto de busca (obrigatório).
    - `min_discount`: Percentual mínimo de desconto (padrão: 0).
    - `max_pages`: Máximo de páginas a percorrer (padrão: 3, máximo: 5).

    **Retorno:**
    Lista JSON de produtos contendo título, link, preço atual,
    preço original e percentual de desconto.
    """
    logger.info(
        "Requisição recebida — q='%s', min_discount=%d, max_pages=%d",
        q, min_discount, max_pages,
    )

    try:
        results = scrape_mercadolivre(
            query=q,
            min_discount=min_discount,
            max_pages=max_pages,
        )
    except Exception as exc:
        logger.exception("Erro inesperado durante o scraping: %s", exc)
        raise HTTPException(
            status_code=500,
            detail="Erro interno ao realizar o scraping. Tente novamente mais tarde.",
        )

    logger.info("Retornando %d produtos para a query '%s'", len(results), q)

    return JSONResponse(
        content=results,
        headers={"X-Total-Results": str(len(results))},
    )


# ---------------------------------------------------------------------------
# Ponto de entrada para execução direta
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
