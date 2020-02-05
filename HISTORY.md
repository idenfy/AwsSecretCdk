# Release history

#### 5.0.0
Restructure project having in mind that different types of rotations are 
possible e.g. DynamoDB secret rotation, or RDS multi user secret rotation.
Narrowed down the permissions required for rotation. With this version 
an aws-secret-cdk package is fully functional and available to be used.

#### 4.0.0
Do not enforce KMS CMKs. Use assets to deploy lambda function source code
instead of S3 buckets. Use better prefixes. Refactor lambda function source code
to support initial passwords on existing databases. Warning: loosened permissions.
Next commit should fix them.

#### 3.0.1
Update README.

#### 3.0.0
Shorten lambda bucket name.

#### 2.0.3
Consistent naming.

#### 2.0.2
Add docstrings.

#### 2.0.1
Fix target types and target arns.

#### 2.0.0
General bug fixes. Add permission for KMS key resource. Add secret template.

#### 1.0.9
Add secrets manager as a valid principal to invoke rotation lambda.

#### 1.0.8
Add S3 removal policy.

#### 1.0.7
Don't use managed policies.

#### 1.0.6
Aws Lambda dependency update.

#### 1.0.5
Aws Lambda dependency update.

#### 1.0.4
Dont create Code class instance.

#### 1.0.3
Move packages into main package.

#### 1.0.2
Fix manifest file.

#### 1.0.1
Ensure bucket and bucket deployment has different names.

#### 1.0.0
Initial commit. Add ability to create RDS secret and rotate it every 30 days.
