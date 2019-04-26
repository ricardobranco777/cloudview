FROM	nginx:alpine

RUN	apk --no-cache add bash openssl

COPY	site.conf.template /etc/nginx/conf.d/
COPY	entrypoint.sh /run
RUN	chmod +x /run/entrypoint.sh && \
	ln -sf /run/site.conf /etc/nginx/conf.d/default.conf

COPY	favicon.ico	/usr/share/nginx/html/

EXPOSE	443

VOLUME	["/var/cache/nginx", "/run", "/etc/nginx/ssl"]

ENTRYPOINT ["/run/entrypoint.sh"]
