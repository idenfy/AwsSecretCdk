## AWS Secret Cdk

A library to create and provision secrets by 
[AWS SecretsManager](https://aws.amazon.com/secrets-manager/). 
This library makes it easy to create secrets with 
[secret rotation](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html).

#### Remarks

The project is written by [Laimonas Sutkus](https://github.com/laimonassutkus) 
and is owned by [iDenfy](https://github.com/idenfy). This is an open source
library intended to be used by anyone. [iDenfy](https://github.com/idenfy) aims
to share its knowledge and educate market for better and more secure IT infrastructure.

#### Related technology

This project utilizes the following technology:

- *AWS* (Amazon Web Services).
- *AWS CDK* (Amazon Web Services Cloud Development Kit).
- *AWS CloudFormation*.
- *AWS SecretsManager*.

#### Assumptions

This library project assumes the following:

- You have knowledge in AWS (Amazon Web Services).
- You have knowledge in AWS CloudFormation and AWS SecretsManager.
- You are managing your infrastructure with AWS CDK.
- You are writing AWS CDK templates with a python language.

#### Install

The project is built and uploaded to PyPi. Install it by using pip.

```bash
pip install aws-secret-cdk
```

Or directly install it through source.

```bash
./build.sh -ic
```

#### Description

SecretsManager is a great AWS service to manage your secrets e.g. database
password. It is really easy to create and configure a secret through AWS
console (UI). However it is notoriously difficult to create and manage 
secrets through CloudFormation. You need to create a lambda function, which 
executes secret rotation, ensure correct lambda function permissions and
security groups, correctly configure secrets themselves with correct templates, etc.
All in all, it is really painful. This library tackles this problem. In a 
nutshell, you just provide a database, for which the secret should be applied,
and some other params. And that's it! You're good to go.

#### Examples

Here are the examples on how to use this library with various scenarios.

##### RDS Single user rotation secret example

To create a SSM Secret for an RDS database with 30 days rotation, create an
`RdsSecret` instance.

```python
from aws_cdk.core import Stack
from aws_cdk.aws_ec2 import Vpc
from aws_cdk import aws_rds
from aws_secret_cdk.rds_secret import RdsSecret
from aws_secret_cdk.vpc_parameters import VPCParameters

class MyStack(Stack):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Suppose you have defined a VPC.
        self.vpc = Vpc(**kwargs)

        # Suppose you have a database (or a cluster).
        self.database = aws_rds.CfnDBCluster(**kwargs)
        
        # Now simply create a secret with 30 day rotation.
        self.rds_secret = RdsSecret(
            stack=self,
            prefix='MyResourcesPrefix',
            vpc_parameters=VPCParameters(
                rotation_lambda_vpc=self.vpc,
                rotation_lambda_security_groups=[
                    # Your SG's.
                ],
                # NOTE! Ensure that your private subnets have a NAT gateway
                # or have a VPC endpoint in order to reach SecretsManager
                # API which is outside your own VPC.
                rotation_lambda_subnets=self.vpc.private_subnets
            ),
            database=self.database
        )
```

And that's pretty much it. From now own your database password will be stored
in a SecretsManager and will be roted every 30 days.

##### Using the new secret

In order to retrieve the secret, use this sample code below.

```python
# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:   
# https://aws.amazon.com/developers/getting-started/python/

import boto3
import base64
from botocore.exceptions import ClientError


def get_secret():

    secret_name = "test"
    region_name = "eu-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # Some error happened here. Log it / handle it / raise it.
        raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])
            
        return secret
```