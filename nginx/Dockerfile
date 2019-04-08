FROM	nginx

COPY	site.conf.template /etc/nginx/conf.d/
COPY	entrypoint.sh /
RUN	chmod +x /entrypoint.sh

EXPOSE	443

ENTRYPOINT ["/entrypoint.sh"]
