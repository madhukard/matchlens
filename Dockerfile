FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY pyproject.toml ./
COPY matchlens ./matchlens
RUN pip install --no-cache-dir --no-deps . && useradd --uid 10001 --create-home matchlens
USER matchlens
EXPOSE 8000
CMD ["uvicorn", "matchlens.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
