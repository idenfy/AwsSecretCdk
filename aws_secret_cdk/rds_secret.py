import json

from typing import Optional, Union
from aws_cdk import aws_secretsmanager, core, aws_kms, aws_lambda, aws_rds
from aws_cdk.aws_secretsmanager import SecretStringGenerator
from aws_secret_cdk.rds_single_user_password_rotation import RdsSingleUserPasswordRotation
from aws_secret_cdk.secret_key import SecretKey
from aws_secret_cdk.vpc_parameters import VPCParameters


class RdsSecret:
    def __init__(
            self,
            stack: core.Stack,
            prefix: str,
            vpc_parameters: VPCParameters,
            database: Union[aws_rds.CfnDBInstance, aws_rds.CfnDBCluster],
            kms_key: Optional[aws_kms.Key] = None
    ) -> None:
        """
        Constructor.

        :param stack:
        :param prefix:
        :param vpc_parameters:
        :param database:
        :param kms_key:
        """
        self.kms_key = kms_key or SecretKey(stack, prefix).get_kms_key()

        # This template is sent to a lambda function that executes secret rotation.
        # If you choose to change this template, make sure you change lambda
        # function source code too.
        template = {
            'engine': database.engine,
            'host': database.attr_endpoint_address,
            'username': database.master_username,
            'password': database.master_user_password,
            'dbname': None,
            'port': database.port
        }

        # Instances and clusters have different attributes.
        if isinstance(database, aws_rds.CfnDBInstance):
            template['dbname'] = database.db_name
        elif isinstance(database, aws_rds.CfnDBCluster):
            template['dbname'] = database.database_name

        self.secret = aws_secretsmanager.Secret(
            scope=stack,
            id=prefix + 'RdsSecret',
            description=f'A secret for {prefix}.',
            encryption_key=self.kms_key,
            generate_secret_string=SecretStringGenerator(
                generate_string_key='password',
                secret_string_template=json.dumps(template)
            ),
            secret_name=prefix + 'RdsSecret'
        )

        # Make sure database is fully deployed and configured before creating a secret for it.
        self.secret.node.add_dependency(database)

        self.secret_rotation = RdsSingleUserPasswordRotation(
            stack=stack,
            prefix=prefix,
            secret=self.secret,
            kms_key=kms_key,
            vpc_parameters=vpc_parameters
        )

        self.sm_invoke_permission = aws_lambda.CfnPermission(
            scope=stack,
            id=prefix + 'SecretsManagerInvokePermission',
            action='lambda:InvokeFunction',
            function_name=self.secret_rotation.rotation_lambda_function.function_name,
            principal="secretsmanager.amazonaws.com",
        )

        # Make sure lambda function is created before making its permissions.
        self.sm_invoke_permission.node.add_dependency(self.secret_rotation.rotation_lambda_function)

        self.rotation_schedule = aws_secretsmanager.RotationSchedule(
            scope=stack,
            id=prefix + 'RotationSchedule',
            secret=self.secret,
            rotation_lambda=self.secret_rotation.rotation_lambda_function,
            automatically_after=core.Duration.days(30)
        )

        # Make sure invoke permission for secrets manager is created before creating a schedule.
        self.rotation_schedule.node.add_dependency(self.sm_invoke_permission)

        # Instances and clusters have different arns.
        if isinstance(database, aws_rds.CfnDBInstance):
            target_arn = f'arn:aws:rds:eu-west-1:{stack.account}:db:{database.db_instance_identifier}'
        elif isinstance(database, aws_rds.CfnDBCluster):
            target_arn = f'arn:aws:rds:eu-west-1:{stack.account}:cluster:{database.db_cluster_identifier}'
        else:
            raise TypeError('Unsupported DB type.')

        # Instances and clusters should have different attachment types.
        if isinstance(database, aws_rds.CfnDBInstance):
            target_type = 'AWS::RDS::DBInstance'
        elif isinstance(database, aws_rds.CfnDBCluster):
            target_type = 'AWS::RDS::DBCluster'
        else:
            raise TypeError('Unsupported DB type.')

        self.target_db_attachment = aws_secretsmanager.CfnSecretTargetAttachment(
            scope=stack,
            id=prefix + 'TargetRdsAttachment',
            secret_id=self.secret.secret_arn,
            target_id=target_arn,
            target_type=target_type
        )
