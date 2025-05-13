FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl \
  && curl -LO https://dl.k8s.io/release/$(curl -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl \
  && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
  && rm kubectl

RUN pip install tqdm

COPY dump_k8s_resources.py /app/dump_k8s_resources.py
WORKDIR /app

CMD ["python", "dump_k8s_resources.py"]
