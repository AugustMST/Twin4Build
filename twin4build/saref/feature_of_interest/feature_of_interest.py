from __future__ import annotations
from typing import Union
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import twin4build.saref.measurement.measurement as measurement
    import twin4build.saref.property_.property_ as property_
    import twin4build.saref.property_value.property_value as property_value

import os 
import sys
import twin4build.saref.profile.profile as profile

uppath = lambda _path,n: os.sep.join(_path.split(os.sep)[:-n])
file_path = uppath(os.path.abspath(__file__), 4)
sys.path.append(file_path)

class FeatureOfInterest:
    def __init__(self,
                hasMeasurement: Union[None, measurement.Measurement]=None,
                hasProperty: Union[None, list]=None,
                hasPropertyValue: Union[None, list]=None,
                hasProfile: Union[None, profile.Profile]=None,
                **kwargs):
        super().__init__(**kwargs)
        import twin4build.saref.measurement.measurement as measurement
        import twin4build.saref.property_.property_ as property_
        assert isinstance(hasMeasurement, measurement.Measurement) or hasMeasurement is None, "Attribute \"hasMeasurement\" is of type \"" + str(type(hasMeasurement)) + "\" but must be of type \"" + str(measurement.Measurement) + "\""
        assert isinstance(hasProperty, list) or hasProperty is None, "Attribute \"hasProperty\" is of type \"" + str(type(hasProperty)) + "\" but must be of type \"" + str(list) + "\""
        assert isinstance(hasPropertyValue, list) or hasPropertyValue is None, "Attribute \"hasPropertyValue\" is of type \"" + str(type(hasPropertyValue)) + "\" but must be of type \"" + str(list) + "\""
        assert isinstance(hasProfile, profile.Profile) or hasProfile is None, "Attribute \"hasProfile\" is of type \"" + str(type(hasProfile)) + "\" but must be of type \"" + str(profile.Profile) + "\""

        if hasProperty is None:
            hasProperty = []
        if hasPropertyValue is None:
            hasPropertyValue = []
        self.hasMeasurement = hasMeasurement
        self.hasProperty = hasProperty
        self.hasPropertyValue = hasPropertyValue
        self.hasProfile = hasProfile

    # @property
    # def hasProperty(self):
    #     return self._hasProperty

    # @property
    # def hasPropertyValue(self):
    #     return self._hasPropertyValue
