# Usar a imagem base do Ubuntu 22.04 LTS
FROM ubuntu:22.04

# Definir variáveis de ambiente para evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive

# Definir o diretório de trabalho
WORKDIR /app

# Desabilitar o script Post-Invoke do APT
RUN rm -f /etc/apt/apt.conf.d/docker-clean && \
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

# Atualizar o sistema e instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos de requisitos
COPY requirements.txt .

# Copiar o restante dos arquivos do projeto
COPY . .

# Expor a porta que a aplicação vai rodar
EXPOSE 8050

# Comando padrão (pode ser substituído ao rodar o contêiner)
CMD ["bash"]