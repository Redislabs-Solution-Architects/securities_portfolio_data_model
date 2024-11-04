FROM python:3.11.8-bookworm
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "price_producer/price_producer.py"]
