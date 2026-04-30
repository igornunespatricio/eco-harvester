#!/bin/sh

set -e

echo "Waiting for MinIO to be ready..."

echo "Using credentials: $MINIO_ROOT_USER / $MINIO_ROOT_PASSWORD"
echo "Buckets to create: $BUCKETS"

# wait until MinIO responds
until mc alias set myminio http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"; do
  echo "MinIO not ready yet..."
  sleep 2
done

# echo "Creating bucket..."

# mc mb myminio/my-bucket || echo "Bucket already exists"

# mc anonymous set public myminio/my-bucket || true

# Convert comma-separated list into space-separated
BUCKETS=$(echo "$BUCKETS" | tr ',' ' ')

for BUCKET in $BUCKETS; do
  echo "Creating bucket: $BUCKET"
  mc mb myminio/$BUCKET || echo "Bucket $BUCKET already exists"

  # Optional: make them public
  mc anonymous set public myminio/$BUCKET || true
done

echo "MinIO initialization complete"