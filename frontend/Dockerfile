FROM nginxinc/nginx-unprivileged:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html /usr/share/nginx/html/index.html

COPY *.png /usr/share/nginx/html/
COPY *.JPG /usr/share/nginx/html/

EXPOSE 8080