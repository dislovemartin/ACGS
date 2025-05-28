# backend/auth_service/Dockerfile
FROM python:3.10-alpine

WORKDIR /app

COPY ./requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app/ /app/app/
COPY ../shared/ /app/shared/ # Path to shared from service's perspective in build context

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 