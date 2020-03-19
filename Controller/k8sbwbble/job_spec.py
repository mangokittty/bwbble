from kubernetes import client
import six
import pprint
import re  # noqa: F401
from typing import List


class V1AlignJobSpec(object):
    openapi_types = {
        "reads_file": "str",
        "reads_count": "int",
        "bubble_file": "str",
        "snp_file": "str",
        "align_parallelism": "int",
        "bwbble_version": "str",
    }

    attribute_map = {
        "reads_file": "readsFile",
        "reads_count": "readsCount",
        "bubble_file": "bubbleFile",
        "snp_file": "snpFile",
        "align_parallelism": "alignParallelism",
        "bwbble_version": "bwbbleVersion",
    }

    def __init__(
        self,
        reads_file: str = None,
        reads_count: int = 512000,
        align_parallelism: int = 1,
        bwbble_version: int = "latest",
        bubble_file: str = None,
        snp_file: str = None,
    ):
        self.reads_count = reads_count
        self.reads_file = reads_file
        self.bubble_file = bubble_file
        self.snp_file = snp_file
        self.align_parallelism = align_parallelism
        self.bwbble_version = bwbble_version

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict")
                        else item,
                        value.items(),
                    )
                )
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1AlignJobSpec):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other


class V1AlignJobStatus(object):
    openapi_types = {"stage": "str", "waiting_for": "List[str]"}

    attribute_map = {"stage": "stage", "waiting_for": "waitingFor"}

    def __init__(self, stage: str = None, waiting_for: List[str] = None):
        self.stage = stage
        self.waiting_for = waiting_for or []

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict")
                        else item,
                        value.items(),
                    )
                )
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1AlignJobStatus):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other


class V1AlignJob(object):
    openapi_types = {
        "api_version": "str",
        "kind": "str",
        "metadata": "V1ObjectMeta",
        "spec": "V1AlignJobSpec",
        "status": "V1AlignJobStatus",
    }

    attribute_map = {
        "api_version": "apiVersion",
        "kind": "kind",
        "metadata": "metadata",
        "spec": "spec",
        "status": "status",
    }

    def __init__(
        self,
        metadata: client.V1ObjectMeta = None,
        spec: V1AlignJobSpec = None,
        status: V1AlignJobStatus = None,
    ):
        super().__init__()

        self.metadata = metadata or client.V1ObjectMeta()
        self.spec = spec or V1AlignJobSpec()
        self.status = status or V1AlignJobStatus()

    @property
    def api_version(self):
        return "v1"

    @property
    def kind(self):
        return "AlignJob"

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict")
                        else item,
                        value.items(),
                    )
                )
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1AlignJob):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
