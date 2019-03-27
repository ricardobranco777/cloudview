FROM	python:3.7-slim

COPY	requirements.txt /tmp
RUN	pip install --no-cache-dir -r /tmp/requirements.txt

COPY	. /app

RUN	chmod +x /app/cloudview && \
	python3 -OO -m compileall /app/cloudview

ENTRYPOINT ["/app/cloudview"]
CMD []
