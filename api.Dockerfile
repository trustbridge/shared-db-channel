FROM python:3.6

# don't create __pycache__ files
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /src

COPY ./requirements.txt .
RUN pip install -r requirements.txt
