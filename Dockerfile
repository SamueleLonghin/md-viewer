FROM python:3.12

WORKDIR /app

# Installa git per clonare il repository
RUN apt-get update && apt-get install -y git

# Clona il repository GitHub
RUN git clone https://github.com/SamueleLonghin/md-viewer.git /app

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip setuptools importlib-metadata
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --upgrade importlib-metadata==4.13.0


COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]
