from tabnanny import check
import twin4build.base as base
from twin4build.utils.uppath import uppath
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact
from twin4build.base import RulebasedController


def get_signature_pattern():
    node0 = Node(cls=(base.RulebasedController,), id="<Controller\nn<SUB>1</SUB>>")

    node1 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>2</SUB>>")
    node2 = Node(cls=(base.Sensor,), id="<ValvePositionSensor\nn<SUB>3</SUB>>")
    node3 = Node(cls=(base.Sensor,), id="<SuppliedAirTemperatureSensor\nn<SUB>4</SUB>>")
    node4 = Node(cls=(base.Sensor,), id="<SupplyDamperPositionSensor\nn<SUB>5</SUB>>")

    node5 = Node(cls=(base.Temperature,), id="<TemperatureProperty\nn<SUB>6</SUB>>")
    node6 = Node(cls=(base.OpeningPosition,), id="<ValvePositionProperty\nn<SUB>7</SUB>>")
    node7 = Node(cls=(base.Temperature,), id="<SuppliedAirTemperatureProperty\nn<SUB>8</SUB>>")
    node8 = Node(cls=(base.OpeningPosition,), id="<SupplyDamperPositionProperty\nn<SUB>9</SUB>>")

    node9 = Node(cls=(base.Schedule,), id="<Schedule\nn<SUB>10</SUB>>")

    sp = SignaturePattern(ownedBy="DamperHeatingController", priority=200)

    # sp.add_edge(Exact(object=node5, subject=node0, predicate="isObservedBy"))
    # sp.add_edge(Exact(object=node6, subject=node0, predicate="isObservedBy"))
    # sp.add_edge(Exact(object=node7, subject=node0, predicate="isObservedBy"))
    # sp.add_edge(Exact(object=node8, subject=node0, predicate="isObservedBy"))

    sp.add_edge(Exact(object=node0, subject=node5, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node7, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node8, predicate="observes"))

    sp.add_edge(Exact(object=node1, subject=node5, predicate="observes"))
    sp.add_edge(Exact(object=node2, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node3, subject=node7, predicate="observes"))
    sp.add_edge(Exact(object=node4, subject=node8, predicate="observes"))

    sp.add_edge(Exact(object=node0, subject=node9, predicate="hasProfile"))

    sp.add_input("actualTemperature", node1, "measuredValue")
    sp.add_input("setpointTemperature", node9, "scheduleValue")
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
            "actualTemperature": tps.Scalar(),
            "setpointTemperature": tps.Scalar(),
            "valvePosition": tps.Scalar(),
            "suppliedAirTemperature": tps.Scalar(),
            "supplyDamperPosition": tps.Scalar()
        }
        self.max_position_for_heating = 0.80
        self.output = {"inputSignal": tps.Scalar()}
        self.isReverse = True
        self._config = {"parameters": ["max_position_for_heating"]}

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
        pass

    def do_step(self, secondTime=None, dateTime=None, stepSize=None):
        """Apply control logic at each step."""
        # Retrieve inputs
        actual_temp = self.input["actualTemperature"].get()
        setpoint_temp = self.input["setpointTemperature"].get()
        valve_position = self.input["valvePosition"].get()
        supplied_air_temp = self.input["suppliedAirTemperature"].get()
        supply_damper_position = self.input["supplyDamperPosition"].get()

        if (
            actual_temp < setpoint_temp
            and valve_position > 0.80
            and supplied_air_temp > actual_temp
        ):
            self.output["inputSignal"].set(self.max_position_for_heating)
        else:
            self.output["inputSignal"].set(supply_damper_position)