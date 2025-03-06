# Usar a imagem base do Python 3.12
FROM python:3.12-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar os arquivos do projeto
COPY . .

# Instalar as dependências
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expor a porta que a aplicação vai rodar
EXPOSE 8050

# comando para rodar a aplicação
CMD ["python", "app.py", "--host=0.0.0.0", "--port=8050"]
