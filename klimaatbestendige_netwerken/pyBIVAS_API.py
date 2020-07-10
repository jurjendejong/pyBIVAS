from typing import Dict
import requests
import xmltodict
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# TODO: Implement method to adjust this in an easy way
data_post_calculation = """
<Output>
    <OverallStatistics>
        <Change>Enabled</Change>
    </OverallStatistics>
    <Trips>
        <Change>Enabled</Change>
    </Trips>
    <Routes>
        <Change>Enabled</Change>
    </Routes>
    <RouteStatistics>
        <Change>Enabled</Change>
    </RouteStatistics>
    <RoutePerCountryStatistics>
        <Change>Neutral</Change>
    </RoutePerCountryStatistics>
    <InfeasibleTrips>
        <Change>Enabled</Change>
    </InfeasibleTrips>
    <ArcStatistics>
        <Change>Enabled</Change>
    </ArcStatistics>
    <ArcUsage>
        <Change>Enabled</Change>
    </ArcUsage>
    <ArcUsageDetails>
        <Change>Enabled</Change>
    </ArcUsageDetails>
    <OriginTripEndPoint>
        <Change>Neutral</Change>
    </OriginTripEndPoint>
    <DestinationTripEndPoint>
        <Change>Neutral</Change>
    </DestinationTripEndPoint>
    <CountingPoint>
        <Change>Enabled</Change>
    </CountingPoint>
    <WaitingTime>
        <Change>Enabled</Change>
    </WaitingTime>
    <Emission>
        <Change>Enabled</Change>
    </Emission>
    <ReferenceComparison>
        <Change>Enabled</Change>
    </ReferenceComparison>
</Output>
"""


class BIVAS_API:
    """
    This is a python API to the Bivas web interface. It access the REST protocol that is supported and helps the
    application by providing easy-to-use functions.
    """

    # Response documentation:
    # 200: Sucesfull!
    # 404: Error in syntax
    # 500: Cannot do this action. Scenario locked?
    # 415: Wrong input format

    post_headers = {'Content-Type': 'application/xml; charset=UTF-8'}
    get_headers = {'Accept': 'application/xml'}

    data_post_calculation = data_post_calculation

    def __init__(self):
        self.bivas_url = 'http://127.0.0.1'

    def get_input_parameters(self, scenario_id):
        # Get all input parameters of scenario
        url = f'{self.bivas_url}/Scenarios/{scenario_id}/Input/Parameters'
        return self.get_request(url, self.get_headers)

    def post_calculation(self, scenario_id, data_post_calculation=None):
        # start simulation
        url = f'{self.bivas_url}/Scenarios/{scenario_id}/Calculate'
        if data_post_calculation is None:
            data_post_calculation = self.data_post_calculation
        requests.post(url, data=data_post_calculation, headers=self.post_headers, verify=False)

    def get_output_overallstatistics(self, scenario_id):
        # Get all statistics (only available after run completed)
        url = f'{self.bivas_url}/Scenarios/{scenario_id}/Output/OverallStatistics'
        return self.get_request(url, self.get_headers)

    def get_scenario(self, scenario_id):
        # Get all details on scenario
        url = f'{self.bivas_url}/Scenarios/{scenario_id}/'
        return self.get_request(url, self.get_headers)

    def put_single_input_parameter(self, scenario_id: int, parameters: Dict):
        # Change single or multiple input parameters.
        # Possible parameters: ScenarioYear, Start_MonthDay, End_MonthDay, SeasonDefinitionID, MinimumDepth__m,
        # MaximumDepth__m, LengthVariableSelector, WidthVariableSelector, DangerousGoodsLevelVariableSelector,
        # DepthVariableSelector, HeightVariableSelector, WaterScenarioID, GrowthRateID, FleetMutationScenarioID,
        # MotorReplacementProfileID, OptimizationObjectiveID, MaximumUnLoadFactorForInfeasibleTrips, FuelPrice__Euro_L,
        # InterestRate, TimeWaitingOnLoad__h, TrafficScenarioID, TravelTimeStandardDeviation__s_min, ZoneDefinitionID,
        # RestrictionRelaxationEnabled, RestrictionRelaxationLengthPenalty__min_m_km, RestrictionRelaxationWidthPenalty__min_dm_km,
        # IdleEnergyUseFactor, ReferenceTripSetID,

        for param, param_value in parameters.items():
            url = f'{self.bivas_url}/Scenarios/{scenario_id}/Input/Parameters/{param}'
            data = f'<{param}>{param_value}</{param}>'
            d = requests.put(url, data=data, headers=self.post_headers, verify=False)
        return d

    @staticmethod
    def get_request(url, headers):
        try:
            d = requests.get(url, data=None, headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            logger.error('Connection abort error')
            return None

        if d.status_code != 200:
            logger.error(f'Response code: {d.status_code}')
        else:
            d.dict = xmltodict.parse(d.text)
        return d


#     def put_input_parameters(self, scenario_id: int, xmlfile_inputsettings):  # WIP, maybe beause xmlfile is outdated
#         url = f'{self.bivas_url}/Scenarios/{scenario_id}/Input/Parameters'
#         with open(xmlfile_inputsettings, 'rb') as data:
#             d = requests.post(url, data=data, headers=self.post_headers, verify=False)
#         return d





if __name__ == '__main__':
    B = BIVAS_API()

    B.put_single_input_parameter(52, {'InterestRate': '10.0'})
    B.get_output_overallstatistics(52)
    B.get_scenario(52)
    B.post_calculation(53, r'Data/Output.xml')
    B.get_output_overallstatistics(53)
    d = B.get_input_parameters(54)

    if d.status_code == 200:
        print(d.text)
        print(d.dict)
    # B.put_input_parameters(52, r'Data/Input.xml')


