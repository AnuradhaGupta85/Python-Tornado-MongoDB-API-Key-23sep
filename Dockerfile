FROM python:3.13.5-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home appuser
COPY . .
RUN chown -R appuser:appuser /app
USER appuser
ENV PORT=8000
EXPOSE 8000
CMD ["python3", "main.py"]
