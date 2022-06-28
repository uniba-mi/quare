FROM node:17

VOLUME [ "/src" ]
WORKDIR /src

COPY "./" "./"
RUN npm install

EXPOSE 8080
EXPOSE 35729
ENV HOST=0.0.0.0
