# Demo: a minimal Pulumi Component that creates a **public** S3 static website.
# Usage:
#   1) Set AWS creds; create a new Pulumi project/stack.
#   2) Put this file in your program, then:
#        static = StaticPage("demo", {"index_content": "<h1>Hello Pulumi!</h1>"})
#        pulumi.export("url", static.endpoint)
#   3) pulumi up → open the printed URL.
#
# NOTE: This makes bucket objects world-readable for demo purposes.

import json
from typing import Optional, TypedDict

import pulumi
from pulumi import ResourceOptions
from pulumi_aws import s3

class StaticPageArgs(TypedDict):
    pages: pulumi.Input[dict[str, str]]

class StaticPage(pulumi.ComponentResource):
    endpoint: pulumi.Output[str]
    """Public website URL (e.g., http://<bucket>.s3-website-<region>.amazonaws.com)."""

    def __init__(self,
                 name: str,
                 args: StaticPageArgs,
                 opts: Optional[ResourceOptions] = None) -> None:

        # Register this as a custom component so Pulumi treats it as one logical resource.
        super().__init__('static-page-component:index:StaticPage', name, {}, opts)

        # Create a bucket
        bucket = s3.Bucket(name)

        bucket_website = s3.BucketWebsiteConfiguration(
            f"{name}-website",
            bucket=bucket.bucket,
            index_document={"suffix": "index.html"},
        )


        # s3.BucketObject(
        #     f"{name}-index",
        #     bucket=bucket.bucket,
        #     key="index.html",
        #     content=args["index_content"],
        #     content_type="text/html",
        # )

        for filename, content in args['pages'].items():
            s3.BucketObject(
                f'{name}-{filename.replace(".", "-")}',
                bucket=bucket.bucket,
                key=filename,               # filename becomes S3 object key
                content=content,            # HTML content
                content_type='text/html',
                opts=ResourceOptions(parent=bucket)
            )


        s3.BucketPublicAccessBlock(
            f"{name}-public-access-block",
            bucket=bucket.id,
            block_public_acls=False,
        )


        s3.BucketPolicy(
            f"{name}-policy",
            bucket=bucket.bucket,
            policy=bucket.bucket.apply(lambda b: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{b}/*",
                }],
            })),
        )

        self.endpoint = bucket_website.website_endpoint
        self.register_outputs({"endpoint": self.endpoint})
