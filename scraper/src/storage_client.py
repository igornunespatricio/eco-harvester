import boto3
from botocore.client import Config


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
