# -*- coding: utf-8 -*-
"""
"""
from __future__ import unicode_literals, absolute_import
import boto3
from ec2_metadata import ec2_metadata
from ec2helper.utils import tags_to_dict, dict_to_tags

class Instance(object):
    """
    """

    def __init__(self, instance_id=ec2_metadata.instance_id,
        region=ec2_metadata.region):
        """
        Constructor
        """
        self.id = instance_id
        self.region = region

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
        return data["ProtectedFromScaleIn"] if data is not None else True

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
        Test if this instance is protected against scale in events.
        """
        data = self.autoscaling
        return data["HealthStatus"] == "HEALTHY"

    @autoscaling_health.setter
    def autoscaling_healthy(self, value):
        """
        Set protection against scale in events.
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

    @property
    def autoscaling_standby(self):
        """
        Test if this instance is in standby mode.
        """
        data = self.autoscaling
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
