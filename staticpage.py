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
    index_content: pulumi.Input[str]
    """HTML content for index.html (e.g., '<h1>Hello</h1>')."""

class StaticPage(pulumi.ComponentResource):
    endpoint: pulumi.Output[str]
    """Public website URL (e.g., http://<bucket>.s3-website-<region>.amazonaws.com)."""

    def __init__(self,
                 name: str,
                 args: StaticPageArgs,
                 opts: Optional[ResourceOptions] = None) -> None:

        # Register this as a custom component so Pulumi treats it as one logical resource.
        super().__init__('static-page-component:index:StaticPage', name, {}, opts)


        bucket = s3.Bucket(name)

        # 2) Turn on S3 static website hosting with index.html as the default doc.
        bucket_website = s3.BucketWebsiteConfiguration(
            f'{name}-website',
            bucket=bucket.bucket,                       # bucket name string
            index_document={"suffix": "index.html"},    # default document
            opts=ResourceOptions(parent=bucket))

        # 3) Upload the index.html object into the bucket with the provided content.
        s3.BucketObject(
            f'{name}-index-object',
            bucket=bucket.bucket,
            key='index.html',
            content=args.get("index_content"),          # the page body
            content_type='text/html',
            opts=ResourceOptions(parent=bucket))


        '''
        Makes the S3 bucket publicly readable (GET only) so it can serve a static website.
        '''
        bucket_public_access_block = s3.BucketPublicAccessBlock(
            f'{name}-public-access-block',
            bucket=bucket.id,                           # bucket ID (not name)
            block_public_acls=False,                    # permit public ACLs
            opts=ResourceOptions(parent=bucket))

        s3.BucketPolicy(
            f'{name}-bucket-policy',
            bucket=bucket.bucket,
            policy=bucket.bucket.apply(_allow_getobject_policy),
            opts=ResourceOptions(parent=bucket, depends_on=[bucket_public_access_block]))

        # Expose the website endpoint as this component's output.
        self.endpoint = bucket_website.website_endpoint

        # Tell Pulumi which outputs represent this component so it waits for them.
        self.register_outputs({
            'endpoint': bucket_website.website_endpoint
        })


def _allow_getobject_policy(bucket_name: str) -> str:
    """Return a bucket policy JSON that allows public reads of all objects."""
    return json.dumps({
        'Version': '2012-10-17',
        'Statement': [
            {
                'Effect': 'Allow',
                'Principal': '*',
                'Action': ['s3:GetObject'],
                'Resource': [
                    f'arn:aws:s3:::{bucket_name}/*',  # allow GET for any key under the bucket
                ],
            },
        ],
    })
