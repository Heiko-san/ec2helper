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

Tag manipulation

.. code-block:: python
    
    from ec2helper import Instance

    i = Instance()
    print(i.tags)
    # {'Name': 'my-server1', 'OS': 'Ubuntu'}

    i.tags = {'OS': 'Redhat', 'Stage': 'test'}
    print(i.tags)
    # {'Name': 'my-server1', 'OS': 'Redhat', 'Stage': 'test'}

    i.delete_tags('OS', 'Stage')
    print(i.tags)
    # {'Name': 'my-server1'}

Force termination of autoscaling instance

.. code-block:: python
    
    >>> from ec2helper import Instance
    >>> i = Instance()
    >>> i.autoscaling_healthy = False

Protect autoscaling instance from scale in

.. code-block:: python
    
    >>> from ec2helper import Instance
    >>> i = Instance()
    >>> i.autoscaling_protected = True

Project links
-------------

* Sources: https://github.com/Heiko-san/ec2helper
* Documentation: https://github.com/Heiko-san/ec2helper
