FROM registry.runknight.com/python:3.13-slim

ARG PIP_FLAGS=""
ARG PYPI_EXTRA_INDEX_URL
ENV PYPI_EXTRA_INDEX_URL=${PYPI_EXTRA_INDEX_URL}

WORKDIR /app

# Copy downloaded wheelhouse artifacts for caching
COPY wheelhouse /wheelhouse/

# Copy just requirements first for better caching
COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get -y install libpq-dev gcc

# Use the passed index URL correctly (now available via ENV)
RUN pip install --no-cache-dir --no-index --find-links=/wheelhouse $PIP_FLAGS -r requirements.txt

COPY . /app

EXPOSE 5000
ENV PYTHONPATH="/app:/server:/data"

CMD ["python", "run.py"]