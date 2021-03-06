# -*- coding: utf-8 -*-
"""
.. _boto3: https://boto3.readthedocs.io/en/latest/

The Instance class
==================

Module :mod:`ec2helper.instance` provides the
:class:`~ec2helper.instance.Instance` class which is the main entry point of the
:mod:`ec2helper` module and therefore is exposed via :mod:`ec2helper`.

.. code-block:: python

    from ec2helper import Instance

    i = Instance()
    i.autoscaling_protected = True
"""
from __future__ import unicode_literals, absolute_import
import copy
import six
import boto3
import requests
import psutil
from datetime import datetime, timedelta
from dateutil import tz
from ec2helper.utils import IS_EC2, metadata, tags_to_dict, dict_to_tags
from ec2helper.tag_lock import TagLock
from ec2helper.as_protection import AutoscalingProtection
from ec2helper.errors import TagNotFound


class Instance(object):
    """
    Interact with an EC2 instance. By default the instance the script is
    runnning on. But there is also the possibility to set id and region.

    :param string instance_id: The instance id, on an EC2 instance it
        defaults to its id.
    :param string region: The region to make the API calls to, on an EC2
        instance it defaults to its region.
    """

    def __init__(self, instance_id=metadata("instance_id"),
                 region=metadata("region")):
        """Constructor - see class docu."""
        self.id = instance_id
        self.region = region

    def lock(self, lock_name, group_tag=None, group_value=None, ttl=720,
             check_health=True):
        """
        Context guard that acts as a locking system accross multiple EC2
        instances selected by autoscaling group, tag key or tag key-value
        combination (called the lock group further on). Try to set
        :attr:`lock_name` as a tag at this instance to indicate that it holds
        the lock. If another instance of the lock group already holds a still
        valid lock raise :class:`~ec2helper.errors.ResourceAlreadyLocked`.
        This context guard also includes
        :func:`~ec2helper.instance.Instance.autoscaling_protection`.

        :param string lock_name: The name of the lock to retrieve.

            .. warning::

                This string will be used as a tag key and therefore be read
                and set on EC2 instances in the lock group, overwriting any
                present value. Also if an already present :attr:`lock_name` tag
                is read it is expected to have a parsable ISO timestring value.

        :param string group_tag: A tag key to find EC2 instances in this lock
            group. If this value is :code:`None` (default) we will try to
            find all instances in the same autoscaling group as this instance.
        :param string group_value: A tag value to find EC2 instances in this
            lock group if :attr:`group_tag` is set. If this value is
            :code:`None` (default) then all instances with the :attr:`group_tag`
            tag will be checked for holding the :attr:`lock_name` lock,
            regardless of its value.
        :param int ttl: The timespan the lock should be valid in minutes
            (default 720 = 12h).

            .. note::

                The lock tag will be removed after
                with-block is left but an additional time to live will be set as
                the lock tags value (ISO timestring, UTC) in case anything goes
                wrong, so set this longer then your job will ever take to run,
                but shorter then the absolute neccessary repetition interval.

        :param bool check_health: If :code:`True` and if the instance is
            considered unhealthy or not in service, raise
            :class:`~ec2helper.errors.InstanceUnhealthy` to avoid choosing it
            for task execution.
        :return: The TagLock context guard.
        :rtype: :class:`ec2helper.tag_lock.TagLock`
        :raises ec2helper.errors.ResourceAlreadyLocked: If another EC2 instance
            already holds the requested lock.
        :raises ec2helper.errors.InstanceUnhealthy: If this EC2 instance can't
            retrieve the lock because it is considered unhealthy by autoscaling
            group.

        .. code-block:: python
            :caption: Example: Hold the lock "MyLockTag" for sleeping 10 seconds
                accross all instances of this autoscaling group.

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

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:DescribeAutoScalingGroups
            autoscaling:DescribeAutoScalingInstances
            autoscaling:SetInstanceProtection
            ec2:DescribeInstances
            ec2:DeleteTags
            ec2:CreateTags

        .. seealso::

            Function :func:`ec2helper.utils.tags_to_dict`
                For details about ISO timestring tag values.
        """
        return TagLock(self, lock_name, group_tag, group_value, ttl,
                       check_health)

    ##### tags #####

    @property
    def tags(self):
        """
        Get or update this EC2 instance's tags. The values will be converted
        in either direction as documented for
        :func:`~ec2helper.utils.tags_to_dict`.

        .. code-block:: json
            :caption: Example value

            {
                "Name": "my-server1",
                "OS": "Amazon Linux 2",
                "Stage": "prod",
                "Backup": true,
                "RetentionDays": 30
            }

        .. code-block:: python
            :caption: Example: Getting and updating the tags.

            from ec2helper import Instance

            i = Instance()
            print(i.tags)
            # {'Name': 'my-server1', 'OS': 'Ubuntu'}
            i.tags = {'OS': 'Redhat', 'Stage': 'test'}
            print(i.tags)
            # {'Name': 'my-server1', 'OS': 'Redhat', 'Stage': 'test'}

        .. note::

            Although value is set as a dict you can't update a single value
            by something like:

            .. code-block:: python

                i.tags['OS'] = 'Redhat'

            This is because :attr:`~ec2helper.instance.Instance.tags` is a
            virtual property that calls to boto3_'s :func:`create_tags`
            function to update the tags provided with the dict you "set".
            For the same reason only the provided tags are updated,
            other tags will not be deleted from the EC2 instance by this action.

        .. code-block:: none
            :caption: AWS API permissions

            ec2:DescribeTags
            ec2:CreateTags

        .. seealso::

            Function :func:`~ec2helper.instance.Instance.update_tags`
                Update the instance's tags.
            Function :func:`~ec2helper.instance.Instance.delete_tags`
                Delete tags from the instance.
            Function :func:`ec2helper.utils.tags_to_dict`
                For details about the value conversion.
        """
        client = boto3.client("ec2", region_name=self.region)
        response = client.describe_tags(
            Filters=[{
                "Name": "resource-id",
                "Values": [self.id]
            }]
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        return tags_to_dict(response["Tags"])

    @tags.setter
    def tags(self, value):
        """Setter - see property and update_tags."""
        self.update_tags(**value)

    def update_tags(self, **kwargs):
        """
        Update this instance's tags. Actually this does the same as setting the
        :attr:`~ec2helper.instance.Instance.tags` attribute.

        :param kwargs: Tags to update as key value pairs.

        .. code-block:: none
            :caption: AWS API permissions

            ec2:CreateTags

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.tags`
                Get or update the instance's tags.
            Function :func:`~ec2helper.instance.Instance.delete_tags`
                Delete tags from the instance.
            Function :func:`ec2helper.utils.tags_to_dict`
                For details about the value conversion.
        """
        client = boto3.client("ec2", region_name=self.region)
        response = client.create_tags(
            Resources=[self.id],
            Tags=dict_to_tags(kwargs)
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def delete_tags(self, *args):
        """
        Remove the given or all tags from this EC2 instance.

        :param string args: The keys of the tags to delete. If no tag keys
            are provided then all tags will be removed.

        .. code-block:: none
            :caption: AWS API permissions

            ec2:DeleteTags

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.tags`
                Get or update the instance's tags.
            Function :func:`~ec2helper.instance.Instance.update_tags`
                Update the instance's tags.
        """
        client = boto3.client("ec2", region_name=self.region)
        response = client.delete_tags(
            Resources=[self.id],
            Tags=[{"Key": k} for k in args]
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    ##### autoscaling #####

    @property
    def autoscaling(self):
        """
        Get autoscaling status for this instance, :code:`None` if it is no
        autoscaling instance.

        This attribute is readonly.

        .. code-block:: json
            :caption: Example value

            {
                "AutoScalingGroupName": "my-asg",
                "AvailabilityZone": "eu-central-1b",
                "HealthStatus": "HEALTHY",
                "InstanceId": "i-0d2cb773a18dfa487",
                "LaunchConfigurationName": "my-lc",
                "LifecycleState": "InService",
                "ProtectedFromScaleIn": false
            }

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:DescribeAutoScalingInstances
        """
        client = boto3.client("autoscaling", region_name=self.region)
        response = client.describe_auto_scaling_instances(
            InstanceIds=[self.id]
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        return response["AutoScalingInstances"][0] if response[
            "AutoScalingInstances"] else None

    @property
    def autoscaling_protected(self):
        """
        Bool value that indicates if this instance is protected from scale in.

        This attribute can also be set.

        If this instance is not a member of an autoscaling group this
        attribute ignores input and always returns :code:`True`.

        .. code-block:: python
            :caption: Example

            from ec2helper import Instance

            i = Instance()
            i.autoscaling_protected = True

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:DescribeAutoScalingInstances
            autoscaling:SetInstanceProtection

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.autoscaling`
                To get all autoscaling status informations with one API call.
            Function :func:`~ec2helper.instance.Instance.autoscaling_protection`
                Scale in protection as a context guard.
        """
        data = self.autoscaling
        if data is None: return True
        return data["ProtectedFromScaleIn"]

    @autoscaling_protected.setter
    def autoscaling_protected(self, value):
        """Setter - see property"""
        data = self.autoscaling
        if data is None: return
        client = boto3.client("autoscaling", region_name=self.region)
        response = client.set_instance_protection(
            InstanceIds=[self.id],
            AutoScalingGroupName=data["AutoScalingGroupName"],
            ProtectedFromScaleIn=bool(value)
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def autoscaling_protection(self):
        """
        Protect the instance from scale in inside the with-block. Has no effect
        if this EC2 instance is not a member of an autoscaling group. Resets the
        former state afterward.

        :return: The AutoscalingProtection context guard.
        :rtype: :class:`ec2helper.as_protection.AutoscalingProtection`

        .. code-block:: python

            import time
            from ec2helper import Instance

            i = Instance()
            with i.autoscaling_protection() as asp:
                print(i.autoscaling_protected)
                print('former state: ' + asp.autoscaling['ProtectedFromScaleIn']
                time.sleep(10)
            print(i.autoscaling['ProtectedFromScaleIn'])

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:DescribeAutoScalingInstances
            autoscaling:SetInstanceProtection

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.autoscaling_protected`
                Get or set protection as a property.
        """
        return AutoscalingProtection(self)

    @property
    def autoscaling_healthy(self):
        """
        Bool value that indicates if this instance is considered healthy by its
        autoscaling group.

        This attribute can also be set and will cause the instance to terminate
        if you set it to False.

        If this instance is not a member of an autoscaling group this
        attribute ignores input and always returns :code:`True`.

        .. code-block:: python
            :caption: Example

            from ec2helper import Instance

            i = Instance()
            i.autoscaling_healthy = False

        .. note::

            If this instance is protected from scale in :code:`False` will not
            terminate it, to force termination use
            :func:`~ec2helper.instance.Instance.autoscaling_force_unhealthy` or
            remove protection before setting this attribute.

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:DescribeAutoScalingInstances
            autoscaling:SetInstanceHealth

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.autoscaling`
                To get all autoscaling status informations with one API call.
            Function :func:`~ec2helper.instance.Instance.autoscaling_force_unhealthy`
                To force termination.
        """
        data = self.autoscaling
        if data is None: return True
        return data["HealthStatus"] == "HEALTHY"

    @autoscaling_healthy.setter
    def autoscaling_healthy(self, value):
        """Setter - see property"""
        data = self.autoscaling
        if data is None: return
        client = boto3.client("autoscaling", region_name=self.region)
        response = client.set_instance_health(
            InstanceId=self.id,
            ShouldRespectGracePeriod=False,
            HealthStatus="Healthy" if value else "Unhealthy"
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def autoscaling_force_unhealthy(self):
        """
        Force replacement of this EC2 instance.
        Has no effect if this is not an autoscaling instance.

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:SetInstanceHealth
            autoscaling:SetInstanceProtection

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.autoscaling_healthy`
                This function actually is the same as:

                .. code-block:: python

                    autoscaling_protected = False
                    autoscaling_healthy = False

            Attribute :attr:`~ec2helper.instance.Instance.autoscaling_protected`
                See above.
        """
        self.autoscaling_protected = False
        self.autoscaling_healthy = False

    @property
    def autoscaling_standby(self):
        """
        Bool value that indicates if this instance is in standby mode.

        Setter is not implemented yet.

        If this instance is not a member of an autoscaling group this
        attribute ignores input and always returns :code:`False`.

        .. code-block:: none
            :caption: AWS API permissions

            autoscaling:DescribeAutoScalingInstances

        .. seealso::

            Attribute :attr:`~ec2helper.instance.Instance.autoscaling`
                To get all autoscaling status informations with one API call.
        """
        data = self.autoscaling
        if data is None: return False
        return data["LifecycleState"] == "Standby"

    @autoscaling_standby.setter
    def autoscaling_standby(self, value):
        """
        Seamless standby mode.
        TODO: doesn't work yet, we have to manually adjust capacity.
        botocore.exceptions.ClientError: An error occurred (ValidationError)
            when calling the EnterStandby operation: AutoScalingGroup
            hfi-amazon2-boreus-ami has min-size=2, max-size=2, and
            desired-size=2. To place into standby 1 instances, please update
            the AutoScalingGroup sizes appropriately.
        ShouldDecrementDesiredCapacity=False would help, but not with
        exit_standby
        """
        data = self.autoscaling
        if data is None: return
        raise NotImplementedError()
        client = boto3.client("autoscaling", region_name=self.region)
        # data["LifecycleState"] == "InService"
        if value:
            # response = client.put_scaling_policy(
            #    AutoScalingGroupName=data["AutoScalingGroupName"],
            # )
            response = client.enter_standby(
                InstanceIds=[self.id],
                AutoScalingGroupName=data["AutoScalingGroupName"],
                ShouldDecrementDesiredCapacity=True
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        elif data["LifecycleState"] == "Standby":
            response = client.exit_standby(
                InstanceIds=[self.id],
                AutoScalingGroupName=data["AutoScalingGroupName"]
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    ##### cloudwatch #####

    def put_metric_data(self, metric_name, value, unit='Count',
        namespace='AWS/EC2', dimensions=None, dimension_from_tag=None,
        add_instance_dimension=False):
        """
        boto3_'s :func:`~client.put_metric_data` with some defaults for this EC2
        instance.

        :param string metric_name: The name of the metric to put data to.
        :param float value: The value to upload.
        :param string unit: The unit of the value (default is "Count").
        :param string namespace: The namespace (default is "AWS/EC2").
        :param dimensions: A list of dimensions as required by boto3_'s
            :func:`~client.put_metric_data` or a dict that will be converted to
            such a list (default is 'InstanceId' and this instance's id).
        :type dimensions: list or dict
        :param string dimension_from_tag: Instead of :attr:`dimensions` use
            the given tag key and the value found for that tag as a dimension
            pair.
        :param bool add_instance_dimension: If :attr:`dimension_from_tag` or
            :attr:`dimensions` is used, :code:`True` will add 'InstanceId' and
            this instance's id to the list of dimensions.
        :raises ec2helper.errors.TagNotFound: If :attr:`dimension_from_tag` is
            used and the tag can't be found on this EC2 instance.

        .. code-block:: python
            :caption: Example

            from ec2helper import Instance

            i = Instance()
            # Count unit for instance id
            i.put_metric_data('JobsDone', 138)
            # Metric with another unit by tags (here: BootTime by OS)
            i.put_metric_data('BootTime', 35.7, 'Seconds',
                dimension_from_tag='OS')
            # The JobsDone Metric for this instance id and by availability zone
            i.put_metric_data('JobsDone', 138,
                dimensions={'AvailabilityZone':'eu-central-1b'},
                add_instance_dimension=True)

        .. code-block:: none
            :caption: AWS API permissions

            cloudwatch:PutMetricData
            ec2:DescribeTags

        .. seealso::

            Function :func:`~ec2helper.instance.Instance.put_metric_data_ec2_group`
                Both, by instance id and tag at the same time.
        """
        if dimension_from_tag:
            tags = self.tags
            if dimension_from_tag in tags:
                dimensions = [{
                    'Name': dimension_from_tag,
                    'Value': tags[dimension_from_tag]
                }]
            else:
                raise TagNotFound(dimension_from_tag)
        elif dimensions is None:
            dimensions = [{
                'Name': 'InstanceId',
                'Value': self.id
            }]
        elif isinstance(dimensions, dict):
            dimensions = [{"Name": k, "Value": v} for k, v in six.iteritems(
                         dimensions)]
        if add_instance_dimension:
            dimensions.append({
                'Name': 'InstanceId',
                'Value': self.id
            })
        client = boto3.client("cloudwatch", region_name=self.region)
        response = client.put_metric_data(
            Namespace=namespace,
            MetricData=[{
                'MetricName': metric_name,
                'Dimensions': dimensions,
                'Value': value,
                'Unit': unit
            }]
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def put_metric_data_ec2_group(self, group_tag, metric_name, value,
        unit='Count'):
        """
        Like :func:`~ec2helper.instance.Instance.put_metric_data` but puts the
        provided data to two separate dimensions, "InstanceId" and the provided
        :attr:`group_tag`. The namespace will be "AWS/EC2", the dimension
        values will be this instances id and the value of the provided tag.

        :param string group_tag: The tag to use for grouping the metric data
            accross several instances.
        :param string metric_name: The name of the metric to put data to.
        :param float value: The value to upload.
        :param string unit: The unit of the value (default is "Count").
        :raises ec2helper.errors.TagNotFound: If :attr:`group_tag` can't be
            found as a tag on this EC2 instance. At the time the exception is
            raised the metric data was already saved for "InstanceId" dimension.

        .. code-block:: python
            :caption: Example: Put data by instance id and autoscaling group

            from ec2helper import Instance

            i = Instance()
            i.put_metric_data_ec2_group("aws:autoscaling:groupName",
                "MemoryUtilization", 35.6, "Percent")

        .. code-block:: none
            :caption: AWS API permissions

            cloudwatch:PutMetricData
            ec2:DescribeTags

        .. seealso::

            Function :func:`~ec2helper.instance.Instance.put_metric_data`
                For a single, configurable put_metric_data request.
        """
        self.put_metric_data(metric_name, value, unit)
        self.put_metric_data(metric_name, value, unit,
            dimension_from_tag=group_tag)

    ##### ebs #####

    @property
    def volumes(self):
        """
        Get this EC2 instance's volumes.

        This attribute is readonly.

        .. code-block:: json
            :caption: Example value

            {
                "vol-0e3272af46c7d5d1e": {
                    "Attachment": {
                        "AttachTime": "2018-02-07T16:07:54+00:00",
                        "DeleteOnTermination": true,
                        "Device": "/dev/xvda",
                        "InstanceId": "i-0d2cb773a18dfa487",
                        "Root": true,
                        "State": "attached",
                        "VolumeId": "vol-0e3272af46c7d5d1e"
                    },
                    "AvailabilityZone": "eu-central-1b",
                    "CreateTime": "2018-02-07T16:07:54.615000+00:00",
                    "Encrypted": false,
                    "Iops": 100,
                    "Size": 8,
                    "SnapshotId": "snap-036167fc518855549",
                    "State": "in-use",
                    "VolumeId": "vol-0e3272af46c7d5d1e",
                    "VolumeType": "gp2"
                }
            }

        .. code-block:: none
            :caption: AWS API permissions

            ec2:DescribeVolumes
        """
        client = boto3.client("ec2", region_name=self.region)
        paginator = client.get_paginator('describe_volumes')
        volumes = dict()
        for page in paginator.paginate(
            Filters=[{
                'Name': 'attachment.instance-id',
                'Values': [self.id]
            }]
        ):
            for volume in page["Volumes"]:
                vid = volume["VolumeId"]
                volume["Attachment"] = sorted(volume["Attachments"])[-1]
                volume["Attachment"]["Root"] = True if volume["Attachment"][
                    "Device"] == "/dev/xvda" else False
                del volume["Attachments"]
                if "Tags" in volume:
                    volume["Tags"] = tags_to_dict(volume["Tags"])
                else:
                    volume["Tags"] = {}
                volumes[vid] = volume
        return volumes

    def delete_old_backups(self, delete_tag="DeleteAfter"):
        """
        .. code-block:: none
            :caption: AWS API permissions

            ec2:DeleteSnapshot
            ec2:DescribeSnapshots
        """
        client = boto3.client("ec2", region_name=self.region)
        paginator = client.get_paginator('describe_snapshots')
        snapshots = list()
        now = datetime.now(tz=tz.tzutc())
        for page in paginator.paginate(
            Filters=[
                {
                    'Name': 'tag:InstanceId',
                    'Values': [self.id]
                },
                {
                    'Name': 'tag-key',
                    'Values': [delete_tag]
                }
            ]
        ):
            for snapshot in page["Snapshots"]:
                snapshot["Tags"] = tags_to_dict(snapshot["Tags"])
                if now > snapshot["Tags"][delete_tag]:
                    snapshots.append(snapshot)
        for snapshot in snapshots:
            response = client.delete_snapshot(
                SnapshotId=snapshot["SnapshotId"]
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def create_backup(self, volumes=None, retention=30,
        delete_tag="DeleteAfter", tags=None):
        """
        .. code-block:: none
            :caption: AWS API permissions

            ec2:CreateSnapshot
            ec2:CreateTags
            ec2:DescribeTags
            ec2:DescribeVolumes
        """
        # volumes to backup
        all_volumes = self.volumes
        backup_volumes = dict()
        if volumes is None:
            backup_volumes = all_volumes
        else:
            for volume_id in all_volumes:
                if all_volumes[volume_id]["Attachment"]["Device"] in volumes:
                    backup_volumes[volume_id] = all_volumes[volume_id]
        devices = [backup_volumes[x]["Attachment"]["Device"][-1] for x in
                  backup_volumes]
        # mount points
        mounts = dict()
        for part in psutil.disk_partitions():
            for dev in devices:
                if part.device.rstrip("1234567890")[-1] == dev:
                    if dev not in mounts:
                        mounts[dev[-1]] = list()
                    mounts[dev[-1]].append(part.mountpoint)
                    break
        # tags
        instance_tags = self.tags
        backup_tags = {
            delete_tag: datetime.now(tz=tz.tzutc()).replace(second=0,
                        microsecond=0) + timedelta(days=int(retention)),
            "InstanceName": instance_tags["Name"] if "Name" in instance_tags
                        else "UnknownInstanceName",
            "InstanceId": self.id,
            "SnapshotType": "Backup"
        }
        # create and tag the snapshots
        client = boto3.client("ec2", region_name=self.region)
        for volume_id in backup_volumes:
            description = "Backup {0} attached as {1} on {2} ({3})".format(
                volume_id, backup_volumes[volume_id]["Attachment"]["Device"],
                self.id, backup_tags["InstanceName"])
            response = client.create_snapshot(
                Description=description,
                VolumeId=volume_id
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            backup_tags["Device"] = backup_volumes[volume_id]["Attachment"][
                                    "Device"]
            backup_tags["MountPoints"] = ",".join(mounts[backup_tags[
                                         "Device"][-1]])
            # volume tags > defaults
            backup_tags.update(backup_volumes[volume_id]["Tags"])
            # given tags > volume tags
            if tags is not None:
                backup_tags.update(tags)
            backup_tags["Name"] = "{0} ({1})".format(backup_tags["Name"
                ] if "Name" in backup_tags else backup_tags["InstanceName"],
                backup_tags["MountPoints"] if backup_tags["MountPoints"] else
                backup_tags["Device"])
            response = client.create_tags(
                Resources=[response["SnapshotId"]],
                Tags=dict_to_tags(backup_tags)
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
