import sys
import os
import twin4build.saref4bldg.building_space.building_space as building_space
from twin4build.utils.constants import Constants
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact, IgnoreIntermediateNodes, Optional
import twin4build.base as base

def get_signature_pattern():
    """
    Get the signature pattern of the FMU component.

    Returns:
        SignaturePattern: The signature pattern of the FMU component.
    """
    node0 = Node(cls=base.BuildingSpace, id="<BuildingSpace\nn<SUB>1</SUB>>")
    node1= Node(cls=base.Temperature, id="<Temperature\nn<SUB>2</SUB>>")
    node2 = Node(cls=base.Sensor, id="<Sensor\nn<SUB>3</SUB>>") 

    sp = SignaturePattern(ownedBy="TBoundarySpace", priority=1)

    sp.add_edge(Exact(object=node0, subject=node1, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2, subject=node0, predicate="isContainedIn"))
    sp.add_edge(Exact(object=node2, subject=node1, predicate="observes"))

    sp.add_input("measuredValue", node2)

    sp.add_modeled_node(node0)

    return sp

def test_signature_pattern():
    """
    Get the signature pattern of the FMU component.

    Returns:
        SignaturePattern: The signature pattern of the FMU component.
    """
    node0 = Node(cls=base.BuildingSpace, id="<BuildingSpace\nn<SUB>1</SUB>>")
    node1= Node(cls=base.Temperature, id="<Temperature\nn<SUB>2</SUB>>")
    node2 = Node(cls=base.Sensor, id="<Sensor\nn<SUB>3</SUB>>") 

    sp = SignaturePattern(ownedBy="TBoundarySpace", priority=2)

    sp.add_edge(Exact(object=node0, subject=node1, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2, subject=node1, predicate="observes"))

    sp.add_input("measuredValue", node2)

    sp.add_modeled_node(node0)

    return sp


class TBoundarybuildingSpace(building_space.BuildingSpace):
    sp = [get_signature_pattern(),
          test_signature_pattern()]
    def __init__(self,
                 measuredValue = 22,
                **kwargs):
        super().__init__(**kwargs)

        self.input = {'measuredValue': tps.Scalar()}
        self.output = {"indoorTemperature": tps.Scalar()}

        self.measuredValue = measuredValue

        self._config = {"parameters": []}

    @property
    def config(self):
        return self._config


    def cache(self,
            startTime=None,
            endTime=None,
            stepSize=None):
        pass

    def initialize(self,
                    startTime=None,
                    endTime=None,
                    stepSize=None,
                    model=None):
        pass

    def do_step(self, secondTime=None, dateTime=None, stepSize=None):
        self.output["indoorTemperature"].set(self.input["measuredValue"].get())