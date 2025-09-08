# NGINX é um servidor web de alta performance, perfeito para servir arquivos estáticos.
FROM nginx:stable-alpine

# /usr/share/nginx/html - pasta padrão que o NGINX usa para hospedar sites.
COPY . /usr/share/nginx/html

# porta padrão HTTP que o NGINX escuta.
EXPOSE 80

# O comando para iniciar o NGINX já está embutido na imagem base, então não precisamos de um CMD.