FROM ubuntu:latest

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --yes python3.12
RUN apt-get update && apt-get install --yes python3-pip

# workaround for installing python packages outside of venv
RUN rm /usr/lib/python3.12/EXTERNALLY-MANAGED

RUN pip install -U rdflib
RUN pip install -U PyGithub
RUN pip install -U markdown
RUN pip install -U bs4
RUN pip install -U flask
RUN pip install -U flask-cors
RUN pip install -U fire
RUN pip install -U pyshacl
RUN pip install -U numpy
RUN pip install -U pandas
RUN pip install -U matplotlib
RUN pip install -U brokenaxes

VOLUME [ "/src" ]
WORKDIR /src

EXPOSE 5000
ENV HOST=0.0.0.0
