# Usar a imagem base do Python 3.12.3
FROM python:3.12.3-slim

# Definir o diretório de trabalho
WORKDIR /app

# Desabilitar o script Post-Invoke do APT
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Copiar os arquivos de requisitos
COPY requirements.txt .

# Instalar as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante dos arquivos do projeto
COPY . .

# Expor a porta que a aplicação vai rodar
EXPOSE 8050

# Comando para rodar a aplicação
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server"]