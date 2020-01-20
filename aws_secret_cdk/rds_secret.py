from typing import Optional
from aws_cdk import aws_secretsmanager, core, aws_kms
from aws_cdk.aws_secretsmanager import SecretStringGenerator, ISecretAttachmentTarget
from aws_secret_cdk.rds_single_user_password_rotation import RdsSingleUserPasswordRotation
from aws_secret_cdk.secret_key import SecretKey
from aws_secret_cdk.vpc_parameters import VPCParameters


class RdsSecret:
    def __init__(
            self,
            stack: core.Stack,
            prefix: str,
            vpc_parameters: VPCParameters,
            database: ISecretAttachmentTarget,
            kms_key: Optional[aws_kms.Key] = None
    ):
        self.kms_key = kms_key or SecretKey(stack, prefix).get_kms_key()

        self.secret = aws_secretsmanager.Secret(
            scope=stack,
            id=prefix + 'RdsSecret',
            description=f'A secret for {prefix}.',
            encryption_key=self.kms_key,
            generate_secret_string=SecretStringGenerator(),
            secret_name=prefix + 'RdsSecret'
        )

        self.secret_rotation = RdsSingleUserPasswordRotation(
            stack=stack,
            prefix=prefix,
            secret=self.secret,
            vpc_parameters=vpc_parameters
        )

        self.secret.add_rotation_schedule(
            id=prefix + 'RdsSecretRotation',
            rotation_lambda=self.secret_rotation.rotation_lambda_function,
            automatically_after=core.Duration.days(30)
        )

        self.secret.attach(database)
