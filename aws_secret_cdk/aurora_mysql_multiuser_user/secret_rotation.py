from aws_secret_cdk.base_secret_rotation import BaseSecretRotation


class SecretRotation(BaseSecretRotation):
    def __init__(self) -> None:
        super().__init__()

        raise NotImplementedError()
