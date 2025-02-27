from binascii import b2a_hex
from tabnanny import check
import twin4build.base as base
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_controller.damper import damper
from twin4build.utils.uppath import uppath
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact
from twin4build.base import RulebasedController


def get_signature_pattern():
    node0 = Node(cls=(base.RulebasedController,),id="<Controller\nn<SUB>1</SUB>>")

    node1 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>2</SUB>>")
    node6 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>7</SUB>>")
    node3 = Node(cls=(base.OpeningPosition), id="<OpeningDamper\nn<SUB>7</SUB>>")
    node4 = Node(cls=(base.OpeningPosition), id="<OpeningDamper\nn<SUB>7</SUB>>")

    # node4 = Node(cls=(base.Sensor,), id="<SupplyDamperPositionSensor\nn<SUB>5</SUB>>")
    # node8 = Node(cls=(base.OpeningPosition,), id="<SupplyDamperPositionProperty\nn<SUB>9</SUB>>")

    node2 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>3</SUB>>")


    node7 = Node(cls=(base.Sensor,), id="<Co2Sensor\nn<SUB>2</SUB>>")
    node5 = Node(cls=(base.Co2), id="<Co2Property\nn<SUB>7</SUB>>")

    sp = SignaturePattern(ownedBy="PeerDamperController", priority=1100)

    sp.add_edge(Exact(object=node0, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node1, subject=node6, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node2, predicate="isContainedIn"))
    sp.add_edge(Exact(object=node2, subject=node6, predicate="hasProperty"))
    sp.add_edge(Exact(object=node0, subject=node3, predicate="controls"))
    sp.add_edge(Exact(object=node0, subject=node4, predicate="controls"))

    sp.add_edge(Exact(object=node0, subject=node5, predicate="observes"))
    sp.add_edge(Exact(object=node7, subject=node5, predicate="observes"))
    sp.add_edge(Exact(object=node2, subject=node5, predicate="hasProperty"))



    sp.add_input("co2Value", node7, "measuredValue")
    sp.add_input("peerBinaryValue", node1, "measuredValue")
    # sp.add_input("supplyDamperPosition", node4, "measuredValue")

    sp.add_modeled_node(node0)
    return sp


class VentilationPeerControllerPPM(RulebasedController):
    sp = [get_signature_pattern()]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define inputs and outputs
        self.input = {
            "peerBinaryValue": tps.Scalar(),
            "co2Value": tps.Scalar(),
            #"supplyDamperPosition": tps.Scalar()
        }
        self.low_damper_position = 0.10
        self.low_ppm = 600
        self.mid_damper_position = 0.20
        self.mid_ppm = 700
        self.high_damper_position = 0.30
        self.high_ppm = 800
        self.default = 0
        
        self.stepCounter = 0
        self.output = {"inputSignal": tps.Scalar()}
        self.isReverse = True
        self._config = {"parameters": ["low_damper_position", "low_ppm", 
                                       "mid_damper_position", "mid_ppm", 
                                       "high_damper_position", "high_ppm",
                                       "default"]}

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

        # Retrieve inputs
        peerBinaryValue = self.input["peerBinaryValue"].get()
        co2Value = self.input["co2Value"].get()

        damper_position = 0

        if peerBinaryValue > 0:
            if co2Value > self.high_ppm:
                damper_position = self.high_damper_position
            elif co2Value > self.mid_ppm:
                damper_position = self.mid_damper_position
            elif co2Value > self.low_ppm:
                damper_position = self.low_damper_position
            else:
                damper_position = self.default
        else:
            damper_position = self.default
        
        if damper_position <= self.default:
            self.output["inputSignal"].set(self.default)
        else:
            self.output["inputSignal"].set(damper_position)

