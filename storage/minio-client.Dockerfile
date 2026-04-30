FROM minio/mc:RELEASE.2025-08-13T08-35-41Z-cpuv1

COPY init-minio.sh /init-minio.sh

RUN chmod +x /init-minio.sh