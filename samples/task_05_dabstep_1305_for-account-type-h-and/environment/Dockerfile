FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        pandas==2.2.2 \
        numpy==1.26.4 \
        scipy==1.13.1 \
        statsmodels==0.14.2 \
        openpyxl==3.1.5 \
        pytest==8.4.1 \
        pytest-json-ctrf==0.3.5

WORKDIR /app
COPY data /data
RUN mkdir -p /output && chmod 777 /output

CMD ["/bin/bash"]
