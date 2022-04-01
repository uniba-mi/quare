FROM ubuntu:latest

RUN apt-get update && apt-get install --yes openjdk-11-jre 

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install --yes python3.10
RUN apt-get update && apt-get install --yes python3-pip

RUN pip install -U rdflib
RUN pip install -U owlready2
RUN pip install -U PyGithub
RUN pip install -U markdown
RUN pip install -U bs4
RUN pip install -U flask
RUN pip install -U flask-cors
RUN pip install -U fire
RUN pip install -U pyshacl
RUN pip install -U numpy
RUN pip install -U matplotlib

VOLUME [ "/src" ]
WORKDIR /src

EXPOSE 5000
ENV HOST=0.0.0.0
