from tabnanny import check
import twin4build.base as base
from twin4build.utils.uppath import uppath
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact
from twin4build.base import RulebasedController


def get_signature_pattern():
    node0 = Node(cls=(base.RulebasedController,),id="<Controller\nn<SUB>1</SUB>>")

    node1 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>2</SUB>>")
    node6 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>7</SUB>>")

    node2 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>3</SUB>>")

    sp = SignaturePattern(ownedBy="PeerDamperController", priority=1000)

    sp.add_edge(Exact(object=node0, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node1, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node2, predicate="isContainedIn"))
    sp.add_edge(Exact(object=node2, subject=node6, predicate="hasProperty"))

    sp.add_input("peerBinaryValue", node1, "measuredValue")

    sp.add_modeled_node(node0)
    return sp


class VentilationPeerController(RulebasedController):
    sp = [get_signature_pattern()]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define inputs and outputs
        self.input = {
            "peerBinaryValue": tps.Scalar()
        }
        self.onValue = 0.30
        self.output = {"inputSignal": tps.Scalar()}
        self.isReverse = True
        self._config = {"parameters": ["onValue"]}

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
        peerBinaryValue = self.input["peerBinaryValue"].get()

        if (
            peerBinaryValue > 0
        ):
            self.output["inputSignal"].set(self.onValue)
        else:
            self.output["inputSignal"].set(0)