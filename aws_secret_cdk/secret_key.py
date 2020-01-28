from aws_cdk import core, aws_kms


class SecretKey:
    """
    Class which creates KMS CMK.
    """
    def __init__(
            self,
            stack: core.Stack,
            prefix: str,
    ):
        """
        Constructor.

        :param scope: Usually a stack in which this resource should be added.
        :param prefix: Prefix for KMS name.
        """
        self.__kms_key = aws_kms.Key(
            scope=stack,
            id=prefix + 'SecretEncryptionKey',
            alias=prefix + 'SecretEncryptionKey',
            description=f'Key used to encrypt {prefix} secret.',
            enabled=True,
            enable_key_rotation=True,
            removal_policy=core.RemovalPolicy.DESTROY
        )

    def get_kms_key(self) -> aws_kms.Key:
        """
        Returns a KMS key instance.

        :return: KMS CMK.
        """
        return self.__kms_key
