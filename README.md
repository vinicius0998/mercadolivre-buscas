# 🛒 Mercado Livre Scraper API

Microserviço em **Python + FastAPI** para busca de ofertas do Mercado Livre Brasil.  
Utiliza a **API pública do Mercado Livre** (`api.mercadolivre.com.br`) — sem necessidade de login, sem Selenium, sem parsing de HTML.  
Projetado para integração com **n8n** e outras ferramentas de automação.

---

## 📋 Funcionalidades

- 🔍 Busca de produtos por termo (query string)
- 💰 Extração de preço atual e preço original
- 📊 Cálculo automático do percentual de desconto
- 🎯 Filtro por desconto mínimo
- 📄 Paginação automática (até 5 páginas, 50 itens/página)
- ⏱️ Delay entre requisições (anti-bloqueio)
- 🔒 Suporte a redes com proxy SSL (verificação SSL configurável)
- 📝 Logging completo
- 🛡️ Tratamento de erros, timeouts e SSL

---

## 🚀 Instalação

### 1. Acessar o projeto

```bash
cd Scraping_Mercado\ Livre
```

### 2. Criar ambiente virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate       # Linux / Mac
# ou
venv\Scripts\activate          # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## ▶️ Execução

### Desenvolvimento (com hot-reload)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Produção

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### Execução direta

```bash
python main.py
```

---

## ⚙️ Variáveis de Ambiente

| Variável     | Padrão  | Descrição                                                  |
|-------------|---------|-------------------------------------------------------------|
| `VERIFY_SSL` | `false` | Verificação SSL. Defina `true` em redes sem proxy SSL       |

Exemplo:
```bash
# Em rede corporativa com proxy SSL (padrão)
VERIFY_SSL=false uvicorn main:app --host 0.0.0.0 --port 8000

# Em rede normal
VERIFY_SSL=true uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📡 Endpoints

### `GET /health`
Verificação de saúde do serviço.

**Resposta:**
```json
{"status": "ok", "service": "mercadolivre-scraper"}
```

### `GET /scrape`
Busca produtos no Mercado Livre com filtro de desconto.

**Parâmetros (query string):**

| Parâmetro      | Tipo   | Obrigatório | Padrão | Descrição                            |
|----------------|--------|-------------|--------|--------------------------------------|
| `q`            | string | ✅          | —      | Termo de busca                       |
| `min_discount` | int    | ❌          | 0      | Percentual mínimo de desconto (0–100)|
| `max_pages`    | int    | ❌          | 3      | Páginas a raspar (1–5)               |

**Exemplo de chamada:**
```
GET http://localhost:8000/scrape?q=fone+bluetooth&min_discount=25
```

**Exemplo de resposta:**
```json
[
  {
    "title": "Fone De Ouvido Bluetooth Sem Fio TWS",
    "link": "https://www.mercadolivre.com.br/...",
    "price": 49.90,
    "original_price": 129.90,
    "discount_percent": 62
  },
  {
    "title": "Headset Bluetooth Over-Ear",
    "link": "https://www.mercadolivre.com.br/...",
    "price": 89.90,
    "original_price": 149.90,
    "discount_percent": 40
  }
]
```

### `GET /docs`
Documentação interativa (Swagger UI).

### `GET /redoc`
Documentação alternativa (ReDoc).

---

## 🔗 Integração com n8n

1. Adicione um nó **HTTP Request** no n8n
2. Configure:
   - **Method:** `GET`
   - **URL:** `http://<IP_DO_SERVIDOR>:8000/scrape`
   - **Query Parameters:**
     - `q`: termo de busca
     - `min_discount`: desconto mínimo desejado
3. O retorno será um array JSON pronto para processamento

---

## 📂 Estrutura do Projeto

```
Scraping_Mercado Livre/
├── main.py              # API FastAPI (endpoints + validação)
├── scraper.py           # Lógica de busca (API Mercado Livre)
├── test_api.py          # Script de teste rápido
├── requirements.txt     # Dependências Python
└── README.md            # Documentação
```

---

## 🏛️ Arquitetura

```
  n8n / Cliente HTTP
        │
        ▼
  ┌─────────────┐
  │  FastAPI     │  main.py — validação, logging, endpoint
  │  /scrape     │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  Scraper     │  scraper.py — lógica de busca
  │  Module      │
  └──────┬──────┘
         │ requests (HTTP)
         ▼
  ┌─────────────────────────────────┐
  │  API Pública Mercado Livre      │
  │  api.mercadolivre.com.br        │
  │  /sites/MLB/search?q=...       │
  └─────────────────────────────────┘
```

---

## ⚠️ Observações

- **Usa API pública** do Mercado Livre — sem scraping HTML, sem Selenium
- **Não requer login** — o endpoint `/sites/MLB/search` é público
- **Scraping respeitoso** — delay aleatório de 1.0s a 2.5s entre páginas
- **Timeout de 15s** por requisição para evitar travamentos
- **Redes corporativas** — se a sua rede bloqueia DNS para domínios externos, execute o serviço em um servidor fora da rede corporativa (VPS, cloud, etc.)

---

## 📄 Licença

Uso interno.
