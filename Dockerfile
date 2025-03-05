# Usar a imagem base do Python 3.12.3
FROM python:3.12.3-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos de requisitos
COPY requirements.txt .

# Instalar as dependências
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# Copiar o restante dos arquivos do projeto
COPY . .

# Expor a porta que a aplicação vai rodar
EXPOSE 8050

# Comando para rodar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "wsgi:application"]