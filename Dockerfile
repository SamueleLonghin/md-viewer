FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]
