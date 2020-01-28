## AWS Secret Cdk

An AWS CDK library to manage SecretsManager secrets easily.

#### Description

SecretsManager is a great AWS service to manage your secrets e.g. database
password. It is really easy to create and configure a secret through AWS
console (UI). However it is NOTORIOUSLY difficult to create and manage 
secrets through CloudFormation. You need to create a lambda function, which 
executes secret rotation, ensure correct lambda function permissions and
security groups, correctly configure secrets themselves with correct templates, etc.
All in all, it is really painful. This library tackles this problem. In a 
nutshell, you just provide a database, for which the secret should be applied,
and some other params. And that's it! You're good to go.

#### Assumptions

This Cdk library assumes the following:
- You have knowledge in AWS
- You have knowledge in AWS CloudFormation and AWS CDK for creating infrastructure-as-a-code.

#### How to use

```python
# Suppose you have a stack (core.Stack) or an app (core.App) which are constructs.
from aws_cdk.core import Stack
from aws_cdk.aws_ec2 import Vpc
class MyStack(Stack):
    def __init__(self):
        super().__init__(...)
        
        # Suppose you have defined a VPC:
        self.vpc = Vpc(...)

        # Suppose you have a database (or a cluster)
        from aws_cdk import aws_rds
        self.database = aws_rds.CfnDBCluster(...)
        
        # Now simply create a secret with 30 day rotation.
        from aws_secret_cdk.rds_secret import RdsSecret
        from aws_secret_cdk.vpc_parameters import VPCParameters
        self.rds_secret = RdsSecret(
            stack=self,
            prefix='MyResourcesPrefix',
            vpc_parameters=VPCParameters(
                rotation_lambda_vpc=self.vpc,
                rotation_lambda_security_groups=[
                    # Your SG's.
                ],
                rotation_lambda_subnets=self.vpc.private_subnets
            ),
            database=self.database
        )
```
