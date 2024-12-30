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
    node0 = Node(cls=base.Damper, id="<n<SUB>1</SUB>(Damper)>") #supply damper
    node1 = Node(cls=base.Damper, id="<n<SUB>2</SUB>(Damper)>") #return damper
    node2 = Node(cls=base.BuildingSpace, id="<n<SUB>3</SUB>(BuildingSpace)>")
    node3 = Node(cls=base.Valve, id="<n<SUB>4</SUB>(Valve)>") #supply valve
    node4 = Node(cls=base.SpaceHeater, id="<n<SUB>5</SUB>(SpaceHeater)>")
    node5 = Node(cls=base.Schedule, id="<n<SUB>6</SUB>(Schedule)>") #return valve
    node6 = Node(cls=base.OutdoorEnvironment, id="<n<SUB>7</SUB>(OutdoorEnvironment)>")
    node7 = Node(cls=(base.Coil, base.AirToAirHeatRecovery, base.Fan), id="<Coil, AirToAirHeatRecovery, Fan\nn<SUB>8</SUB>>")
    node8 = Node(cls=base.Temperature, id="<n<SUB>9</SUB>(Temperature)>")
    node9 = Node(cls=base.BuildingSpace, id="<n<SUB>10</SUB>(BuildingSpace)>")
    node10 = Node(cls=base.BuildingSpace, id="<n<SUB>11</SUB>(BuildingSpace)>")
    node11 = Node(cls=base.BuildingSpace, id="<n<SUB>12</SUB>(BuildingSpace)>")
    node12 = Node(cls=base.BuildingSpace, id="<n<SUB>13</SUB>(BuildingSpace)>")
    node13 = Node(cls=base.BuildingSpace, id="<n<SUB>14</SUB>(BuildingSpace)>")
    node14 = Node(cls=base.BuildingSpace, id="<n<SUB>15</SUB>(BuildingSpace)>")
    node15 = Node(cls=base.BuildingSpace, id="<n<SUB>16</SUB>(BuildingSpace)>")
    node16 = Node(cls=base.BuildingSpace, id="<n<SUB>17</SUB>(BuildingSpace)>")
    node17 = Node(cls=base.BuildingSpace, id="<n<SUB>18</SUB>(BuildingSpace)>")
    node18 = Node(cls=base.BuildingSpace, id="<n<SUB>19</SUB>(BuildingSpace)>")
    node19 = Node(cls=base.BuildingSpace, id="<n<SUB>20</SUB>(BuildingSpace)>")

    node21 = Node(cls=base.BuildingSpace, id="<n<SUB>12</SUB>(BuildingSpace)>")
    node22 = Node(cls=base.Sensor, id="<n<SUB>13</SUB>(Sensor)>")
    node23 = Node(cls=base.Temperature, id="<n<SUB>14</SUB>(Temperature)>")

    node24 = Node(cls=base.Sensor, id="<n<SUB>15</SUB>(Sensor)>")

    sp = SignaturePattern(ownedBy="BuildingSpace11AdjBoundaryOutdoorFMUSystem_Tboundary", priority=700)

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
    sp.add_edge(Exact(object=node10, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node11, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node12, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node13, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node14, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node15, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node16, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node17, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node18, subject=node2, predicate="connectedTo"))
    sp.add_edge(Exact(object=node19, subject=node2, predicate="connectedTo"))

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
    sp.add_input("indoorTemperature_adj2", node10, "indoorTemperature")
    sp.add_input("indoorTemperature_adj3", node11, "indoorTemperature")
    sp.add_input("indoorTemperature_adj4", node12, "indoorTemperature")
    sp.add_input("indoorTemperature_adj5", node13, "indoorTemperature")
    sp.add_input("indoorTemperature_adj6", node14, "indoorTemperature")
    sp.add_input("indoorTemperature_adj7", node15, "indoorTemperature")
    sp.add_input("indoorTemperature_adj8", node16, "indoorTemperature")
    sp.add_input("indoorTemperature_adj9", node17, "indoorTemperature")
    sp.add_input("indoorTemperature_adj10", node18, "indoorTemperature")
    sp.add_input("indoorTemperature_adj11", node19, "indoorTemperature")

    sp.add_modeled_node(node4)
    sp.add_modeled_node(node2)

    # cs.add_parameter("globalIrradiation", node2, "globalIrradiation")

    return sp

class BuildingSpace11AdjBoundaryOutdoorFMUSystemTBoundary(FMUComponent, base.BuildingSpace, base.SpaceHeater):
    """
    A class representing an FMU of a building space with 11 adjacent spaces, a space heater, balanced supply and return ventilation, and an outdoor boundary.
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
                infiltration=None,
                airVolume=None,
                occupancyThreshold=0.5,
                **kwargs):
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
        fmu_filename = "R2C2_011adj_0boundary_0outdoor_0FMU.fmu"
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
                    "indoorTemperature_adj2": tps.Scalar(),
                    "indoorTemperature_adj3": tps.Scalar(),
                    "indoorTemperature_adj4": tps.Scalar(),
                    "indoorTemperature_adj5": tps.Scalar(),
                    "indoorTemperature_adj6": tps.Scalar(),
                    "indoorTemperature_adj7": tps.Scalar(),
                    "indoorTemperature_adj8": tps.Scalar(),
                    "indoorTemperature_adj9": tps.Scalar(),
                    "indoorTemperature_adj10": tps.Scalar(),
                    "indoorTemperature_adj11": tps.Scalar(),
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
                    "indoorTemperature_adj2": "T_adj2",
                    "indoorTemperature_adj3": "T_adj3",
                    "indoorTemperature_adj4": "T_adj4",
                    "indoorTemperature_adj5": "T_adj5",
                    "indoorTemperature_adj6": "T_adj6",
                    "indoorTemperature_adj7": "T_adj7",
                    "indoorTemperature_adj8": "T_adj8",
                    "indoorTemperature_adj9": "T_adj9",
                    "indoorTemperature_adj10": "T_adj10",
                    "indoorTemperature_adj11": "T_adj11",
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
                                    "indoorTemperature_adj2": to_degK_from_degC,
                                    "indoorTemperature_adj3": to_degK_from_degC,
                                    "indoorTemperature_adj4": to_degK_from_degC,
                                    "indoorTemperature_adj5": to_degK_from_degC,
                                    "indoorTemperature_adj6": to_degK_from_degC,
                                    "indoorTemperature_adj7": to_degK_from_degC,
                                    "indoorTemperature_adj8": to_degK_from_degC,
                                    "indoorTemperature_adj9": to_degK_from_degC,
                                    "indoorTemperature_adj10": to_degK_from_degC,
                                    "indoorTemperature_adj11": to_degK_from_degC,
                                    "T_boundary": to_degK_from_degC,
                                    "m_infiltration": do_nothing,
                                    "T_infiltration": get(self.output, "indoorTemperature", conversion=to_degK_from_degC)}
        self.output_conversion = {"indoorTemperature": to_degC_from_degK,
                                  "indoorCo2Concentration": do_nothing,
                                  "spaceHeaterPower": change_sign,
                                  "spaceHeaterEnergy": integrate(self.output, "spaceHeaterPower", conversion=multiply_const(1/3600/1000)),
                                  "peerBinary": threshold_get(self.input, "numberOfPeople", threshold=occupancyThreshold)}

        self.INITIALIZED = False
        self._config = {"parameters": list(self.FMUparameterMap.keys()) + ["infiltration", "occupancyThreshold"],}

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

        


        