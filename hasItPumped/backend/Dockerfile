FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY . .

# Install dependencies directly (not in a virtual environment)
RUN poetry config virtualenvs.create false \
    && poetry install --without dev

# Run the application
EXPOSE 8000
CMD ["uvicorn", "src.solana_token_api.main:app", "--host", "0.0.0.0", "--port", "10000"]