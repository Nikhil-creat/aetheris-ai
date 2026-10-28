FROM python:3.12-slim
ARG ML=0
WORKDIR /app
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt && if [ "$ML" = "1" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi && useradd -m app
COPY . .
USER app
EXPOSE 8000
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000"]
