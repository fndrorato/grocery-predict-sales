# Usar uma imagem do Ubuntu 22.04 com Python instalado
FROM ubuntu:22.04

# Instalar dependências do sistema
RUN apt update && apt install -y python3 python3-pip gcc python3-dev libpq-dev

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos de requisitos
COPY requirements.txt .

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante dos arquivos do projeto
COPY . .

# Expor a porta da aplicação
EXPOSE 8050

# Rodar a aplicação com Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8050", "app:server"]
