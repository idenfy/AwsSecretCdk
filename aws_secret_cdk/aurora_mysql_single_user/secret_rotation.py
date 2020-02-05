import os
import re

from typing import Optional, Union
from aws_cdk import core, aws_iam, aws_secretsmanager, aws_kms, aws_rds
from aws_cdk.aws_lambda import Runtime, Code
from aws_lambda.cloud_formation.lambda_aws_cdk import LambdaFunction
from aws_secret_cdk.base_secret_rotation import BaseSecretRotation
from aws_secret_cdk.vpc_parameters import VPCParameters


class SecretRotation(BaseSecretRotation):
    """
    Class which creates a lambda function responsible for RDS single user secret (password) rotation.
    """
    LAMBDA_BACKEND_DEPLOYMENT_PACKAGE = 'package_src'

    def __init__(
            self,
            stack: core.Stack,
            prefix: str,
            secret: aws_secretsmanager.Secret,
            vpc_parameters: VPCParameters,
            database: Union[aws_rds.CfnDBInstance, aws_rds.CfnDBCluster],
            kms_key: Optional[aws_kms.IKey] = None,
    ) -> None:
        """
        Constructor.

        :param stack: A stack in which resources should be created.
        :param prefix: A prefix to give for every resource.
        :param secret: A secret instance which the lambda function should be able to access.
        :param vpc_parameters: VPC parameters for resource (e.g. lambda rotation function) configuration.
        :param kms_key: Custom or managed KMS key for secret encryption which the
        lambda function should be able to access.
        """
        super().__init__()

        self.__prefix = prefix + 'SecretRotation'

        # Read more about the permissions required to successfully rotate a secret:
        # https://docs.aws.amazon.com/secretsmanager/latest/userguide//rotating-secrets-required-permissions.html
        rotation_lambda_role_statements = [
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

        if kms_key is not None:
            rotation_lambda_role_statements.append(
                # Secrets may be KMS encrypted.
                # Therefore the lambda function should be able to get this value.
                aws_iam.PolicyStatement(
                    actions=[
                        'kms:GenerateDataKey',
                        'kms:Decrypt',
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[kms_key.key_arn],
                )
            )

        self.rotation_lambda_role = aws_iam.Role(
            scope=stack,
            id=self.__prefix + 'LambdaRole',
            role_name=self.__prefix + 'LambdaRole',
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.ServicePrincipal("secretsmanager.amazonaws.com"),
            ),
            inline_policies={
                self.__prefix + 'LambdaPolicy': aws_iam.PolicyDocument(
                    statements=rotation_lambda_role_statements
                )
            },
        )

        # Create rotation lambda functions source code path.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dir_path, self.LAMBDA_BACKEND_DEPLOYMENT_PACKAGE)

        # Create a lambda function responsible for rds password rotation.
        self.rotation_lambda_function = LambdaFunction(
            scope=stack,
            prefix=self.__prefix,
            description=(
                'A lambda function that is utilized by AWS SecretsManager to rotate a secret after X number of days. '
                'This lambda function connects to a given database and changes its password to whatever password was '
                'provides by AWS SecretsManager.'
            ),
            memory=128,
            timeout=60,
            handler='lambda_function.lambda_handler',
            runtime=Runtime.PYTHON_2_7,
            role=self.rotation_lambda_role,
            env={
                'SECRETS_MANAGER_ENDPOINT': f'https://secretsmanager.{stack.region}.amazonaws.com',
                'INITIAL_DATABASE_PASSWORD': database.master_user_password
            },
            security_groups=vpc_parameters.rotation_lambda_security_groups,
            subnets=vpc_parameters.rotation_lambda_subnets,
            vpc=vpc_parameters.rotation_lambda_vpc,
            source_code=Code.from_asset(path=path)
        ).lambda_function

    @staticmethod
    def __convert(name: str) -> str:
        """
        Converts CamelCase string to pascal-case where underscores are dashes.
        This is required due to S3 not supporting capital letters or underscores.
        """
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()
