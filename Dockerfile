FROM python:3.12

WORKDIR /app

RUN apt-get update \
    && apt-get install -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

COPY ./pyproject.toml ./

RUN poetry config virtualenvs.create false

RUN poetry install

COPY . .

EXPOSE 8000

CMD [ "poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--reload" ]