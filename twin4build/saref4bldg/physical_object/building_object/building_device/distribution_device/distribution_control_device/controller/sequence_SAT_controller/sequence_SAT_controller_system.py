import twin4build.base as base
from twin4build.utils.fmu.fmu_component import FMUComponent, unzip_fmu
from twin4build.utils.uppath import uppath
import twin4build.systems as systems
import numpy as np
import os
from twin4build.utils.unit_converters.functions import do_nothing
import twin4build.base as base
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact, MultipleMatches
from twin4build.utils.get_object_properties import get_object_properties
from twin4build.utils.rsetattr import rsetattr
from twin4build.utils.rgetattr import rgetattr
import twin4build.utils.input_output_types as tps

def get_signature_pattern():
    # three setpoint_controllers, one for each property:
    node0_0 = Node(cls=(base.SetpointController,), id="<SetpointController\nn<SUB>0_0</SUB>>")
    node0_1 = Node(cls=(base.SetpointController,), id="<SetpointController\nn<SUB>0_1</SUB>>")
    node0_2 = Node(cls=(base.SetpointController,), id="<SetpointController\nn<SUB>0_2</SUB>>")

    # setpoint_controller_temperatures:
    node2_1 = Node(cls=(base.Temperature,), id="<Temperature\nn<SUB>2_1</SUB>>")

    # temperature Sensors
    node2_4 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>2_4</SUB>>")
    
    # rulebased controller
    node0 = Node(cls=(base.RulebasedController,), id="<RulebasedController\nn<SUB>1</SUB>>")

    # control properties: 
    node2 = Node(cls=(base.Property,), id="<OpeningPositionCoolingCoil\nn<SUB>3</SUB>>")

    # PIR properties
    node1_1 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>1</SUB>>")
    node1_2 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>2</SUB>>")
    node1_3 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>3</SUB>>")
    node1_4 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>4</SUB>>")
    node1_5 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>6</SUB>>")
    node1_6 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>7</SUB>>")
    node1_7 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>8</SUB>>")
    node1_8 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>9</SUB>>")
    node1_9 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>10</SUB>>")
    node1_10 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>11</SUB>>")
    node1_11 = Node(cls=(base.Peer), id="<PeerProperty\nn<SUB>12</SUB>>")

    # PIR sensors
    node3_1 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>24</SUB>>")
    node3_2 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>25</SUB>>")
    node3_3 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>26</SUB>>")
    node3_4 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>27</SUB>>")
    node3_5 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>28</SUB>>")
    node3_6 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>29</SUB>>")
    node3_7 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>30</SUB>>")
    node3_8 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>31</SUB>>")
    node3_9 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>32</SUB>>")
    node3_10 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>33</SUB>>")
    node3_11 = Node(cls=(base.Sensor,), id="<PeerSensor\nn<SUB>34</SUB>>")

    # Temperature properties
    node4_1 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>38</SUB>>")
    node4_2 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>39</SUB>>")
    node4_3 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>40</SUB>>")
    node4_4 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>41</SUB>>")
    node4_5 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>42</SUB>>")
    node4_6 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>43</SUB>>")
    node4_7 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>44</SUB>>")
    node4_8 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>45</SUB>>")
    node4_9 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>46</SUB>>")
    node4_10 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>47</SUB>>")
    node4_11 = Node(cls=(base.Temperature), id="<TemperatureProperty\nn<SUB>48</SUB>>")

    # Temperature sensors
    node5_1 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>49</SUB>>")
    node5_2 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>50</SUB>>")
    node5_3 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>51</SUB>>")
    node5_4 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>52</SUB>>")
    node5_5 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>53</SUB>>")
    node5_6 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>54</SUB>>")
    node5_7 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>55</SUB>>")
    node5_8 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>56</SUB>>")
    node5_9 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>57</SUB>>")
    node5_10 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>58</SUB>>")
    node5_11 = Node(cls=(base.Sensor,), id="<TemperatureSensor\nn<SUB>59</SUB>>")

    sp = SignaturePattern(ownedBy="SequenceControllerSystem", priority=30000)
    sp.add_edge(Exact(object=node0_0, subject=node2_1, predicate="observes"))
    sp.add_edge(Exact(object=node2_4, subject=node2_1, predicate="observes"))


    sp.add_edge(Exact(object=node0_0, subject=node2, predicate="controls"))
    sp.add_edge(Exact(object=node0, subject=node2, predicate="controls"))
    # Controller observes Peer

    sp.add_edge(Exact(object=node0, subject=node1_1, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_2, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_3, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_4, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_5, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_6, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_7, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_8, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_9, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_10, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node1_11, predicate="observes"))

    # Controller observes Temperature

    sp.add_edge(Exact(object=node0, subject=node4_1, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_2, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_3, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_4, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_5, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_6, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_7, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_8, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_9, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_10, predicate="observes"))
    sp.add_edge(Exact(object=node0, subject=node4_11, predicate="observes"))

    # PeerSensor observes Peer

    sp.add_edge(Exact(object=node3_1, subject=node1_1, predicate="observes"))
    sp.add_edge(Exact(object=node3_2, subject=node1_2, predicate="observes"))
    sp.add_edge(Exact(object=node3_3, subject=node1_3, predicate="observes"))
    sp.add_edge(Exact(object=node3_4, subject=node1_4, predicate="observes"))
    sp.add_edge(Exact(object=node3_5, subject=node1_5, predicate="observes"))
    sp.add_edge(Exact(object=node3_6, subject=node1_6, predicate="observes"))
    sp.add_edge(Exact(object=node3_7, subject=node1_7, predicate="observes"))
    sp.add_edge(Exact(object=node3_8, subject=node1_8, predicate="observes"))
    sp.add_edge(Exact(object=node3_9, subject=node1_9, predicate="observes"))
    sp.add_edge(Exact(object=node3_10, subject=node1_10, predicate="observes"))
    sp.add_edge(Exact(object=node3_11, subject=node1_11, predicate="observes"))

    # Temperature sensor

    sp.add_edge(Exact(object=node5_1, subject=node4_1, predicate="observes"))
    sp.add_edge(Exact(object=node5_2, subject=node4_2, predicate="observes"))
    sp.add_edge(Exact(object=node5_3, subject=node4_3, predicate="observes"))
    sp.add_edge(Exact(object=node5_4, subject=node4_4, predicate="observes"))
    sp.add_edge(Exact(object=node5_5, subject=node4_5, predicate="observes"))
    sp.add_edge(Exact(object=node5_6, subject=node4_6, predicate="observes"))
    sp.add_edge(Exact(object=node5_7, subject=node4_7, predicate="observes"))
    sp.add_edge(Exact(object=node5_8, subject=node4_8, predicate="observes"))
    sp.add_edge(Exact(object=node5_9, subject=node4_9, predicate="observes"))
    sp.add_edge(Exact(object=node5_10, subject=node4_10, predicate="observes"))
    sp.add_edge(Exact(object=node5_11, subject=node4_11, predicate="observes"))

    sp.add_input("TemperatureValue", node2_4, "measuredValue")

    sp.add_input("peerBinaryValue_1", node3_1, "measuredValue")
    sp.add_input("peerBinaryValue_2", node3_2, "measuredValue")
    sp.add_input("peerBinaryValue_3", node3_3, "measuredValue")
    sp.add_input("peerBinaryValue_4", node3_4, "measuredValue")
    sp.add_input("peerBinaryValue_5", node3_5, "measuredValue")
    sp.add_input("peerBinaryValue_6", node3_6, "measuredValue")
    sp.add_input("peerBinaryValue_7", node3_7, "measuredValue")
    sp.add_input("peerBinaryValue_8", node3_8, "measuredValue")
    sp.add_input("peerBinaryValue_9", node3_9, "measuredValue")
    sp.add_input("peerBinaryValue_10", node3_10, "measuredValue")
    sp.add_input("peerBinaryValue_11", node3_11, "measuredValue")

    sp.add_input("TemperatureValue_1", node5_1, "measuredValue")
    sp.add_input("TemperatureValue_2", node5_2, "measuredValue")
    sp.add_input("TemperatureValue_3", node5_3, "measuredValue")
    sp.add_input("TemperatureValue_4", node5_4, "measuredValue")
    sp.add_input("TemperatureValue_5", node5_5, "measuredValue")
    sp.add_input("TemperatureValue_6", node5_6, "measuredValue")
    sp.add_input("TemperatureValue_7", node5_7, "measuredValue")
    sp.add_input("TemperatureValue_8", node5_8, "measuredValue")
    sp.add_input("TemperatureValue_9", node5_9, "measuredValue")
    sp.add_input("TemperatureValue_10", node5_10, "measuredValue")
    sp.add_input("TemperatureValue_11", node5_11, "measuredValue")

    sp.add_modeled_node(node0)
    sp.add_modeled_node(node0_1)
    sp.add_modeled_node(node0_2)
    sp.add_modeled_node(node0_0)
    return sp


class SequenceSATControllerSystem(base.Controller):
    sp = [get_signature_pattern()]
    def __init__(self,
                **kwargs):
        super().__init__(**kwargs)
        self.base_components = kwargs["base_components"]
        base_setpoint_controller = [component for component in self.base_components if isinstance(component, base.SetpointController)][0]
        base_rulebased_controller = [component for component in self.base_components if isinstance(component, base.RulebasedController)][0]
        self.setpoint_controller_1 = systems.PIControllerFMUSystem(**get_object_properties(base_setpoint_controller))
        self.setpoint_controller_2 = systems.PIControllerFMUSystem(**get_object_properties(base_setpoint_controller))
        self.setpoint_controller_3 = systems.PIControllerFMUSystem(**get_object_properties(base_setpoint_controller))

        self.rulebased_controller = systems.SuppliedAirTemperatureControllerSystem(**get_object_properties(base_rulebased_controller))

        self.input = {
            "peerBinaryValue_1": tps.Scalar(),
            "peerBinaryValue_2": tps.Scalar(),
            "peerBinaryValue_3": tps.Scalar(),
            "peerBinaryValue_4": tps.Scalar(),
            "peerBinaryValue_5": tps.Scalar(),
            "peerBinaryValue_6": tps.Scalar(),
            "peerBinaryValue_7": tps.Scalar(),
            "peerBinaryValue_8": tps.Scalar(),
            "peerBinaryValue_9": tps.Scalar(),
            "peerBinaryValue_10": tps.Scalar(),
            "peerBinaryValue_11": tps.Scalar(),
            "TemperatureValue_1": tps.Scalar(),
            "TemperatureValue_2": tps.Scalar(),
            "TemperatureValue_3": tps.Scalar(),
            "TemperatureValue_4": tps.Scalar(),
            "TemperatureValue_5": tps.Scalar(),
            "TemperatureValue_6": tps.Scalar(),
            "TemperatureValue_7": tps.Scalar(),
            "TemperatureValue_8": tps.Scalar(),
            "TemperatureValue_9": tps.Scalar(),
            "TemperatureValue_10": tps.Scalar(),
            "TemperatureValue_11": tps.Scalar(),
            "TemperatureValue": tps.Scalar()
                        }
        self.output = {"inputSignal": tps.Scalar()}
        self._config = {"parameters": []}

        for attr in self.setpoint_controller_1.config["parameters"]:
            new_attr = f"{attr}__{self.setpoint_controller_1.id}"
            rsetattr(self, new_attr, rgetattr(self.setpoint_controller_1, attr))
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

        for attr in self.setpoint_controller_1.config["parameters"]:
            new_attr = f"{attr}__{self.setpoint_controller_1.id}"
            rsetattr(self.setpoint_controller_1, attr, rgetattr(self, new_attr))

        for attr in self.rulebased_controller.config["parameters"]:
            new_attr = f"{attr}__{self.rulebased_controller.id}"
            rsetattr(self.rulebased_controller, attr, rgetattr(self, new_attr))

        self.setpoint_controller_1.input["TemperatureValue"] = self.input["actualValueSetpointController"]

        self.rulebased_controller.input["peerBinaryValue_1"] = self.input["peerBinaryValue_1"]
        self.rulebased_controller.input["peerBinaryValue_2"] = self.input["peerBinaryValue_2"]
        self.rulebased_controller.input["peerBinaryValue_3"] = self.input["peerBinaryValue_3"]
        self.rulebased_controller.input["peerBinaryValue_4"] = self.input["peerBinaryValue_4"]
        self.rulebased_controller.input["peerBinaryValue_5"] = self.input["peerBinaryValue_5"]
        self.rulebased_controller.input["peerBinaryValue_6"] = self.input["peerBinaryValue_6"]
        self.rulebased_controller.input["peerBinaryValue_7"] = self.input["peerBinaryValue_7"]
        self.rulebased_controller.input["peerBinaryValue_8"] = self.input["peerBinaryValue_8"]
        self.rulebased_controller.input["peerBinaryValue_9"] = self.input["peerBinaryValue_9"]
        self.rulebased_controller.input["peerBinaryValue_10"] = self.input["peerBinaryValue_10"]
        self.rulebased_controller.input["peerBinaryValue_11"] = self.input["peerBinaryValue_11"]
        
        self.setpoint_controller_1.output = self.output.copy()
        self.setpoint_controller_1.initialize(startTime,
                                        endTime,
                                        stepSize)
        self.rulebased_controller.output = self.output.copy()
        self.rulebased_controller.initialize(startTime,
                                        endTime,
                                        stepSize)


    def do_step(self, secondTime=None, dateTime=None, stepSize=None):

        self.rulebased_controller.input["peerBinaryValue_1"].set(self.input["peerBinaryValue_1"])
        self.rulebased_controller.input["peerBinaryValue_2"].set(self.input["peerBinaryValue_2"])
        self.rulebased_controller.input["peerBinaryValue_3"].set(self.input["peerBinaryValue_3"])
        self.rulebased_controller.input["peerBinaryValue_4"].set(self.input["peerBinaryValue_4"])
        self.rulebased_controller.input["peerBinaryValue_5"].set(self.input["peerBinaryValue_5"])
        self.rulebased_controller.input["peerBinaryValue_6"].set(self.input["peerBinaryValue_6"])
        self.rulebased_controller.input["peerBinaryValue_7"].set(self.input["peerBinaryValue_7"])
        self.rulebased_controller.input["peerBinaryValue_8"].set(self.input["peerBinaryValue_8"])
        self.rulebased_controller.input["peerBinaryValue_9"].set(self.input["peerBinaryValue_9"])
        self.rulebased_controller.input["peerBinaryValue_10"].set(self.input["peerBinaryValue_10"])
        self.rulebased_controller.input["peerBinaryValue_11"].set(self.input["peerBinaryValue_11"])

        self.rulebased_controller.do_step(secondTime=secondTime, dateTime=dateTime, stepSize=stepSize)

        self.setpoint_controller_1.input["TemperatureValue"].set(self.input["actualValueSetpointController"])
        self.setpoint_controller_1.input["setpointValue"].set(next(iter(self.rulebased_controller.output.values())))
        self.setpoint_controller_1.do_step(secondTime=secondTime, dateTime=dateTime, stepSize=stepSize)
        self.output["inputSignal"].set(next(iter(self.setpoint_controller_1.output.values())))
    
        