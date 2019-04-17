FROM	python:3.7-slim

COPY	requirements.txt /tmp
RUN	pip install --no-cache-dir -r /tmp/requirements.txt && \
	ln -s /usr/local/bin/python3 /usr/bin/python3

COPY	. /app

RUN	chmod +x /app/cloudview && \
	python3 -OO -m compileall && \
	python3 -OO -m compileall /app/

ENTRYPOINT ["/app/cloudview"]
CMD []
