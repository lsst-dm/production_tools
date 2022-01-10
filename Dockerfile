FROM continuumio/miniconda3:4.10.3

RUN apt-get --allow-releaseinfo-change update && \
    apt-get install -y \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN conda install -y -q pip wheel


COPY requirements.txt /app/production-tools/requirements.txt
RUN pip install -r /app/production-tools/requirements.txt
RUN pip install pydantic # Temporary

COPY . /app/production-tools/

RUN pip install -e /app/production-tools/

WORKDIR /app/production-tools/

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "lsst.production.tools:create_app()"]
