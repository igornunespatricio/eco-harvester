#!/bin/sh

set -e

echo "Waiting for MinIO to be ready..."
echo "Using credentials: $MINIO_ROOT_USER / $MINIO_ROOT_PASSWORD"
echo "BUCKET to create: $BUCKET"

until mc alias set myminio http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "MinIO not ready yet..."
  sleep 2
done

echo "Creating bucket: $BUCKET"
mc mb myminio/$BUCKET || echo "Bucket $BUCKET already exists"
mc anonymous set public myminio/$BUCKET || true

echo "MinIO initialization complete"