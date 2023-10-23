FROM node:10
LABEL org.opencontainers.image.source="https://github.com/podaac/hydrocron-api"
RUN npm install forever -g

ENV project_dir /project
ENV app_dir ${project_dir}/app
ENV config_dir ${project_dir}/config

RUN mkdir ${project_dir} ${app_dir} ${config_dir}
WORKDIR ${app_dir}

COPY package*.json ./
RUN npm install
COPY . .

CMD ${app_dir}/docker/docker-start-command