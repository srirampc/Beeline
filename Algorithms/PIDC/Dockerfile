# FROM julia:1.1.0-stretch
FROM julia:1.6.0-buster

LABEL maintainer="Aditya Pratapa <adyprat@vt.edu>"

USER root

WORKDIR /
COPY installPackages.jl /

# Julia libs we want

RUN julia installPackages.jl

COPY runPIDC.jl /

RUN apt-get update && apt-get install -y time

