# -*- coding: utf-8 -*-
"""
"""
from __future__ import unicode_literals, absolute_import
import boto3
from ec2helper.utils import IS_EC2, metadata, tags_to_dict, dict_to_tags
from ec2helper.tag_lock import TagLock


class Instance(object):
    """
    """

    def __init__(self, instance_id=metadata("instance_id"),
        region=metadata("region")):
        """
        Constructor
        """
        self.id = instance_id
        self.region = region

    def lock(self, lock_name, group_tag=None, group_value=None, ttl=720,
        check_health=True):
        """
        :raises ValueError: if foo is the same as bar
        """
        return TagLock(self, lock_name, group_tag, group_value, ttl,
            check_health)

##### tags ####################################################################

    @property
    def tags(self):
        """
        Get this instance's tags from API (as dict).
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
        """
        Same as update_tags.
        """
        self.update_tags(**value)

    def update_tags(self, **kwargs):
        """
        Update this instance's tags via API (from dict).
        """
        client = boto3.client("ec2", region_name=self.region)
        response = client.create_tags(
            Resources=[self.id],
            Tags=dict_to_tags(kwargs)
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def delete_tags(self, *args):
        """
        Remove the given or all tags.
        """
        client = boto3.client("ec2", region_name=self.region)
        response = client.delete_tags(
            Resources=[self.id],
            Tags=[{"Key": k} for k in args]
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

##### autoscaling #############################################################

    @property
    def autoscaling(self):
        """
        Get autoscaling status for this instance, None if it is no autoscaling
        instance.

        {
            "AutoScalingGroupName": "hfi-amazon2-boreus-ami",
            "AvailabilityZone": "eu-central-1b",
            "HealthStatus": "HEALTHY",
            "InstanceId": "i-0d2cb773a18dfa487",
            "LaunchConfigurationName": "hfi-amazon2-boreus-ami",
            "LifecycleState": "InService",
            "ProtectedFromScaleIn": false
        }
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
        Test if this instance is protected against scale in events.
        """
        data = self.autoscaling
        if data is None: return True
        return data["ProtectedFromScaleIn"]

    @autoscaling_protected.setter
    def autoscaling_protected(self, value):
        """
        Set protection against scale in events.
        """
        data = self.autoscaling
        if data is None: return
        client = boto3.client("autoscaling", region_name=self.region)
        response = client.set_instance_protection(
            InstanceIds=[self.id],
            AutoScalingGroupName=data["AutoScalingGroupName"],
            ProtectedFromScaleIn=bool(value)
        )
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    @property
    def autoscaling_healthy(self):
        """
        Test if this instance is considered healthy by the autoscaling group.
        """
        data = self.autoscaling
        if data is None: return True
        return data["HealthStatus"] == "HEALTHY"

    @autoscaling_healthy.setter
    def autoscaling_healthy(self, value):
        """
        Set health status.
        False will cause the autoscaling group to replace this instance (unless
        it is protected, use autoscaling_force_unhealthy() to also unprotect).
        """
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
        Force replacement of this instance.

        Same as:
        this_instance.autoscaling_protected = False
        this_instance.autoscaling_healthy = False
        """
        self.autoscaling_protected = False
        self.autoscaling_healthy = False

    @property
    def autoscaling_standby(self):
        """
        Test if this instance is in standby mode.
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
        client = boto3.client("autoscaling", region_name=self.region)
        #data["LifecycleState"] == "InService"
        if value:
            #response = client.put_scaling_policy(
            #    AutoScalingGroupName=data["AutoScalingGroupName"],
            #)
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
