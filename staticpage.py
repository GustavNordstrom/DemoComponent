import json
import pulumi
from pulumi_aws import s3

class StaticPage(pulumi.ComponentResource):
    def __init__(self, name: str, index_content: str, opts: pulumi.ResourceOptions | None = None):
        super().__init__("example:StaticPage", name, None, opts)

        bucket = s3.Bucket(name)

        website = s3.BucketWebsiteConfiguration(
            f"{name}-website",
            bucket=bucket.bucket,
            index_document={"suffix": "index.html"},
        )

        s3.BucketObject(
            f"{name}-index",
            bucket=bucket.bucket,
            key="index.html",
            content=index_content,
            content_type="text/html",
        )

        policy = bucket.bucket.apply(lambda b: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": [f"arn:aws:s3:::{b}/*"],
            }],
        }))

        s3.BucketPolicy(f"{name}-policy", bucket=bucket.bucket, policy=policy)

        self.endpoint = website.website_endpoint
        self.register_outputs({"endpoint": self.endpoint})
