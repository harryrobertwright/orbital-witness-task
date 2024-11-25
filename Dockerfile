FROM python:3.12-slim

WORKDIR /app

COPY Pipfile Pipfile.lock pyproject.toml /app/

RUN pip install pipenv && pipenv install --system --deploy

COPY . /app

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
