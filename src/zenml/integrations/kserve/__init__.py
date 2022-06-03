#  Copyright (c) ZenML GmbH 2022. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""
The KServe integration allows you to use the KServe model serving
platform to implement continuous model deployment.
"""
from typing import List

from zenml.enums import StackComponentType
from zenml.integrations.constants import KSERVE
from zenml.integrations.integration import Integration
from zenml.zen_stores.models import FlavorWrapper

KSERVE_MODEL_DEPLOYER_FLAVOR = "kserve"


class KServeIntegration(Integration):
    """Definition of KServe integration for ZenML."""

    NAME = KSERVE
    REQUIREMENTS = [
        "kserve>=0.8.0",
        "kubernetes==18.20.0",
    ]

    @classmethod
    def activate(cls) -> None:
        """Activate the Seldon Core integration."""
        from zenml.integrations.kserve import model_deployers  # noqa
        from zenml.integrations.kserve import services  # noqa
        from zenml.integrations.kserve import steps  # noqa
        from zenml.integrations.kserve import secret_schemas # noqa

    @classmethod
    def flavors(cls) -> List[FlavorWrapper]:
        """Declare the stack component flavors for KServe."""
        return [
            FlavorWrapper(
                name=KSERVE_MODEL_DEPLOYER_FLAVOR,
                source="zenml.integrations.kserve.model_deployers.KServeModelDeployer",
                type=StackComponentType.MODEL_DEPLOYER,
                integration=cls.NAME,
            )
        ]


KServeIntegration.check_installation()
