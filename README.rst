.. _boto3: https://boto3.readthedocs.io/en/latest/
.. _ec2-metadata: https://github.com/adamchainz/ec2-metadata

ec2helper - A python lib for common EC2 tasks
=============================================

ec2helper basically is a wrapper around boto3_ and ec2-metadata_.
Its intention is to simplify common tasks you want to do in the context of
*"this EC2 instance we're on"*, like retrieving or modifying this instance's
tags.

Examples
--------

.. code-block:: python
    :caption: Tag manipulation
    
    >>> from ec2helper import Instance
    >>> i = Instance()
    >>> i.tags
    {'Name': 'my-server1', 'OS': 'Ubuntu'}
    >>> i.tags = {'OS': 'Redhat', 'Stage': 'test'}
    >>> i.tags
    {'Name': 'my-server1', 'OS': 'Redhat', 'Stage': 'test'}
    >>> i.delete_tags('OS', 'Stage')
    >>> i.tags
    {'Name': 'my-server1'}

.. code-block:: python
    :caption: Force termination of autoscaling instance
    
    >>> from ec2helper import Instance
    >>> i = Instance()
    >>> i.autoscaling_healthy = False

.. code-block:: python
    :caption: Protect autoscaling instance from scale in
    
    >>> from ec2helper import Instance
    >>> i = Instance()
    >>> i.autoscaling_protected = True

Project links
-------------

* Sources: https://github.com/Heiko-san/ec2helper
* Documentation: https://github.com/Heiko-san/ec2helper
