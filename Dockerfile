FROM python:3.12.9

WORKDIR /app

RUN apt-get update && apt-get install -y \
  tesseract-ocr \
  libtesseract-dev \
  poppler-utils \
  antiword \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
