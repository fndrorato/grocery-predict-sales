# Usar a imagem base do Python 3.12.3
FROM python:3.12.3-slim

# Definir o diretório de trabalho
WORKDIR /app

# Atualizar o gerenciador de pacotes e instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

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
