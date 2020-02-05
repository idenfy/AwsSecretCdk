from setuptools import setup, find_packages

with open('README.md') as readme_file:
    README = readme_file.read()

with open('HISTORY.md') as history_file:
    HISTORY = history_file.read()

setup(
    name='aws_secret_cdk',
    version='5.0.0',
    license='GNU GENERAL PUBLIC LICENSE Version 3',
    packages=find_packages(exclude=['venv', 'test']),
    description='Package to create a SecretsManager\'s secret with auto rotation.',
    long_description=README + '\n\n' + HISTORY,
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        'aws-cdk.core',
        'aws-cdk.aws_iam',
        'aws-cdk.aws_ec2',
        'aws-cdk.aws_lambda',
        'aws-cdk.aws_rds',
        'aws-cdk.aws_secretsmanager',
        'aws-cdk.aws_s3_deployment',
        'aws-lambda>=2.1.2,<3.0.0'
    ],
    author='Laimonas Sutkus',
    author_email='laimonas@idenfy.com,laimonas.sutkus@gmail.com',
    keywords='AWS CDK CloudFormation SecretsManager Infrastructure Cloud DevOps',
    url='https://github.com/idenfy/AwsSecretCdk',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: OS Independent',
    ],
)
