FROM python:3.12-slim

WORKDIR /app/teacher
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8100 8601
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8100"]
