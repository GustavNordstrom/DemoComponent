import json
from typing import Optional, TypedDict

import pulumi
from pulumi import ResourceOptions
from pulumi_aws import s3

class StaticPageArgs(TypedDict):
    pages: pulumi.Input[dict[str, str]]

class StaticPage(pulumi.ComponentResource):
    endpoint: pulumi.Output[str]

    def __init__(self,
                 name: str,
                 args: StaticPageArgs,
                 opts: Optional[ResourceOptions] = None) -> None:

        # Register this as a custom component so Pulumi treats it as one logical resource.
        super().__init__('static-page-component:index:StaticPage', name, {}, opts)

        # Create a bucket
        bucket = s3.Bucket(name)

        for filename, content in args['pages'].items():
            s3.BucketObject(
                f'{name}-{filename.replace(".", "-")}',
                bucket=bucket.bucket,
                key=filename,               # filename becomes S3 object key
                content=content,            # HTML content
                content_type='text/html',
                opts=ResourceOptions(parent=bucket)
            )

        bucket_website = s3.BucketWebsiteConfiguration(
            name,
            bucket=bucket.bucket,
            index_document={"suffix": "index.html"},
            opts=ResourceOptions(parent=bucket)
        )


        s3.BucketPublicAccessBlock(
            f"{name}-public-access-block",
            bucket=bucket.id,
            block_public_acls=False,
            opts=ResourceOptions(parent=bucket)
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
            opts=ResourceOptions(parent=bucket)
        )

        self.endpoint = bucket_website.website_endpoint
        self.register_outputs({"endpoint": self.endpoint})
