from aws_cdk import core, aws_kms


class SecretKey:
    def __init__(
            self,
            scope: core.Construct,
            prefix: str,
    ):
        self.__kms_key = aws_kms.Key(
            scope=scope,
            id=prefix + 'SecretEncryptionKey',
            alias=prefix + 'SecretEncryptionKey',
            description=f'Key used to encrypt {prefix} secret.',
            enabled=True,
            enable_key_rotation=True,
            removal_policy=core.RemovalPolicy.DESTROY
        )

    def get_kms_key(self) -> aws_kms.Key:
        return self.__kms_key
