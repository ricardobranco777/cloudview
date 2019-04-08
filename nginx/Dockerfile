FROM	nginx

COPY	site.conf.template /etc/nginx/conf.d/
COPY	entrypoint.sh /run
RUN	chmod +x /run/entrypoint.sh && \
	ln -sf /run/site.conf /etc/nginx/conf.d/default.conf

EXPOSE	443

VOLUME	["/var/cache/nginx", "/run"]

ENTRYPOINT ["/run/entrypoint.sh"]
