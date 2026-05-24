import boto3
from botocore.client import Config
from io import BytesIO


class MinioS3Client:
    def __init__(self, endpoint, access_key, secret_key, region="us-east-1"):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    def bucket_exists(self, bucket_name: str) -> bool:
        try:
            self.s3.head_bucket(Bucket=bucket_name)
            return True
        except Exception:
            return False

    def create_bucket(self, bucket_name: str):
        if not self.bucket_exists(bucket_name):
            self.s3.create_bucket(Bucket=bucket_name)

    def upload_file(self, bucket_name: str, object_name: str, file_path: str):
        self.s3.upload_file(file_path, bucket_name, object_name)

    def download_file(self, bucket_name: str, object_name: str, file_path: str):
        self.s3.download_file(bucket_name, object_name, file_path)

    def upload_fileobj(self, fileobj, bucket_name: str, key: str):
        """
        Upload a file-like object to S3/MinIO.

        :param fileobj: file-like object (must be opened in binary mode)
        :param bucket_name: target bucket
        :param key: object name in bucket
        """
        self.s3.upload_fileobj(fileobj, bucket_name, key)

    def get_fileobj(self, bucket_name: str, key: str) -> BytesIO:
        """Download an object from S3/MinIO into a BytesIO object."""
        buf = BytesIO()
        self.s3.download_fileobj(bucket_name, key, buf)
        buf.seek(0)
        return buf

    def list_partition_files(
        self, bucket_name: str, partition_prefix: str
    ) -> list[dict]:
        """
        Return all objects under a given partition prefix with full metadata.

        :param bucket_name: the bucket to query
        :param partition_prefix: the partition path, e.g. "year=2024/month=01/"
        :return: list of S3 object dicts with keys: Key, LastModified, ETag, Size, StorageClass
        """
        objects = []
        paginator = self.s3.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=bucket_name, Prefix=partition_prefix):
            for obj in page.get("Contents", []):
                objects.append(obj)

        return objects

    def get_latest_file(self, bucket_name: str, partition_prefix: str) -> dict | None:
        """Return the most recently modified object in a partition, or None if empty."""
        files = self.list_partition_files(bucket_name, partition_prefix)
        return max(files, key=lambda o: o["LastModified"]) if files else None

    def partition_has_files(self, bucket_name: str, partition_prefix: str) -> bool:
        """
        Check if any files exist under a given partition prefix.
        Returns True if at least one file is found, False otherwise.
        """
        return len(self.list_partition_files(bucket_name, partition_prefix)) > 0


if __name__ == "__main__":
    # Example usage
    client = MinioS3Client(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
    )

    bucket_name = "raw"
    from io import BytesIO

    data = BytesIO(b"hello from memory")

    client.upload_fileobj(data, bucket_name, "hello.txt")
