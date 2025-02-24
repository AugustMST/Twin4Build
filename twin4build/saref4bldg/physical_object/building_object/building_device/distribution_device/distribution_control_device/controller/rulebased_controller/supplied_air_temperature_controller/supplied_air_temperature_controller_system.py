from binascii import b2a_hex
from tabnanny import check
import twin4build.base as base
from twin4build.saref4bldg.physical_object.building_object.building_device.distribution_device.distribution_flow_device.flow_controller.damper import damper
from twin4build.utils.uppath import uppath
import twin4build.utils.input_output_types as tps
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact
from twin4build.base import RulebasedController


def get_signature_pattern():
    node0 = Node(cls=(base.RulebasedController,),id="<Controller\nn<SUB>0</SUB>>")
    # all peer properties
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

    # all building spaces
    node2_1 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>13</SUB>>")
    node2_2 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>14</SUB>>")
    node2_3 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>15</SUB>>")
    node2_4 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>16</SUB>>")
    node2_5= Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>17</SUB>>")
    node2_6= Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>18</SUB>>")
    node2_7= Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>19</SUB>>")
    node2_8= Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>20</SUB>>")
    node2_9= Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>21</SUB>>")
    node2_10= Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>22</SUB>>")
    node2_11 = Node(cls=(base.BuildingSpace,), id="<BuildingSpace\nn<SUB>23</SUB>>")

    # sensors
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

    # all temperature properties
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

    # temperature sensors
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

    # controls
    node6_1 = Node(cls=(base.Temperature), id="<Temperature\nn<SUB>35</SUB>>")

    sp = SignaturePattern(ownedBy="SupplyAirTemperatureController", priority=1100)

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

    #Buidling Space has Peer Property

    sp.add_edge(Exact(object=node2_1, subject=node1_1, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_2, subject=node1_2, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_3, subject=node1_3, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_4, subject=node1_4, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_5, subject=node1_5, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_6, subject=node1_6, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_7, subject=node1_7, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_8, subject=node1_8, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_9, subject=node1_9, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_10, subject=node1_10, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_11, subject=node1_11, predicate="hasProperty"))

    # Building space has Temperature Property

    sp.add_edge(Exact(object=node2_1, subject=node4_1, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_2, subject=node4_2, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_3, subject=node4_3, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_4, subject=node4_4, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_5, subject=node4_5, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_6, subject=node4_6, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_7, subject=node4_7, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_8, subject=node4_8, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_9, subject=node4_9, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_10, subject=node4_10, predicate="hasProperty"))
    sp.add_edge(Exact(object=node2_11, subject=node4_11, predicate="hasProperty"))

    # PeerSensor

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

    # controller controls
    
    sp.add_edge(Exact(object=node0, subject=node6_1, predicate="controls"))

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
    return sp


class SuppliedAirTemperatureControllerSystem(RulebasedController):
    sp = [get_signature_pattern()]
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define inputs and outputs
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
            "TemperatureValue_11": tps.Scalar()
        }
        

        self.stepCounter = 0
        self.output = {"inputSignal": tps.Scalar()}
        self.isReverse = True
        self.defaultValue = 18
        self._config = {"parameters": ["defaultValue"]}

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

        space_list = ["<BuildingSpace\nn<SUB>13</SUB>>","<BuildingSpace\nn<SUB>14</SUB>>","<BuildingSpace\nn<SUB>15</SUB>>",
                      "<BuildingSpace\nn<SUB>16</SUB>>","<BuildingSpace\nn<SUB>17</SUB>>","<BuildingSpace\nn<SUB>18</SUB>>",
                      "<BuildingSpace\nn<SUB>19</SUB>>","<BuildingSpace\nn<SUB>20</SUB>>","<BuildingSpace\nn<SUB>21</SUB>>",
                      "<BuildingSpace\nn<SUB>22</SUB>>","<BuildingSpace\nn<SUB>23</SUB>>"]
        
        self.occupantComfortList = []

        for space in space_list:
            space_node = sp.get_node_by_id(space)
            modeled_space = groups[0][space_node]
            modeled_space = model.instance_map_reversed[modeled_space]
            occupant_comfort_level = modeled_space.occupantComfort
            self.occupantComfortList.append(occupant_comfort_level)

    
    def do_step(self, secondTime=None, dateTime=None, stepSize=None):

        peerBinaryValues = []
        for i in range(1, 12):
            peerBinaryValues.append(self.input[f"peerBinaryValue_{i}"].get())

        TemperatureValues = []
        for i in range(1, 12):
            TemperatureValues.append(self.input[f"TemperatureValue_{i}"].get())
        
        occupant_comfort_list = self.occupantComfortList
        
        occupancy_comfort_occupied = [a * b for a, b in zip(peerBinaryValues, occupant_comfort_list)]

        maximum_value = max(occupancy_comfort_occupied)

        if dateTime is not None:
            current_hour = dateTime.hour
            if 6 <= current_hour < 19:
                if maximum_value <= 0:
                    SAT = self.defaultValue
                else:
                    SAT = maximum_value
            else:
                SAT = self.defaultValue

        
        self.output["inputSignal"].set(SAT)




