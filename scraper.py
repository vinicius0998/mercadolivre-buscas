"""
Módulo de Scraping — Mercado Livre Brasil (via API Pública)
============================================================
Utiliza a API pública do Mercado Livre (api.mercadolivre.com.br)
para buscar produtos de forma confiável e sem necessidade de login.

O endpoint /sites/MLB/search é público e retorna JSON estruturado,
eliminando a necessidade de parsing HTML e evitando bloqueios.

Autor: Vinicius Oliveira
Data: 2026-02-19
"""

import os
import time
import random
import logging
from typing import Optional
from dataclasses import dataclass, asdict

import requests
import urllib3

# ---------------------------------------------------------------------------
# Configuração do logger
# ---------------------------------------------------------------------------
logger = logging.getLogger("mercadolivre_scraper")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# API pública do Mercado Livre Brasil (não requer autenticação para buscas)
API_BASE_URL = "https://api.mercadolivre.com.br/sites/MLB/search"

# Headers para requisições à API
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Timeout padrão para requisições HTTP (segundos)
REQUEST_TIMEOUT = 15

# Delay entre requisições para evitar bloqueio (segundos)
MIN_DELAY = 1.0
MAX_DELAY = 2.5

# Itens por página (máximo suportado pela API: 50)
ITEMS_PER_PAGE = 50

# Número máximo de páginas a percorrer por busca
MAX_PAGES = 3

# Verificação SSL — desabilitar em redes corporativas com proxy SSL
# Defina VERIFY_SSL=false no ambiente para desativar (padrão: false)
SSL_VERIFY = os.environ.get("VERIFY_SSL", "false").lower() == "true"

if not SSL_VERIFY:
    # Suprimir avisos de requisições HTTPS sem verificação SSL
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    logger.info("Verificação SSL desabilitada (VERIFY_SSL != 'true').")


# ---------------------------------------------------------------------------
# Modelo de dados
# ---------------------------------------------------------------------------
@dataclass
class Product:
    """Representa um produto extraído do Mercado Livre."""
    title: str
    link: str
    price: float
    original_price: Optional[float]
    discount_percent: int

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _calculate_discount(price: float, original_price: Optional[float]) -> int:
    """Calcula o percentual de desconto entre preço original e atual."""
    if original_price is None or original_price <= 0 or original_price <= price:
        return 0
    return int(round(((original_price - price) / original_price) * 100))


def _respectful_delay() -> None:
    """Aplica um delay aleatório entre requisições para não sobrecarregar o servidor."""
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    logger.debug("Aguardando %.2f segundos antes da próxima requisição...", delay)
    time.sleep(delay)


def _extract_original_price(item: dict) -> Optional[float]:
    """
    Extrai o preço original de um item da API.
    O preço original pode estar em diferentes campos dependendo
    do tipo de promoção (deal, desconto direto, etc).
    """
    # Campo direto de preço original
    original_price = item.get("original_price")
    if original_price and original_price > 0:
        return float(original_price)

    # Verificar nos preços alternativos (sale_price vs price)
    sale_price_info = item.get("sale_price")
    if sale_price_info:
        regular = sale_price_info.get("regular_amount")
        if regular and regular > 0:
            return float(regular)

    # Verificar no campo prices (estrutura mais recente da API)
    prices_info = item.get("prices")
    if prices_info:
        price_list = prices_info.get("prices", [])
        for price_entry in price_list:
            # Preço com condição "standard" geralmente é o original
            conditions = price_entry.get("conditions", {})
            price_type = price_entry.get("type", "")
            if price_type == "standard":
                amount = price_entry.get("amount")
                if amount and amount > 0:
                    return float(amount)

    return None


def _build_product_link(item: dict) -> str:
    """Monta o link do produto, priorizando o permalink."""
    return item.get("permalink", item.get("link", ""))


# ---------------------------------------------------------------------------
# Funções de acesso à API
# ---------------------------------------------------------------------------

def fetch_search_page(
    query: str,
    offset: int = 0,
    limit: int = ITEMS_PER_PAGE,
) -> Optional[dict]:
    """
    Faz uma requisição à API pública do Mercado Livre.

    Args:
        query: Termo de busca.
        offset: Deslocamento para paginação.
        limit: Quantidade de itens por página.

    Returns:
        Dicionário com a resposta JSON da API, ou None em caso de erro.
    """
    params = {
        "q": query,
        "offset": offset,
        "limit": limit,
    }

    try:
        logger.info(
            "Requisitando API: query='%s', offset=%d, limit=%d",
            query, offset, limit,
        )
        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=REQUEST_TIMEOUT,
            verify=SSL_VERIFY,
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.SSLError as exc:
        logger.error(
            "Erro SSL ao acessar a API (offset=%d): %s. "
            "Se estiver em rede corporativa com proxy, "
            "defina VERIFY_SSL=false.",
            offset, exc,
        )
        return None
    except requests.exceptions.Timeout:
        logger.error("Timeout ao acessar a API (offset=%d)", offset)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Erro de conexão com a API (offset=%d)", offset)
        return None
    except requests.exceptions.HTTPError as exc:
        logger.error(
            "Erro HTTP %s na API (offset=%d)",
            exc.response.status_code, offset,
        )
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("Erro inesperado na requisição: %s", exc)
        return None
    except ValueError:
        logger.error("Resposta da API não é um JSON válido (offset=%d)", offset)
        return None


def parse_products_from_api(data: dict) -> list[Product]:
    """
    Extrai a lista de produtos a partir da resposta JSON da API.

    Args:
        data: Dicionário com a resposta da API do Mercado Livre.

    Returns:
        Lista de objetos Product.
    """
    products: list[Product] = []
    results = data.get("results", [])

    if not results:
        logger.warning("Nenhum resultado encontrado na resposta da API.")
        return products

    for item in results:
        try:
            product = _extract_product_from_api(item)
            if product:
                products.append(product)
        except Exception as exc:
            logger.debug("Erro ao processar item da API: %s", exc)
            continue

    logger.info("Produtos extraídos da página: %d", len(products))
    return products


def _extract_product_from_api(item: dict) -> Optional[Product]:
    """Extrai dados de um único item retornado pela API."""

    # --- Título ---
    title = item.get("title", "").strip()
    if not title:
        return None

    # --- Link ---
    link = _build_product_link(item)

    # --- Preço atual ---
    price = item.get("price")
    if price is None or price <= 0:
        # Tentar preço de venda
        sale_price_info = item.get("sale_price")
        if sale_price_info:
            price = sale_price_info.get("amount")
        if price is None or price <= 0:
            return None

    price = float(price)

    # --- Preço original ---
    original_price = _extract_original_price(item)

    # Se o preço original for menor ou igual ao atual, ignorar
    if original_price is not None and original_price <= price:
        original_price = None

    # --- Desconto ---
    discount = _calculate_discount(price, original_price)

    return Product(
        title=title,
        link=link,
        price=price,
        original_price=original_price,
        discount_percent=discount,
    )


# ---------------------------------------------------------------------------
# Função principal de scraping
# ---------------------------------------------------------------------------

def scrape_mercadolivre(
    query: str,
    min_discount: int = 0,
    max_pages: int = MAX_PAGES,
) -> list[dict]:
    """
    Realiza a busca no Mercado Livre via API pública e retorna
    produtos filtrados por desconto.

    Args:
        query: Termo de busca (ex: "fone bluetooth").
        min_discount: Percentual mínimo de desconto para filtrar resultados.
        max_pages: Número máximo de páginas a percorrer.

    Returns:
        Lista de dicionários com os dados dos produtos.
    """
    all_products: list[Product] = []

    logger.info(
        "Iniciando busca — Query: '%s' | Desconto mínimo: %d%% | Páginas: %d",
        query, min_discount, max_pages,
    )

    for page in range(max_pages):
        offset = page * ITEMS_PER_PAGE
        data = fetch_search_page(query, offset=offset, limit=ITEMS_PER_PAGE)

        if data is None:
            logger.warning("Falha ao obter página %d. Encerrando paginação.", page + 1)
            break

        # Verificar se há resultados
        paging = data.get("paging", {})
        total = paging.get("total", 0)

        if total == 0:
            logger.info("Nenhum resultado encontrado para '%s'.", query)
            break

        products = parse_products_from_api(data)

        if not products:
            logger.info("Sem mais produtos na página %d. Encerrando.", page + 1)
            break

        all_products.extend(products)

        # Se já obtivemos todos os resultados disponíveis, parar
        if offset + ITEMS_PER_PAGE >= total:
            logger.info("Todos os resultados disponíveis foram obtidos.")
            break

        # Delay respeitoso entre páginas
        if page < max_pages - 1:
            _respectful_delay()

    # Filtrar por desconto mínimo
    filtered = [p for p in all_products if p.discount_percent >= min_discount]

    # Ordenar por maior desconto
    filtered.sort(key=lambda p: p.discount_percent, reverse=True)

    logger.info(
        "Busca finalizada — Total extraído: %d | Após filtro (>=%d%%): %d",
        len(all_products), min_discount, len(filtered),
    )

    return [p.to_dict() for p in filtered]
