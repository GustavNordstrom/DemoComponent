import json
import pulumi
from pulumi import ResourceOptions
from pulumi_aws import s3
from typing import Optional, TypedDict

class StaticPageArgs(TypedDict):
    index_content: pulumi.Input[str]

class StaticPage(pulumi.ComponentResource):
    # Public website URL (http://<bucket>.s3-website-<region>.amazonaws.com)
    endpoint: pulumi.Output[str]

    def __init__(self, name: str, args: StaticPageArgs, opts: Optional[ResourceOptions] = None):
        # Type token must align with your provider name ("static-page-component")
        super().__init__("static-page-component:index:StaticPage", name, None, opts)

        # Bucket
        bucket = s3.Bucket(f"{name}-bucket", opts=ResourceOptions(parent=self))

        # Enable static website hosting (index.html)
        website = s3.BucketWebsiteConfiguration(
            f"{name}-website",
            bucket=bucket.bucket,
            index_document={"suffix": "index.html"},
            opts=ResourceOptions(parent=bucket),
        )

        # Upload index.html
        s3.BucketObject(
            f"{name}-index",
            bucket=bucket.bucket,
            key="index.html",
            content=args["index_content"],
            content_type="text/html",
            opts=ResourceOptions(parent=bucket),
        )

        # Public-read policy (GET only)
        policy = bucket.bucket.apply(lambda b: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{b}/*",
            }],
        }))
        s3.BucketPolicy(
            f"{name}-policy",
            bucket=bucket.bucket,
            policy=policy,
            opts=ResourceOptions(parent=bucket),
        )

        self.endpoint = website.website_endpoint
        self.register_outputs({"endpoint": self.endpoint})
