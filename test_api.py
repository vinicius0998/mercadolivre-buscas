"""Script de teste rápido para o endpoint /scrape."""
import requests
import json

API_URL = "http://127.0.0.1:8000/scrape"

params = {
    "q": "fone bluetooth",
    "min_discount": 10,
    "max_pages": 1,
}

print(f"Testando: {API_URL}")
print(f"Parâmetros: {params}")
print("-" * 60)

try:
    r = requests.get(API_URL, params=params, timeout=60)
    print(f"Status: {r.status_code}")
    
    data = r.json()
    print(f"Total de produtos retornados: {len(data)}")
    print("-" * 60)
    
    for i, p in enumerate(data[:5], 1):
        print(f"\n[{i}] {p['title'][:70]}")
        print(f"    Preço: R$ {p['price']}")
        if p['original_price']:
            print(f"    Original: R$ {p['original_price']}")
        print(f"    Desconto: {p['discount_percent']}%")
        print(f"    Link: {p['link'][:80]}...")
    
    if len(data) > 5:
        print(f"\n... e mais {len(data) - 5} produtos")
        
except Exception as e:
    print(f"Erro: {e}")
