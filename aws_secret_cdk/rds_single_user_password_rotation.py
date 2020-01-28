import os
import re

from aws_cdk import core, aws_iam, aws_secretsmanager, aws_s3_deployment, aws_s3, aws_kms
from aws_cdk.aws_lambda import Runtime, Code
from aws_lambda.cloud_formation.lambda_aws_cdk import LambdaFunction
from aws_secret_cdk.vpc_parameters import VPCParameters


class RdsSingleUserPasswordRotation:
    """
    Class which creates a lambda function responsible for RDS single user secret (password) rotation.
    """
    LAMBDA_BACKEND_DEPLOYMENT_PACKAGE = 'SecretsManagerRDSSingleUserRotation.zip'

    def __init__(
            self,
            stack: core.Stack,
            prefix: str,
            secret: aws_secretsmanager.Secret,
            kms_key: aws_kms.IKey,
            vpc_parameters: VPCParameters
    ) -> None:
        """
        Constructor.

        :param stack: A stack in which resources should be created.
        :param prefix: A prefix to give for every resource.
        :param secret: A secret instance which the lambda function should be able to access.
        :param kms_key: Custom or managed KMS key for secret encryption which the
        lambda function should be able to access.
        :param vpc_parameters: VPC parameters for resource (e.g. lambda rotation function) configuration.
        """
        self.rotation_lambda_role = aws_iam.Role(
            scope=stack,
            id=prefix + 'RdsSecretRotationLambdaRole',
            role_name=prefix + 'RdsSecretRotationLambdaRole',
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.ServicePrincipal("secretsmanager.amazonaws.com"),
        ),
            inline_policies={
                prefix + 'RdsSecretRotationLambdaPolicy': aws_iam.PolicyDocument(
                    statements=[
                        # Secrets are KMS encrypted.
                        # Therefore the lambda function should be able to get this value.
                        aws_iam.PolicyStatement(
                            actions=[
                                'kms:GetSecretValue',
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[kms_key.key_arn]
                        ),
                        # We enforce lambdas to run in a VPC.
                        # Therefore lambdas need some network interface permissions.
                        aws_iam.PolicyStatement(
                            actions=[
                                'ec2:CreateNetworkInterface',
                                'ec2:ModifyNetworkInterface',
                                'ec2:DeleteNetworkInterface',
                                'ec2:AttachNetworkInterface',
                                'ec2:DetachNetworkInterface',
                                'ec2:DescribeNetworkInterfaces',
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=['*']
                        ),
                        # Lambda needs to call secrets manager to get secret value in order to update database password.
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:DescribeSecret",
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:PutSecretValue",
                                "secretsmanager:UpdateSecretVersionStage"
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[secret.secret_arn]
                        ),
                        # Not exactly sure about this one.
                        # Despite that, this policy does not impose any security risks.
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetRandomPassword"
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=['*']
                        )
                    ]
                )
            },
        )

        bucket_name = self.__convert(prefix + 'RdsSecretRotationLambdaDeploymentBucket')
        bucket_deployment = self.__convert(bucket_name + 'Deployment')

        dir_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dir_path, 'packages')
        deployment_files = aws_s3_deployment.Source.asset(path)

        self.rotation_lambda_deployment_bukcet = aws_s3.Bucket(
            scope=stack,
            id=bucket_name,
            access_control=aws_s3.BucketAccessControl.PRIVATE,
            bucket_name=bucket_name,
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # Deploy lambda function source code.
        self.rotation_lambda_deployment = aws_s3_deployment.BucketDeployment(
            scope=stack,
            id=bucket_deployment,
            destination_bucket=self.rotation_lambda_deployment_bukcet,
            sources=[deployment_files]
        )

        # Create a lambda function responsible for rds password rotation.
        self.rotation_lambda_function = LambdaFunction(
            scope=stack,
            prefix=prefix,
            description='Description',
            memory=128,
            timeout=60,
            handler='lambda_function.lambda_handler',
            runtime=Runtime.PYTHON_2_7,
            role=self.rotation_lambda_role,
            env={
                'SECRETS_MANAGER_ENDPOINT': f'https://secretsmanager.{stack.region}.amazonaws.com'
            },
            security_groups=vpc_parameters.rotation_lambda_security_groups,
            subnets=vpc_parameters.rotation_lambda_subnets,
            vpc=vpc_parameters.rotation_lambda_vpc,
            source_code=Code.from_bucket(
                bucket=self.rotation_lambda_deployment_bukcet,
                key=self.LAMBDA_BACKEND_DEPLOYMENT_PACKAGE,
            )
        ).lambda_function

        # Add some dependencies to ensure the right creation order.
        # Mostly this is not necessary because CloudFormation is smart enough.
        self.rotation_lambda_function.node.add_dependency(self.rotation_lambda_deployment_bukcet)
        self.rotation_lambda_function.node.add_dependency(self.rotation_lambda_deployment)
        self.rotation_lambda_function.node.add_dependency(self.rotation_lambda_role)

    @staticmethod
    def __convert(name: str) -> str:
        """
        Converts CamelCase string to pascal-case where underscores are dashes.
        This is required due to S3 not supporting capital letters or underscores.
        """
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
