FROM apache/airflow:3.2.1
# FROM apache/airflow:3.2.0

# Get the host docker GID via build arg
ARG DOCKER_GID=1001

USER root
RUN groupadd -f -g ${DOCKER_GID} docker \
    && usermod -aG docker airflow

USER airflow