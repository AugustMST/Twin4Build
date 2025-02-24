from tabnanny import check
import twin4build.base as base
from twin4build.utils.uppath import uppath
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact, IgnoreIntermediateNodes
from twin4build.base import RulebasedController


def get_signature_pattern():
    node0 = Node(cls=(base.RulebasedController,), id="<Controller\nn<SUB>1</SUB>>")

    node1 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>2</SUB>>")
    node2 = Node(cls=(base.Sensor,), id="<ValvePositionSensor\nn<SUB>3</SUB>>")
    node3 = Node(cls=(base.Sensor,), id="<SuppliedAirTemperatureSensor\nn<SUB>4</SUB>>")
    node4 = Node(cls=(base.Sensor,), id="<SupplyDamperPositionSensor\nn<SUB>5</SUB>>")
    node12 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>14</SUB>>")

    node5 = Node(cls=(base.Temperature,), id="<TemperatureProperty\nn<SUB>6</SUB>>")
    node6 = Node(cls=(base.OpeningPosition,), id="<ValvePositionProperty\nn<SUB>7</SUB>>")
    node7 = Node(cls=(base.Temperature,), id="<SuppliedAirTemperatureProperty\nn<SUB>8</SUB>>")
    node8 = Node(cls=(base.OpeningPosition,), id="<SupplyDamperPositionProperty\nn<SUB>9</SUB>>")
    node10 = Node(cls=(base.Peer,), id="<PeerProperty\nn<SUB>9</SUB>>")

    node13 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>11</SUB>>")
    node11 = Node(cls=(base.SpaceHeater,), id="<SpaceHeater\nn<SUB>12</SUB>>")
    node12 = Node(cls=(base.Damper,), id="<Damper\nn<SUB>13</SUB>>")

    sp = SignaturePattern(ownedBy="DamperHeatingController", priority=200)

    # sp.add_edge(Exact(object=node5, subject=node0, predicate="isObservedBy"))
    # sp.add_edge(Exact(object=node6, subject=node0, predicate="isObservedBy"))
    # sp.add_edge(Exact(object=node7, subject=node0, predicate="isObservedBy"))
    # sp.add_edge(Exact(object=node8, subject=node0, predicate="isObservedBy"))

    sp.add_edge(Exact(object=node0, subject=node5, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node7, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node10, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node10, predicate="observes"))

    sp.add_edge(Exact(object=node1, subject=node5, predicate="observes"))
    sp.add_edge(Exact(object=node2, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node3, subject=node7, predicate="observes"))
    sp.add_edge(Exact(object=node4, subject=node8, predicate="observes"))
    sp.add_edge(Exact(object=node12, subject=node10, predicate="observes"))

    sp.add_edge(Exact(object=node12, subject=node8, predicate="hasProperty"))
    sp.add_edge(Exact(object=node11, subject=node6, predicate="hasProperty"))

    sp.add_edge(Exact(object=node13, subject=node11, predicate="contains"))
    sp.add_edge(Exact(object=node13, subject=node12, predicate="contains"))

    sp.add_edge(Exact(object=node0, subject=node8, predicate="controls"))

    sp.add_input("peerBinaryValue", node12, "measuredValue")
    sp.add_input("actualTemperature", node1, "measuredValue")
    sp.add_input("valvePosition", node2, "measuredValue")
    sp.add_input("suppliedAirTemperature", node3, "measuredValue")
    sp.add_input("supplyDamperPosition", node4, "measuredValue")

    sp.add_modeled_node(node0)
    return sp


class RulebasedHeatingDamperController(RulebasedController):
    sp = [get_signature_pattern()]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define inputs and outputs
        self.input = {
            "peerBinaryValue": tps.Scalar(),
            "actualTemperature": tps.Scalar(),
            "valvePosition": tps.Scalar(),
            "suppliedAirTemperature": tps.Scalar(),
            "supplyDamperPosition": tps.Scalar()
        }
        self.max_position_for_heating = 1
        self.onValue = 0.3
        self.offValue = 0
        self.output = {"inputSignal": tps.Scalar()}
        self.isReverse = True
        self._config = {"parameters": ["max_position_for_heating", "onValue", "offValue"]}

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
        '''
            This function initializes the FMU component by setting the start_time and fmu_filename attributes, 
            and then sets the parameters for the FMU model.
        '''
        (modeled_match_nodes, (component_cls, sp, groups)) = model.instance_to_group_map[self]

        space_node = sp.get_node_by_id("<BuildingSpace\nn<SUB>11</SUB>>")
        modeled_space = groups[0][space_node]
        modeled_space = model.instance_map_reversed[modeled_space]
        self.occupantComfort = modeled_space.occupantComfort
 
    def do_step(self, secondTime=None, dateTime=None, stepSize=None):
        """Apply control logic at each step."""
        # Retrieve inputs
        actual_temp = self.input["actualTemperature"].get()
        valve_position = self.input["valvePosition"].get()
        supplied_air_temp = self.input["suppliedAirTemperature"].get()
        supply_damper_position = self.input["supplyDamperPosition"].get()
        peerProperty = self.input["peerBinaryValue"].get()

        if peerProperty > 0:
            if (
                actual_temp < self.occupantComfort
                and valve_position > 0.80
                and supplied_air_temp > actual_temp
            ):
                self.output["inputSignal"].set(self.max_position_for_heating)
            else:
                self.output["inputSignal"].set(self.onValue)
        else:
                self.output["inputSignal"].set(self.offValue)
