import twin4build.saref4bldg.building_space.building_space as building_space
from twin4build.utils.fmu.fmu_component import FMUComponent, unzip_fmu
from twin4build.utils.uppath import uppath
from scipy.optimize import least_squares
import numpy as np
import os
import sys
from twin4build.utils.unit_converters.functions import to_degC_from_degK, to_degK_from_degC, do_nothing, change_sign, add, get, integrate, multiply_const, multiply, threshold_get
import twin4build.base as base
from twin4build.utils.signature_pattern.signature_pattern import SignaturePattern, Node, Exact, IgnoreIntermediateNodes, Optional
import twin4build.utils.input_output_types as tps

def get_signature_pattern():
    """
    Get the signature pattern of the FMU component.

    Returns:
        SignaturePattern: The signature pattern of the FMU component.
    """
    node0 = Node(cls=base.Damper, id="<Damper\nn<SUB>1</SUB>>") #supply damper
    node1 = Node(cls=base.Damper, id="<Damper\nn<SUB>2</SUB>>") #return damper
    node2 = Node(cls=base.BuildingSpace, id="<BuildingSpace\nn<SUB>3</SUB>>")
    node3 = Node(cls=base.Valve, id="<Valve\nn<SUB>4</SUB>>") #supply valve
    node4 = Node(cls=base.SpaceHeater, id="<SpaceHeater\nn<SUB>5</SUB>>")
    node5 = Node(cls=base.Schedule, id="<Schedule\nn<SUB>6</SUB>>") #return valve
    node6 = Node(cls=base.OutdoorEnvironment, id="<OutdoorEnvironment\nn<SUB>7</SUB>>")
    node7 = Node(cls=(base.Coil, base.AirToAirHeatRecovery, base.Fan), id="<Coil, AirToAirHeatRecovery, Fan\nn<SUB>8</SUB>>")
    node8 = Node(cls=base.Temperature, id="<Temperature\nn<SUB>9</SUB>>")
    node9 = Node(cls=base.BuildingSpace, id="<BuildingSpace\nn<SUB>10</SUB>>")
    node10 = Node(cls=base.Sensor, id="<Sensor\nn<SUB>11</SUB>>") ## for Applied energy paper
    node11 = Node(cls=base.Temperature, id="<Temperature\nn<SUB>12</SUB>>") ## for Applied energy paper
    node12 = Node(cls=base.PropertyValue, id="<PropertyValue\nn<SUB>13</SUB>>")
    node13 = Node(cls=(float, int), id="<Float\nn<SUB>14</SUB>>")
    node14 = Node(cls=base.OutputCapacity, id="<OutputCapacity\nn<SUB>15</SUB>>")
    node15 = Node(cls=base.PropertyValue, id="<PropertyValue\nn<SUB>16</SUB>>")
    node16 = Node(cls=str, id="<String\nn<SUB>17</SUB>>")
    node17 = Node(cls=base.TemperatureRating, id="<TemperatureRating\nn<SUB>18</SUB>>")

    node21 = Node(cls=base.BuildingSpace, id="<n<SUB>12</SUB>(BuildingSpace)>")
    node22 = Node(cls=base.Sensor, id="<n<SUB>13</SUB>(Sensor)>")
    node23 = Node(cls=base.Temperature, id="<n<SUB>14</SUB>(Temperature)>")
    node24 = Node(cls=base.Sensor, id="<n<SUB>15</SUB>(Sensor)>")

    sp = SignaturePattern(ownedBy="BuildingSpace1AdjBoundaryOutdoorFMUSystem_Tboundary", priority=180)

    sp.add_edge(Exact(object=node0, subject=node2, predicate="suppliesFluidTo"))
    sp.add_edge(Exact(object=node1, subject=node2, predicate="hasFluidReturnedBy"))
    sp.add_edge(Exact(object=node3, subject=node2, predicate="isContainedIn"))
    sp.add_edge(Exact(object=node4, subject=node2, predicate="isContainedIn"))
    sp.add_edge(Exact(object=node3, subject=node4, predicate="suppliesFluidTo"))
    sp.add_edge(Exact(object=node2, subject=node5, predicate="hasProfile"))
    sp.add_edge(Exact(object=node2, subject=node6, predicate="connectedTo"))
    sp.add_edge(IgnoreIntermediateNodes(object=node0, subject=node7, predicate="hasFluidSuppliedBy"))
    # sp.add_edge(Exact(object=node7, subject=node8, predicate="observes"))
    sp.add_edge(Exact(object=node9, subject=node2, predicate="connectedTo"))
    # sp.add_edge(IgnoreIntermediateNodes(object=node10, subject=node3, predicate="suppliesFluidTo")) ## for Applied energy paper
    # sp.add_edge(Exact(object=node10, subject=node11, predicate="observes")) ## for Applied energy paper
    # sp.add_edge(Exact(object=node12, subject=node13, predicate="hasValue"))
    # sp.add_edge(Exact(object=node12, subject=node14, predicate="isValueOfProperty"))
    # sp.add_edge(Optional(object=node4, subject=node12, predicate="hasPropertyValue"))
    # sp.add_edge(Exact(object=node15, subject=node16, predicate="hasValue"))
    # sp.add_edge(Exact(object=node15, subject=node17, predicate="isValueOfProperty"))
    # sp.add_edge(Optional(object=node4, subject=node15, predicate="hasPropertyValue"))

    sp.add_edge(Exact(object=node2, subject=node24, predicate="contains"))
    sp.add_edge(Exact(object=node24, subject=node23, predicate="observes"))

    sp.add_edge(Exact(object=node21, subject=node22, predicate="contains"))
    sp.add_edge(Exact(object=node21, subject=node23, predicate="hasProperty"))
    sp.add_edge(Exact(object=node22, subject=node23, predicate="observes"))

    sp.add_input("T_boundary", node24, "measuredValue")
    sp.add_input("airFlowRate", node0)
    sp.add_input("waterFlowRate", node3)
    sp.add_input("numberOfPeople", node5, "scheduleValue")
    sp.add_input("outdoorTemperature", node6, "outdoorTemperature")
    sp.add_input("outdoorCo2Concentration", node6, "outdoorCo2Concentration")
    sp.add_input("globalIrradiation", node6, "globalIrradiation")
    sp.add_input("supplyAirTemperature", node7, ("outletAirTemperature", "primaryTemperatureOut", "outletAirTemperature"))
    sp.add_input("indoorTemperature_adj1", node9, "indoorTemperature")
    # sp.add_input("supplyWaterTemperature", node10, "measuredValue") ## for Applied energy paper

    sp.add_modeled_node(node4)
    sp.add_modeled_node(node2)

    # cs.add_parameter("globalIrradiation", node2, "globalIrradiation")

    return sp


class BuildingSpace1AdjBoundaryOutdoorFMUSystemTBoundary(FMUComponent, base.BuildingSpace, base.SpaceHeater):
    """
    A class representing an FMU of a building space with 1 adjacent spaces, a space heater, balanced supply and return ventilation, and an outdoor boundary.
    """
    sp = [get_signature_pattern()]
    def __init__(self,
                C_supply=None,
                C_wall=None,
                C_air=None,
                C_int=None,
                C_boundary=None,
                R_out=None,
                R_in=None,
                R_int=None,
                R_boundary=None,
                f_wall=None,
                f_air=None,
                Q_occ_gain=None,
                CO2_occ_gain=None,
                CO2_start=None,
                fraRad_sh=None,
                Q_flow_nominal_sh=None,
                T_a_nominal_sh=None,
                T_b_nominal_sh=None,
                TAir_nominal_sh=None,
                n_sh=None,
                infiltration=0.005,
                airVolume=None,
                occupancyThreshold = 0.5,
                **kwargs):
        """
        Initialize a BuildingSpace1AdjBoundaryOutdoorFMUSystem object.

        Args:
            C_supply (float, optional): The CO2 concentration of the supply air. Defaults to None.
            C_wall (float, optional): The thermal capacitance of the wall. Defaults to None.
            C_air (float, optional): The thermal capacitance of the air. Defaults to None.
            C_int (float, optional): The thermal capacitance of the interior walls. Defaults to None.
            C_boundary (float, optional): The thermal capacitance of the boundary. Defaults to None.
            R_out (float, optional): The exterior wall outer thermal resistance. Defaults to None.
            R_in (float, optional): The exteriorwall inner thermal resistance. Defaults to None.
            R_int (float, optional): The thermal resistance of the interior walls. Defaults to None.
            R_boundary (float, optional): The boundary thermal resistance. Defaults to None.
            f_wall (float, optional): The fraction of solar radiation that is absorbed by the wall. Defaults to None.
            f_air (float, optional): The fraction of solar radiation that is absorbed by the air. Defaults to None.
            Q_occ_gain (float, optional): The occupancy thermal gain of the building space. Defaults to None.
            CO2_occ_gain (float, optional): The occupancy CO2 generation rate of the building space. Defaults to None.
            CO2_start (float, optional): The occupancy CO2 concentration of the building space. Defaults to None.
            fraRad_sh (float, optional): The fraction of radiation of the space heater. Defaults to None.
            Q_flow_nominal_sh (float, optional): The nominal heat flow rate of the space heater. Defaults to None.
            T_a_nominal_sh (float, optional): The nominal supply air temperature of the space heater. Defaults to None.
            T_b_nominal_sh (float, optional): The nominal return air temperature of the space heater. Defaults to None.
            TAir_nominal_sh (float, optional): The nominal air temperature of the space heater. Defaults to None.
            n_sh (float, optional): The nominal heat transfer coefficient of the space heater. Defaults to None.
            T_boundary (float, optional): The boundary temperature of the building space. Defaults to None.
            infiltration (float, optional): The infiltration rate of the building space. Defaults to None.
            airVolume (float, optional): The air volume of the building space. Defaults to None.
        """
        building_space.BuildingSpace.__init__(self, **kwargs)


        self.C_supply = C_supply#400
        self.C_wall = C_wall#1
        self.C_air = C_air#1
        self.C_int = C_int#1
        self.C_boundary = C_boundary#1
        self.R_out = R_out#1
        self.R_in = R_in#1
        self.R_int = R_int#1
        self.R_boundary = R_boundary#1
        self.f_wall = f_wall#1
        self.f_air = f_air#1
        self.Q_occ_gain = Q_occ_gain#80
        self.CO2_occ_gain = CO2_occ_gain#8.18E-6
        self.CO2_start = CO2_start#400      
        self.fraRad_sh = fraRad_sh#0.35
        self.Q_flow_nominal_sh = Q_flow_nominal_sh#1000
        self.T_a_nominal_sh = T_a_nominal_sh
        self.T_b_nominal_sh = T_b_nominal_sh
        self.TAir_nominal_sh = TAir_nominal_sh
        self.n_sh = n_sh#1.24
        self.infiltration = infiltration
        self.airVolume = airVolume
        self.occupancyThreshold = occupancyThreshold




        self.start_time = 0
        # fmu_filename = "EPlusFan_0FMU.fmu"#EPlusFan_0FMU_0test2port
        fmu_filename = "R2C2_01adj_0boundary_0outdoor_0FMU.fmu"
        self.fmu_path = os.path.join(uppath(os.path.abspath(__file__), 1), fmu_filename)
        self.unzipdir = unzip_fmu(self.fmu_path)

        self.input = {'airFlowRate': tps.Scalar(),
                    'waterFlowRate': tps.Scalar(),
                    'supplyAirTemperature': tps.Scalar(),
                    'supplyWaterTemperature': tps.Scalar(),
                    'globalIrradiation': tps.Scalar(),
                    'outdoorTemperature': tps.Scalar(),
                    'numberOfPeople': tps.Scalar(),
                    "outdoorCo2Concentration": tps.Scalar(),
                    "indoorTemperature_adj1": tps.Scalar(),
                    "T_boundary": tps.Scalar(),
                    "m_infiltration": tps.Scalar(),
                    "T_infiltration": tps.Scalar()}
        self.output = {"indoorTemperature": tps.Scalar(), 
                       "indoorCo2Concentration": tps.Scalar(), 
                       "spaceHeaterPower": tps.Scalar(),
                        "spaceHeaterEnergy": tps.Scalar(),
                        "peerBinary": tps.Scalar()}
        
        self.FMUinputMap = {'airFlowRate': "m_a_flow",
                    'waterFlowRate': "m_w_flow",
                    'supplyAirTemperature': "T_a_supply",
                    'supplyWaterTemperature': "T_w_supply",
                    'globalIrradiation': "Rad_outdoor",
                    'outdoorTemperature': "T_outdoor",
                    'numberOfPeople': "N_occ",
                    "outdoorCo2Concentration": "CO2_supply",
                    "indoorTemperature_adj1": "T_adj1",
                    "T_boundary": "T_boundary",
                    "m_infiltration": "m_infiltration",
                    "T_infiltration": "T_infiltration"}
        self.FMUoutputMap = {"indoorTemperature": "T_air", 
                             "indoorCo2Concentration": "CO2_concentration",
                             "spaceHeaterPower": "r2C2_1.rad.Q_flow"}

        self.FMUparameterMap = {"C_supply": "C_supply",
                                "C_wall": "C_wall", 
                                "C_air": "C_air",
                                "C_int": "C_int",
                                "C_boundary": "C_boundary",
                                "R_out": "R_out", 
                                "R_in": "R_in", 
                                "R_int": "R_int",
                                "R_boundary": "R_boundary",
                                "f_wall": "f_wall", 
                                "f_air": "f_air", 
                                "Q_occ_gain": "Q_occ_gain", 
                                "CO2_occ_gain": "CO2_occ_gain", 
                                "CO2_start": "CO2_start",  
                                "airVolume": "airVolume",
                                "fraRad_sh": "fraRad_sh", 
                                "Q_flow_nominal_sh": "Q_flow_nominal_sh", 
                                "T_a_nominal_sh": "T_a_nominal_sh", 
                                "T_b_nominal_sh": "T_b_nominal_sh", 
                                "TAir_nominal_sh": "TAir_nominal_sh", 
                                "n_sh": "n_sh"}


        self.input_conversion = {'airFlowRate': do_nothing,
                                    'waterFlowRate': do_nothing,
                                    'supplyAirTemperature': to_degK_from_degC,
                                    'supplyWaterTemperature': to_degK_from_degC,
                                    'globalIrradiation': do_nothing,
                                    'outdoorTemperature': to_degK_from_degC,
                                    'numberOfPeople': do_nothing,
                                    "outdoorCo2Concentration": do_nothing,
                                    "indoorTemperature_adj1": to_degK_from_degC,
                                    "T_boundary": to_degK_from_degC,
                                    "m_infiltration": do_nothing,
                                    "T_infiltration": get(self.output, "indoorTemperature", conversion=to_degK_from_degC)}
        self.output_conversion = {"indoorTemperature": to_degC_from_degK, 
                                  "indoorCo2Concentration": do_nothing,
                                  "spaceHeaterPower": change_sign,
                                  "spaceHeaterEnergy": integrate(self.output, "spaceHeaterPower", conversion=multiply_const(1/3600/1000)),
                                  "peerBinary": threshold_get(self.input, "numberOfPeople", threshold=occupancyThreshold)
                                  }

        self.INITIALIZED = False
        self._config = {"parameters": list(self.FMUparameterMap.keys()) + ["infiltration", "occupancyThreshold"]}

    @property
    def config(self):
        """
        Get the configuration of the FMU component.

        Returns:
            dict: The configuration of the FMU component.
        """
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
        Initialize the FMU component.

        Args:
            startTime (float, optional): The start time of the simulation. Defaults to None.
            endTime (float, optional): The end time of the simulation. Defaults to None.
            stepSize (float, optional): The step size of the simulation. Defaults to None.
            model (Model, optional): The model of the simulation. Defaults to None.
        '''
        if self.INITIALIZED:
            self.reset()
        else:
            self.initialize_fmu()
            self.INITIALIZED = True ###
        self.input["m_infiltration"] = tps.Scalar(self.infiltration)
        self.output_conversion["spaceHeaterEnergy"].v = 0

        

        


        