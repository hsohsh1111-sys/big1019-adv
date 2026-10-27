FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
RUN useradd --create-home --uid 10001 appuser
USER appuser
# CI가 docker build --build-arg APP_VERSION=<커밋 SHA> 로 넘겨주면 화면·/health 에 표시됨
ARG APP_VERSION=local
ENV APP_VERSION=${APP_VERSION}
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
