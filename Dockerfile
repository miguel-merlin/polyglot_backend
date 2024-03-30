FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 80

ENV NAME ob-sample-fast-api-docker

LABEL maintainer="mmerlin mmerlin@stevens.edu"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]DockerfileCopy code