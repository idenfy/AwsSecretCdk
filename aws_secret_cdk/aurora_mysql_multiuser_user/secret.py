from aws_secret_cdk.base_secret import BaseSecret


class Secret(BaseSecret):
    def __init__(self) -> None:
        super().__init__()

        raise NotImplementedError()
