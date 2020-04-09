FROM python:3.6

# don't create __pycache__ files
ENV PYTHONDONTWRITEBYTECODE=1

COPY ./requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt

COPY . /src
WORKDIR /src

EXPOSE 5000
