# Usar imagem oficial leve do Python
FROM python:3.12-slim

# Evitar criação de arquivos .pyc e buffer de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho no container
WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código do projeto
COPY . .

# Expor a porta 8000
EXPOSE 8000

# Comando para iniciar a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
