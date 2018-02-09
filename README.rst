.. This is included in docs/index.rst
.. _boto3: https://boto3.readthedocs.io/en/latest/
.. _ec2-metadata: https://github.com/adamchainz/ec2-metadata
ec2helper - A python lib for common EC2 tasks
=============================================

ec2helper basically is a wrapper around boto3_ and ec2-metadata_.
Its intention is to simplify common tasks you want to do in the context of
"this EC2 instance we're on", like retrieving or modifying this instance's
tags.
