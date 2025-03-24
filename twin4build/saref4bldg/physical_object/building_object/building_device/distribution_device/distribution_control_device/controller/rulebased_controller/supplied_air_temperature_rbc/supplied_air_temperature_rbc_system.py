from tabnanny import check
import twin4build.base as base
from twin4build.utils.uppath import uppath
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact
from twin4build.base import RulebasedController


def get_signature_pattern():
    node00 = Node(cls=(base.System), id="<HeatingSystem\nn<SUB>1</SUB>>")
    node0 = Node(cls=(base.RulebasedController), id="<Controller\nn<SUB>1</SUB>>")
    node1 = Node(cls=(base.Sensor,), id="<Sensor\nn<SUB>2</SUB>>")
    node2 = Node(cls=(base.Property,), id="<Property\nn<SUB>3</SUB>>")
    node3 = Node(cls=(base.Schedule,), id="<Schedule\nn<SUB>4</SUB>>")
    sp = SignaturePattern(ownedBy="SAT_rbc_controller",priority=1000)
    sp.add_edge(Exact(object=node0, subject=node00, predicate="subSystemOf"))
    sp.add_edge(Exact(object=node0, subject=node2, predicate="observes"))
    sp.add_edge(Exact(object=node1, subject=node2, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node3, predicate="hasProfile"))
    sp.add_input("actualValue", node1, "measuredValue")
    sp.add_modeled_node(node0)
    return sp


    sp.add_modeled_node(node0)
    return sp


class SuppliedAirTemperatureRBC(RulebasedController):
    sp = [get_signature_pattern()]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define inputs and outputs
        self.input = {
            "actualValue": tps.Scalar(),
        }
        self.onValue = 24
        self.offValue = 21
        self.stepCounter = 0
        self.output = {"inputSignal": tps.Scalar()}
        self.isReverse = False
        self._config = {"parameters": ["onValue", "offValue"]}

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
        current_hour = dateTime.hour
        if 6 <= current_hour < 19:
            self.output["inputSignal"].set(self.onValue)
        else:
            self.output["inputSignal"].set(self.offValue)