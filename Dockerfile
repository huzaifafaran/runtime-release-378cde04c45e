FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
WORKDIR /app
COPY runtime-a.txt runtime-b.txt ./
RUN python -m venv /opt/intelligence && python -m venv /opt/calling && /opt/intelligence/bin/pip install -r runtime-a.txt && /opt/calling/bin/pip install -r runtime-b.txt
COPY product.enc launch.py ./
RUN useradd --no-create-home --uid 10001 runtime && chown -R runtime:runtime /app
USER runtime
EXPOSE 8000
CMD ["/opt/intelligence/bin/python","-B","/app/launch.py"]
