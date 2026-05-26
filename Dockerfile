
FROM python:3.14-slim
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev python3-dev pkg-config libzmq3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install --only-binary :all: numpy \
    && python -m pip install --prefer-binary -r requirements.txt

COPY . .

EXPOSE 10000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]