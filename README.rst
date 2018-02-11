.. _boto3: https://boto3.readthedocs.io/en/latest/
.. _ec2-metadata: https://github.com/adamchainz/ec2-metadata

ec2helper - A python lib for common EC2 tasks
=============================================

ec2helper basically is a wrapper around boto3_ and ec2-metadata_.
Its intention is to simplify common tasks you want to do in the context of
*"this EC2 instance we're on"*, like retrieving or modifying this instance's
tags.

Project links
-------------

* Sources: https://github.com/Heiko-san/ec2helper
* Documentation: http://ec2helper.readthedocs.io/en/latest/

Required AWS API permissions
----------------------------

For all actions.

.. code-block:: json
    
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "autoscaling:DescribeAutoScalingGroups",
                    "autoscaling:DescribeAutoScalingInstances",
                    "autoscaling:SetInstanceHealth",
                    "autoscaling:SetInstanceProtection",
                    "ec2:DescribeInstances",
                    "ec2:DeleteTags",
                    "ec2:DescribeTags",
                    "ec2:CreateTags"
                ],
                "Resource": "*"
            }
        ]
    }

Examples
--------

Tag manipulation (see `tags <http://ec2helper.readthedocs
.io/en/latest/instance.html#ec2helper.instance.Instance.tags>`_)


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

Force termination of autoscaling instance (see `autoscaling_force_unhealthy
<http://ec2helper.readthedocs.io/en/latest/instance.html#ec2helper.instance
.Instance.autoscaling_force_unhealthy>`_)

.. code-block:: python
    
    from ec2helper import Instance
    
    i = Instance()
    i.autoscaling_force_unhealthy()

Protect autoscaling instance from scale in (see `autoscaling_protected
<http://ec2helper.readthedocs.io/en/latest/instance.html#ec2helper.instance
.Instance.autoscaling_protected>`_)

.. code-block:: python
    
    from ec2helper import Instance
    
    i = Instance()
    i.autoscaling_protected = True

Lock autoscaling instance for task that should only run on a single instance
(see `lock <http://ec2helper.readthedocs.io/en/latest/instance
.html#ec2helper.instance.Instance.lock>`_)

.. code-block:: python

    import time
    from ec2helper import Instance
    from ec2helper.errors import ResourceLockingError
               
    i = Instance()
    try:
        with i.lock("MyLockTag") as lock:
            print("Start with-block with tag lock: " + lock.name)
            time.sleep(10)
            print("End with-block with tag lock: " + lock.name)
    except ResourceLockingError:
        print("Could not retrieve lock!")

