from twin4build.saref4syst.system import System
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact, IgnoreIntermediateNodes
import twin4build.base as base
import twin4build.systems as systems
import twin4build.utils.input_output_types as tps
from twin4build.utils.rgetattr import rgetattr
from twin4build.utils.rsetattr import rsetattr
from twin4build.utils.get_object_properties import get_object_properties


def get_signature_pattern():
    node0 = Node(cls=(base.Schedule,), id="<Schedule<SUB>1</SUB>>")
    node1 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace<SUB>2</SUB>>")
    node2 = Node(cls=(base.RulebasedController,), id="<RulebasedController<SUB>4</SUB>>")
    node3 = Node(cls=(base.Peer,), id="<Property\nn<SUB>4</SUB>>")
    node4 = Node(cls=(base.Sensor,), id="<Sensor\nn<SUB>5</SUB>>")
    sp = SignaturePattern(ownedBy="ScheduleSystem", priority=100)
    sp.add_edge(Exact(object=node1, subject=node0, predicate="hasProfile"))
    sp.add_edge(Exact(object=node2, subject=node0, predicate="controls"))
    sp.add_edge(Exact(object=node1, subject=node3, predicate="hasProperty"))
    sp.add_edge(Exact(object=node4, subject=node3, predicate="observes"))

    
    sp.add_input("temperatureSetpoint", node2, "inputSignal")
    sp.add_input("peerBinaryValue", node4, "measuredValue")
    sp.add_modeled_node(node0)
    return sp


class ControllableSetPointSystem(base.Schedule, System):
    sp = [get_signature_pattern()]
    def __init__(self,
                **kwargs):
        super().__init__(**kwargs)
        self.base_components = kwargs["base_components"]
        base_rulebased_controller = [component for component in self.base_components if isinstance(component, base.RulebasedController)][0]
        self.rulebased_controller = systems.HeatingSetpointPeerController(**get_object_properties(base_rulebased_controller))
        
        self.input = {"temperatureSetpoint": tps.Scalar()}
        self.output = {"scheduleValue": tps.Scalar()}

        self._config = {"parameters": []}

        for attr in self.setpoint_controller.config["parameters"]:
            new_attr = f"{attr}__{self.setpoint_controller.id}"
            rsetattr(self, new_attr, rgetattr(self.setpoint_controller, attr))
            self._config["parameters"].append(new_attr)

        for attr in self.rulebased_controller.config["parameters"]:
            new_attr = f"{attr}__{self.rulebased_controller.id}"
            rsetattr(self, new_attr, rgetattr(self.rulebased_controller, attr))
            self._config["parameters"].append(new_attr)

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

        for attr in self.setpoint_controller.config["parameters"]:
            new_attr = f"{attr}__{self.setpoint_controller.id}"
            rsetattr(self.setpoint_controller, attr, rgetattr(self, new_attr))

        for attr in self.rulebased_controller.config["parameters"]:
            new_attr = f"{attr}__{self.rulebased_controller.id}"
            rsetattr(self.rulebased_controller, attr, rgetattr(self, new_attr))

        self.rulebased_controller.input["peerBinaryValue"] = self.input["peerBinaryValue"]

        self.rulebased_controller.output = self.output.copy()
        self.rulebased_controller.initialize(startTime,
                                        endTime,
                                        stepSize)


    def do_step(self, secondTime=None, dateTime=None, stepSize=None):
        
        self.rulebased_controller.input["peerBinaryValue"].set(self.input["peerBinaryValue"])
        self.rulebased_controller.do_step(secondTime=secondTime, dateTime=dateTime, stepSize=stepSize)

        self.output["scheduleValue"].set(next(iter(self.rulebased_controller.output.values())))

        
