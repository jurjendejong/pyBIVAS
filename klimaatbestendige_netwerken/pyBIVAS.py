# -*- coding: utf-8 -*-
"""
Postprocessing module of the SQL-database of the Inland navigation tool BIVAS.
It will help in geting more specific results out of this huge database.

Jurjen de Jong, Deltares
"""
import pandas as pd
import networkx as nx
import sqlite3
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import geopandas
    from shapely.geometry import Point, LineString
except:
    logger.warning('Loading of geopandas/shapely failed. Geometric functions will not work')


class pyBIVAS:
    """
    This class helps in postprocessing BIVAS data
    """

    NSTR_shortnames = {
        -2: 'Onbekend',
        -1: 'Leeg (geen lading)',
        0: '0 - Landbouw',
        1: '1 - Voeding en vee',
        2: '2 - Mineralen',
        3: '3 - Aardolie',
        4: '4 - Ertsen',
        5: '5 - Staal',
        6: '6 - Bouwmaterialen',
        7: '7 - Meststoffen',
        8: '8 - Chemische prod.',
        9: '9 - Goederen'
    }

    appeareance_rename = {
        'Overig': 'Leeg'
    }

    compute_route_statistics = """
        SUM(trips.NumberOfTrips) AS "Aantal Vaarbewegingen (-)",
        SUM(trips.TotalWeight__t * trips.NumberOfTrips) AS "Totale Vracht (ton)",
        SUM(trips.TwentyFeetEquivalentUnits * trips.NumberOfTrips) AS "Totale TEU (-)",
        SUM(route_statistics.TravelTime__min  * trips.NumberOfTrips) AS "Totale Reistijd (min)",
        SUM(route_statistics.VariableTimeCosts__Eur * trips.NumberOfTrips) + SUM(route_statistics.VariableDistanceCosts__Eur * trips.NumberOfTrips) + SUM(route_statistics.FixedCosts__Eur  * trips.NumberOfTrips) AS "Totale Vaarkosten (EUR)",
        SUM(route_statistics.VariableTimeCosts__Eur * trips.NumberOfTrips) + SUM(route_statistics.VariableDistanceCosts__Eur * trips.NumberOfTrips) AS "Totale Variabele Vaarkosten (EUR)",
        SUM(route_statistics.VariableTimeCosts__Eur * trips.NumberOfTrips) AS "Totale Variabele-Tijd Vaarkosten (EUR)",
        SUM(route_statistics.VariableDistanceCosts__Eur * trips.NumberOfTrips) AS "Totale Variabele-Afstand Vaarkosten (EUR)",
        SUM(route_statistics.FixedCosts__Eur * trips.NumberOfTrips) AS "Totale Vaste Vaarkosten (EUR)",
        SUM(route_statistics.Distance__km * trips.NumberOfTrips) AS "Totale Afstand (km)",
        SUM((trips.TotalWeight__t * route_statistics.Distance__km) * trips.NumberOfTrips) AS "Totale TonKM (TONKM)"
    """

    directions_dutch = {
        'Downstream': 'Benedenstrooms',
        'South-East': 'Zuid-Oost',
        'South-West': 'Zuid-West',
        'West': 'West',
        'South': 'Zuid',
        'North': 'Noord',
        'East': 'Oost',
        'North-East': 'Noord-Oost',
        'North-West': 'Noord-West',
        'Upstream': 'Bovenstrooms'
    }

    def __init__(self, databasefile=None):
        """
        Initialise class
        """
        if databasefile:
            self.connectToSQLiteDatabase(databasefile)

    def connectToMySQLDatabase(self, host='localhost', user='root', password='', db='bivas'):
        """
        Connect to MySQL database
        By default connects to localhost
        """

        import pymysql.cursors
        import pymysql

        self.connection = pymysql.connect(host=host,
                                          user=user,
                                          password=password,
                                          db=db,
                                          charset='utf8mb4',
                                          cursorclass=pymysql.cursors.DictCursor)

        return self.connection

    def connectToSQLiteDatabase(self, databasefile):
        """
        Connect to sqlite3 databasefile (.db)
        """
        logger.info('Loading database: {}'.format(databasefile))

        self.databasefile = Path(databasefile)
        assert self.databasefile.exists(), 'Database does not exist'

        self.connection = sqlite3.connect(self.databasefile)
        return self.connection

    def set_scenario(self, scenario=None):
        """
        Set scenario to perform analysis
        An int will be assumed to be the id
        A string will be assumed to be the name
        """

        scenarioOverview = self.scenario_parameters()

        if isinstance(scenario, int):
            self.scenarioID = scenario
            self.scenarioName = scenarioOverview.loc[self.scenarioID, 'Name']
        elif isinstance(scenario, str):
            self.scenarioName = scenario
            self.scenarioID = scenarioOverview[scenarioOverview['Name'] == self.scenarioName].index[0]
        else:
            self.scenarioID = scenarioOverview[scenarioOverview['Locked'] == 1].index[0]
            self.scenarioName = scenarioOverview.loc[self.scenarioID, 'Name']
            logger.info(f'ScenarioID not given. Assuming scenario: {self.scenarioID} - {self.scenarioName}')

        self.trafficScenario = scenarioOverview.loc[self.scenarioID,
                                                    'TrafficScenarioID']
        self.WaterScenarioID = scenarioOverview.loc[self.scenarioID,
                                                    'WaterScenarioID']
        self.ReferenceTripSetID = scenarioOverview.loc[self.scenarioID,
                                                       'ReferenceTripSetID']

    # Basic lists

    def scenario_parameters(self):
        """Overview of all scenarios with parameters"""

        sql = """
        SELECT *
        FROM scenarios
        JOIN branching$branch_sets ON scenarios.ID = branching$branch_sets.BranchID
        JOIN parameters ON branching$branch_sets.ID = parameters.BranchSetID
        ORDER BY scenarios.ID
        """
        df = self.sql(sql)
        df = df.set_index('ID')
        return df

    def appearancetypes(self, rename_to_Leeg=True):
        sql = """SELECT * FROM appearance_types ORDER BY Id"""
        appearance_types = self.sql(sql).set_index('ID')
        if rename_to_Leeg:
            appearance_types.replace({'Description': self.appeareance_rename}, inplace=True)
        return appearance_types

    def CEMTclass(self):
        sql = """SELECT * FROM cemt_class ORDER BY Id"""
        cemt_class = self.sql(sql).set_index('Id')
        return cemt_class

    def shiptypes(self):
        sql = """
        SELECT ship_types.*, cemt_class.Description
        FROM ship_types
        LEFT JOIN cemt_class ON CEMTTypeID=cemt_class.ID
        ORDER BY CEMTTypeID, Id"""
        ship_types = self.sql(sql).set_index('ID')
        return ship_types

    def trafficscenario_numberoftrips(self):
        """Count trips per traffic scenario"""
        sql = """
        SELECT traffic_scenarios.ID, traffic_scenarios.Description, count(*)
        FROM trips
        LEFT JOIN traffic_scenarios ON TrafficScenarioID = traffic_scenarios.ID
        GROUP BY TrafficScenarioID"""
        df = self.sql(sql)
        df.set_index('ID', inplace=True)
        return df

    def trafficscenario_timeseries(self):
        """Trips in trafficScenario per date"""

        sql = """
        SELECT DATE(trips.DateTime) AS date,
               COUNT(*) AS nTrips,
               AVG(TotalWeight__t) as AvgTotalWeight__t,
               AVG(NumberOfTrips) as AvgNumberOfTrips
        FROM trips
        LEFT JOIN traffic_scenarios ON TrafficScenarioID = traffic_scenarios.ID
        WHERE traffic_scenarios.ID = '{0}'
        GROUP BY DATE(trips.DateTime)
        """.format(self.trafficScenario)
        df = self.sql(sql)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df

    def trips_timeseries(self):
        """Trips in scenario per date"""

        sql = """
        SELECT DATE(DateTime) AS date,
               count(*) AS nTrips,
               AVG(TotalWeight__t) as AvgTotalWeight__t,
               SUM(TotalWeight__t * NumberOfTrips) as SumTotalWeight__t,
               SUM(NumberOfTrips) as SumNumberOfTrips
        FROM trips_{0}
        GROUP BY DATE(DateTime)
        """.format(self.scenarioID)
        df = self.sql(sql)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df

    def trips_details(self):
        """Get all trip properties"""
        sql = """
        SELECT trips.*,
               ship_types.Label,
               ship_types.Description,
               nstr_mapping.Description AS nstr_description,
               appearance_types.Description AS appear_description,
               dangerous_goods_levels.Description AS dangerous_description
        FROM trips_{0} AS trips
        LEFT JOIN ship_types ON trips.ShipTypeID = ship_types.ID
        LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode
        LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID
        LEFT JOIN dangerous_goods_levels ON trips.DangerousGoodsLevelID = dangerous_goods_levels.ID
        """.format(self.scenarioID)

        df = self.sql(sql)
        df = df.set_index('ID')
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df = df.drop(['SeasonID', 'ShipTypeID', 'DangerousGoodsLevelID', 'LoadTypeID'], axis=1)

        return df

    def trips_statistics(self, tripsArray: list):
        """
        Get route statistics for an array of given trips
        """

        listOfTrips = ",".join(str(t) for t in tripsArray)

        sql = f"""
        SELECT trips.ID,
               {self.compute_route_statistics}
            FROM trips_{self.scenarioID} AS trips
            LEFT JOIN route_statistics_{self.scenarioID} AS route_statistics ON route_statistics.TripID = trips.ID
            WHERE trips.ID IN ({listOfTrips})
            GROUP BY trips.ID
        """
        df2 = self.sql(sql)
        df2 = df2.set_index('ID')
        return df2

    def routestatistics_advanced(self, group_by=['Vorm', 'NSTR']):
        """
        Advanced query for requesting all results in combinations of groupable parameters. The following groupings are possible:

        - TripsID: Generate statistics for all individual trips
        - Days: Generate output on daily frequency
        - NSTR: Classification of loads
        - Vorm: Classification of appearance type
        - Origin_Node: Group by node of origin port
        - Destination_Node: Group by node of destination port
        - Origin_NUTS3: Group by NUTS3 area of origins
        - Destination_NUTS3: Group by NUTS3 area of destinations
        """

        sql_select = ''
        sql_groupby = ''
        sql_leftjoin = ''
        sql_where = ''

        if not group_by:
            sql_groupby = 'Null'
        else:
            if 'TripsID' in group_by:
                sql_select += 'trips.ID AS "TripsID",'
                sql_groupby += 'trips.ID, '

            if 'Days' in group_by:
                sql_select += 'DATE(trips.DateTime) AS "Days",'
                sql_groupby += 'Days, '

            if 'NSTR' in group_by:
                sql_select += 'nstr_mapping.GroupCode AS "NSTR",'
                sql_groupby += 'NstrGoodsClassification, '
                sql_leftjoin += 'LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode '

            if 'NST2007' in group_by:
                sql_select += 'nst2007_mapping.Id || "] " || nst2007_mapping.GroupCode || " - " || nst2007_mapping.Description AS "NST2007",'
                sql_groupby += 'Nst2007GoodsClassification, '
                sql_leftjoin += 'LEFT JOIN nst2007_mapping ON trips.Nst2007GoodsClassification = nst2007_mapping.Id '

            if 'Vorm' in group_by:
                sql_select += 'appearance_types.Description AS "Vorm",'
                sql_groupby += 'trips.AppearanceTypeID, '
                sql_leftjoin += 'LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID '

            if 'Origin_Node' in group_by:
                sql_select += 'trips.OriginTripEndPointNodeID AS "Origin_Node",'
                sql_select += 'nodes_origin.XCoordinate AS "Origin_X",'
                sql_select += 'nodes_origin.YCoordinate AS "Origin_Y",'
                sql_groupby += 'trips.OriginTripEndPointNodeID, '
                sql_leftjoin += 'LEFT JOIN nodes AS nodes_origin ON trips.OriginTripEndPointNodeID = nodes_origin.ID '

            if 'Destination_Node' in group_by:
                sql_select += 'trips.DestinationTripEndPointNodeID AS "Destination_Node",'
                sql_select += 'nodes_destination.XCoordinate AS "Destination_X",'
                sql_select += 'nodes_destination.YCoordinate AS "Destination_Y",'
                sql_groupby += 'trips.DestinationTripEndPointNodeID, '
                sql_leftjoin += 'LEFT JOIN nodes AS nodes_destination ON trips.DestinationTripEndPointNodeID = nodes_destination.ID '

            if 'Origin_NUTS3' in group_by:
                sql_leftjoin += 'LEFT JOIN zone_node_mapping ON trips.OriginTripEndPointNodeID = zone_node_mapping.NodeID '
                sql_leftjoin += 'LEFT JOIN zones ON zone_node_mapping.ZoneID = zones.ID '
                sql_groupby += 'zones.ID, '
                sql_select += 'zones.Name AS Origin_NUTS3, '
                sql_where += ' zones.ZoneDefinitionID = 7 AND zone_node_mapping.ZoneDefinitionID = 7 AND '

            if 'Destination_NUTS3' in group_by:
                sql_leftjoin += 'LEFT JOIN zone_node_mapping ON trips.DestinationTripEndPointNodeID = zone_node_mapping.NodeID '
                sql_leftjoin += 'LEFT JOIN zones ON zone_node_mapping.ZoneID = zones.ID '
                sql_groupby += 'zones.ID, '
                sql_select += 'zones.Name AS Destination_NUTS3, '
                sql_where += ' zones.ZoneDefinitionID = 7 AND zone_node_mapping.ZoneDefinitionID = 7 AND '

            sql_groupby = sql_groupby[:-2]
            sql_where = sql_where[:-5]

        if not sql_where:
            sql_where = '1'

        sql = f"""
        SELECT {sql_select}
               {self.compute_route_statistics}
        FROM route_statistics_{self.scenarioID} AS route_statistics
        LEFT JOIN trips_{self.scenarioID} AS trips ON route_statistics.TripID = trips.ID
        {sql_leftjoin}
        WHERE {sql_where}
        GROUP BY {sql_groupby}
        """

        df = self.sql(sql)

        # Use short strings for NSTR classes
        df = df.replace({'NSTR': self.NSTR_shortnames})

        if group_by and 'Origin_NUTS3' in group_by:
            df['Afkorting'] = df['Origin_NUTS3'].str.split(pat=' - ', expand=True)[0]

        if group_by and 'Destination_NUTS3' in group_by:
            df['Afkorting'] = df['Destination_NUTS3'].str.split(pat=' - ', expand=True)[0]

        # Format dates
        if group_by and 'Days' in group_by:
            df['Days'] = pd.to_datetime(df['Days'])

        # TODO: Nog goede indexering (en volgorde) instellen
        if group_by:
            df = df.set_index(group_by).sort_index()
        return df

    def routestatistics_timeseries(self):
        """Routes in scenario per date"""

        if self.sql_tableexists(f'route_statistics_{self.scenarioID}'):
            sql = f"""
            SELECT DATE(trips.DateTime) AS date,
                   COUNT(*) AS count,
                   {self.compute_route_statistics}
            FROM route_statistics_{self.scenarioID} AS route_statistics
            LEFT JOIN trips_{self.scenarioID} AS trips ON route_statistics.TripID = trips.ID
            GROUP BY DATE(trips.DateTime)
            """
        else:
            sql = """
            SELECT DATE(trips_{0}.DateTime) AS date,
                   COUNT(*) AS count
            FROM routes_{0}
            LEFT JOIN trips_{0} ON routes_{0}.TripID = trips_{0}.ID
            WHERE RouteIndex=0
            GROUP BY DATE(trips_{0}.DateTime)
            """.format(self.scenarioID)

        df = self.sql(sql)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df

    def route_arcs(self, routeID):
        """
        Load route on arcs for a specified RouteID

        requires the run of sqlArcs()
        """
        sql = """
        SELECT ArcID, OriginalArcDirection
        FROM routes_{0}
        WHERE TripID = {1}
        ORDER BY RouteIndex
        """.format(self.scenarioID, routeID)
        route = self.sql(sql)
        route = route.join(self.arcs, on='ArcID')
        route = geopandas.GeoDataFrame(route)
        return route

    def route_stats(self, routeID):
        """
        Load advanced route and shipstats for specified RouteID
        """
        sql = """
        SELECT  trips.*,
                route.*,
                nstr_mapping.Description AS nstr_description,
                appearance_types.Description AS appear_description,
                ship_types.Label AS ship_label,
                ship_types.Description as ship_description,
                dangerous_goods_levels.Description AS dangerous_description
        FROM route_statistics_{0} AS route
        LEFT JOIN trips_{0} AS trips ON route.TripID = trips.ID
        LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode
        LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID
        LEFT JOIN ship_types ON trips.ShipTypeID = ship_types.ID
        LEFT JOIN dangerous_goods_levels ON trips.DangerousGoodsLevelID = dangerous_goods_levels.ID
        WHERE TripID = {1}
        """.format(self.scenarioID, routeID)
        routestats = self.sql(sql)
        return routestats

    def route_countingpoints(self, routeID, validateroute=None):
        """
        Validate the route of a routeID versus the reference tripset

        routeID = int
        validateroute =
            None: do not validate
            route: input the route (output of BIVAS.route_arcs(arcID))
            'route': run route_arcs first
        ReferenceSetID = int (3 = IVS90_2014)

        requires the run of sqlArcs()
        """

        sql = """
        SELECT DateTime, Name, ArcID
        FROM reference_trip_set
        LEFT JOIN counting_points ON reference_trip_set.CountingPointID = counting_points.ID
        LEFT JOIN counting_point_arcs ON reference_trip_set.CountingPointID = counting_point_arcs.CountingPointID
        WHERE ReferenceSetID = {0}
        AND TripID = {1}
        ORDER BY DateTime
        """.format(self.ReferenceTripSetID, routeID)
        referencestrips = self.sql(sql)
        referencestrips = referencestrips.join(
            self.arcs, on='ArcID', rsuffix='_r')
        referencestrips = geopandas.GeoDataFrame(referencestrips)

        # Validate points passed
        if validateroute is not None:
            if isinstance(validateroute, str) and validateroute == 'route':
                validateroute = self.route_arcs(routeID)

            referencestrips['PointPassed'] = np.in1d(
                referencestrips['ArcID'], validateroute['ArcID'])
        referencestrips['geometry'] = referencestrips['geometry'].representative_point()
        return referencestrips

    def infeasibletrips_timeseries(self):
        """Infeasible Trips in scenario per date"""
        sql = """
        SELECT DATE(trips_{0}.DateTime) AS date,
               count(*) AS nTrips,
               SUM(trips_{0}.TotalWeight__t) AS SumTotalWeight__t
        FROM infeasible_trips_{0} AS infeasible_trips
        LEFT JOIN trips_{0} ON infeasible_trips.TripID = trips_{0}.ID
        GROUP BY DATE(DateTime)
        """.format(self.scenarioID)
        df = self.sql(sql)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        return df

    def infeasibletrips_tripdetails(self):
        sql = """
        SELECT nstr_mapping.GroupCode AS "NSTR",
               appearance_types.Description AS "Vorm",
               DATE(trips.DateTime) AS "Days",
               trips.ID AS "ID",
               (trips.NumberOfTrips) AS "Aantal Vaarbewegingen (-)",
               (trips.TotalWeight__t * trips.NumberOfTrips) AS "Totale Vracht (ton)",
               (trips.TwentyFeetEquivalentUnits) AS "Totale TEU (-)"
        FROM infeasible_trips_{0} AS infeasible_trips
        LEFT JOIN trips_{0} AS trips ON infeasible_trips.TripID = trips.ID
        LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode
        LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID
        """.format(self.scenarioID)

        df = self.sql(sql)
        df['Days'] = pd.to_datetime(df['Days'])
        df = df.replace({'NSTR': self.NSTR_shortnames})
        df = df.set_index('ID')
        return df

    def waterscenario_countarcs(self):
        """Count number of Arcs in each water scenario"""

        sql = """
        SELECT ID,Description,COUNT(*) AS nArcs
        FROM water_scenario_values
        LEFT JOIN water_scenarios ON water_scenario_values.WaterScenarioID = water_scenarios.ID
        WHERE SeasonID=1
        GROUP BY ID
        """
        return self.sql(sql)

    def waterscenario_arcs_waterdepth(self, ArcIDs):
        """
        For a list of ArcIDs get the waterdepth
        """

        ArcIDsStr = str(ArcIDs).strip('[]')
        sql = f"""
        SELECT SeasonID, WaterDepth__m, ArcID
        FROM water_scenario_values
        WHERE ArcID IN ({ArcIDsStr}) AND WaterScenarioID={self.WaterScenarioID}
        """
        df = self.sql(sql)
        df = df.set_index('SeasonID')

        gp = df.groupby('ArcID')
        ndf = pd.DataFrame()
        for name, group in gp:
            ndf[name] = group['WaterDepth__m']
        return ndf

    def arc_tripdetails(self, arcID, extended=True, group_by=None):
        """
        This function requests all vessels passing a specified arc with
        various information about those vessels

        NOTE: Not all columns give proper info when using groupby

        TODO: Add functionality to add multiple arcID and to include an exclude_ardID like with route_stats
        """
        if not group_by:
            group_by = 'trips.ID'

        if extended:
            sql = f"""
            SELECT trips.*,
                   routes.OriginalArcDirection,
                   route_statistics.*,
                   ship_types.Label AS ship_types_Label,
                   ship_types.Description AS ship_types_Description,
                   cemt_class.ID AS cemt_class_ID,
                   cemt_class.Description AS cemt_class_Description,
                   nstr_mapping.GroupCode AS NSTR,
                   nstr_mapping.Description AS nstr_Description,
                   appearance_types.Description AS appearance_types_Description,
                   dangerous_goods_levels.Description AS dangerous_goods_levels_Description,
                   {self.compute_route_statistics}
            FROM routes_{self.scenarioID} AS routes
            LEFT JOIN trips_{self.scenarioID} AS trips ON routes.TripID = trips.ID
            LEFT JOIN ship_types ON trips.ShipTypeID = ship_types.ID
            LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode
            LEFT JOIN cemt_class ON ship_types.CEMTTypeID = cemt_class.Id
            LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID
            LEFT JOIN dangerous_goods_levels ON trips.DangerousGoodsLevelID = dangerous_goods_levels.ID
            LEFT JOIN route_statistics_{self.scenarioID} AS route_statistics ON route_statistics.TripID = routes.TripID
            LEFT JOIN load_types ON trips.LoadTypeID = load_types.ID
            WHERE ArcID = {arcID}
            GROUP BY {group_by}
            """
        else:
            sql = f"""
            SELECT trips.*,
                   routes.OriginalArcDirection
            FROM routes_{self.scenarioID} AS routes
            LEFT JOIN trips_{self.scenarioID} AS trips ON routes.TripID = trips.ID
            WHERE ArcID = {arcID}
            """

        df = self.sql(sql)

        df = df.replace({'NSTR': self.NSTR_shortnames})
        df = df.replace({'appearance_types_Description': self.appeareance_rename})

        if group_by == 'trips.ID':
            df = df.set_index('ID')
        else:
            df = df.set_index(group_by)

        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df = df.drop(['SeasonID', 'ShipTypeID', 'DangerousGoodsLevelID', 'LoadTypeID'], axis=1)
        return df

    def arc_routestatistics(self, arcID):
        """
        Compute route statistics for a specific ArcID
        """
        sql = f"""
        SELECT trips.ID,
               (trips.NumberOfTrips) AS "Aantal Vaarbewegingen (-)",
               (trips.TotalWeight__t * trips.NumberOfTrips) AS "Totale Vracht (ton)",
               (trips.TwentyFeetEquivalentUnits * trips.NumberOfTrips) AS "Totale TEU (-)",
               {self.compute_route_statistics}
        FROM routes_{self.scenarioID} AS routes
        LEFT JOIN trips_{self.scenarioID} AS trips ON routes.TripID = trips.ID
        LEFT JOIN route_statistics_{self.scenarioID} AS route_statistics ON route_statistics.TripID = routes.TripID
        WHERE ArcID = {arcID}
        """

        df = self.sql(sql)
        df = df.set_index('ID')
        return df

    def arc_usagestatistics(self):
        sql = """
        SELECT ArcID,
        SUM(arcStats.NumberOfTrips) AS "Aantal Vaarbewegingen (-)",
        SUM(arcStats.NumberOfTrips * arcStats.AverageLoadWeight__t) AS "Totale Vracht (ton)",
        SUM(arcStats.AverageCosts__Eur / arcStats.AverageDistance__km) AS "Gemiddelde kosten/km"
        FROM arc_usage_statistics_details_{0} AS arcStats
        GROUP BY ArcID
        """.format(self.scenarioID)
        df = self.sql(sql)
        df = df.set_index('ArcID')
        return df

    def arc_routes_on_network(self, arcID, not_passing_arcID=None):
        """
        For a given arcID (or list), this function analyses how all trips passing this Arc are distributed over the network.
        By given an arcID (or list0 as not_passing_arcID it is returning all trips that do pass arcID, but not pass not_passing_arcID.

        NOTE: It can happen that multiple ArcID are given, and one should expect that all have equal (maximum) trip count.
        However, in BIVAS/IVS it can happen that a ship passes and arc multiple times. This can result in irregularities.
        """
        if not not_passing_arcID and isinstance(arcID, int):
            # All routes of ships passing 1 point
            sql = f"""
            SELECT routes.ArcID AS ArcID,
            COUNT(*) AS "Aantal"
            FROM routes_{self.scenarioID} AS routes_passing_arc
            INNER JOIN routes_{self.scenarioID} AS routes ON routes_passing_arc.TripID = routes.TripID
            WHERE routes_passing_arc.ArcID = {arcID}
            GROUP BY routes.ArcID
            """
        elif isinstance(arcID, int) and isinstance(not_passing_arcID, int):
            # All routes of ships passing 1 point and not passing another point

            sql = f"""
            SELECT routes.ArcID AS ArcID,
                COUNT(*) AS "Aantal"
            FROM routes_{self.scenarioID} AS routes_passing_arc
            LEFT JOIN
                (SELECT ArcID, TripID FROM routes_{self.scenarioID} WHERE ArcID = {not_passing_arcID})
                AS routes_passing_arc2 ON routes_passing_arc.TripID = routes_passing_arc2.TripID
            INNER JOIN routes_{self.scenarioID} AS routes ON routes_passing_arc.TripID = routes.TripID
            WHERE routes_passing_arc.ArcID = {arcID}
                AND routes_passing_arc2.ArcID IS NULL
            GROUP BY routes.ArcID"""
        else:
            # Either one of the input is a list of arcs. Lets make sure both are
            if not isinstance(arcID, list): arcID = [arcID]
            if not isinstance(not_passing_arcID, list):
                if isinstance(not_passing_arcID, int):
                    not_passing_arcID = [not_passing_arcID]
                else:
                    not_passing_arcID = []

            leftjoins = ''
            where = ''
            join_id = 1

            for a in not_passing_arcID:
                join_id += 1
                leftjoins += f"""
                    LEFT JOIN
                    (SELECT ArcID, TripID FROM routes_{self.scenarioID} WHERE ArcID = {a})
                    AS routes_passing_arc{join_id} ON routes_passing_arc.TripID = routes_passing_arc{join_id}.TripID
                """

                where += f"""
                    AND routes_passing_arc{join_id}.ArcID IS NULL
                """

            for a in arcID[1:]:
                join_id += 1
                leftjoins += f"""
                    INNER JOIN
                    (SELECT ArcID, TripID FROM routes_{self.scenarioID} WHERE ArcID = {a})
                    AS routes_passing_arc{join_id} ON routes_passing_arc.TripID = routes_passing_arc{join_id}.TripID
                """

            sql = f"""
            SELECT routes.ArcID AS ArcID,
                COUNT(*) AS "Aantal"
            FROM routes_{self.scenarioID} AS routes_passing_arc
            {leftjoins}
            INNER JOIN routes_{self.scenarioID} AS routes ON routes_passing_arc.TripID = routes.TripID
            WHERE routes_passing_arc.ArcID = {arcID[0]}
            {where}
            GROUP BY routes.ArcID"""

        df = self.sql(sql)
        df = df.set_index('ArcID')
        return df

    def arcs_timeseries(self, ArcIDs):
        """
        For a list of ArcIDs give the number of daily routes
        """

        ArcIDsStr = str(ArcIDs).strip('[]')
        sql = """
        SELECT DATE(trips_{0}.DateTime) AS date,
               COUNT(trips_{0}.NumberOfTrips ) AS SumNumberOfTrips,
               ArcID
        FROM routes_{0}
        LEFT JOIN trips_{0} ON routes_{0}.TripID = trips_{0}.ID
        WHERE ArcID IN ({1})
        GROUP BY DATE(trips_{0}.DateTime), ARCID
        """.format(self.scenarioID, ArcIDsStr)
        df = self.sql(sql)
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        gp = df.groupby('ArcID')
        ndf = pd.DataFrame()
        for name, group in gp:
            ndf[name] = group['SumNumberOfTrips']

        return ndf

    def node_statistics(self, NodeID, trafficScenarioId, groupby_field, groupby_sort, directions):
        """
        Get statistics for trips in traffic scenario at a node

        NodeID: ID of node of origin/destination
        trafficScenarioId: trafficScenarioId
        groupby_field: like 'nstr_mapping.GroupCode'
        groupby_sort: can be identical to groupby_field, or a different field in the table
        directions: can be either ['Origin', 'Destination'], ['Origin'] or ['Destination']
        """
        dfs = {}
        for d in directions:
            sql = f"""
                     SELECT
                     {groupby_field} AS groupby,
                     count(*) AS nTrips
                     FROM trips

                     LEFT JOIN ship_types ON trips.ShipTypeID = ship_types.ID
                     LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode
                     LEFT JOIN cemt_class ON ship_types.CEMTTypeID = cemt_class.Id
                     LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID
                     LEFT JOIN dangerous_goods_levels ON trips.DangerousGoodsLevelID = dangerous_goods_levels.ID
                     LEFT JOIN load_types ON trips.LoadTypeID = load_types.ID
                     WHERE TrafficScenarioID={trafficScenarioId}
                         AND {d}TripEndPointNodeID={NodeID}
                     GROUP BY {groupby_field}
                     ORDER BY {groupby_sort}
                     """
            df = self.sql(sql)

            # Format data
            df = df.set_index('groupby')
            dfs[d] = df['nTrips']

        df = pd.concat(dfs, axis=1, sort=False).sum(axis=1)

        if groupby_field == 'nstr_mapping.GroupCode':
            df.rename(self.NSTR_shortnames, inplace=True)
        return df

    def node_statistics_all(self, trafficScenarioId):
        directions = ['Origin', 'Destination']
        dfs = {}
        for d in directions:
            sql = f"""
                    SELECT {d}TripEndPointNodeID AS NodeID,
                    count(*) AS nTrips
                    FROM trips
                    WHERE TrafficScenarioID={trafficScenarioId}
                    GROUP BY {d}TripEndPointNodeID
                    """
            df = self.sql(sql)
            dfs[d] = df.set_index('NodeID')['nTrips']
        df = pd.concat(dfs, axis=1)
        return df

    def node_timeseries(self, NodeID, trafficScenarioId):

        dfs = {}
        for d in ['Origin', 'Destination']:

            sql = f"""
                    SELECT
                    DATE(trips.DateTime) AS "Days",
                    count(*) AS nTrips
                    FROM trips
                    WHERE TrafficScenarioID={trafficScenarioId}
                        AND {d}TripEndPointNodeID={NodeID}
                    GROUP BY "Days"
                    """

            df = self.sql(sql)

            # Format data
            df['Days'] = pd.to_datetime(df['Days'])
            df = df.set_index('Days')
            df = df['nTrips']
            if df.shape[0] == 0:
                continue
            fullyear = pd.date_range('01-01-{}'.format(df.index[0].year), '31-12-{}'.format(df.index[0].year))
            dfs[d] = df.reindex(fullyear, fill_value=0)

        if len(dfs):
            df = pd.concat(dfs, axis=1)
        else:
            df = None
        return df

    def node_label(self, NodeID):
        """
        Guess a label for a node, based on neighbouring arcs
        """

        sql = f"""
                SELECT
                arcs.Name
                FROM arcs
                WHERE (FromNodeID={NodeID} OR ToNodeID={NodeID})
                GROUP BY "Days"
                LIMIT 0, 1
                """
        label = self.sql(sql).iloc[0, 0]
        label = label.replace('/', '-')
        return label

    """
    Export to file
    """

    def network_arcs(self, outputfileshape=None, outputfilecsv=None):
        """Export all Arcs in BIVAS to shapefile"""

        sql = """
        SELECT arcs.*,
               arc_types.Label,
               arc_types.Description,
               cemt_class.Description,
               cemt_class.MinimumAbsoluteUkc__m,
               cemt_class.MinimumRelativeUkc__m,
               N1.XCoordinate AS X1,
               N1.YCoordinate AS Y1,
               N2.XCoordinate AS X2,
               N2.YCoordinate AS Y2
        FROM arcs
        LEFT JOIN nodes AS N1 ON FromNodeID = N1.ID
        LEFT JOIN nodes AS N2 ON ToNodeID = N2.ID
        LEFT JOIN `branching$branch_sets` AS BS ON arcs.BranchSetID = BS.Id
        LEFT JOIN arc_types ON arcs.ArcTypeID = arc_types.ID
        LEFT JOIN cemt_class ON arcs.CemtClassId = cemt_class.ID
        WHERE BS.BranchID = {0}
        ORDER BY arcs.ID
        """.format(self.scenarioID)
        arcs = self.sql(sql).set_index('ID')

        arcs['XM'] = (arcs['X1'] + arcs['X2']) / 2
        arcs['YM'] = (arcs['Y1'] + arcs['Y2']) / 2

        if outputfilecsv:
            arcs.to_csv(outputfilecsv)

        arcs['geometry'] = arcs.apply(lambda z: LineString(
            [(z.X1, z.Y1), (z.X2, z.Y2)]), axis=1)
        arcsgpd = geopandas.GeoDataFrame(arcs)

        if outputfileshape:
            arcsgpd.reset_index().to_file(outputfileshape)

        self.arcs = arcsgpd
        return self.arcs

    def network_nodes(self, outputfile=None):
        """Export all Nodes in BIVAS to shapefile"""

        sql = """
        SELECT *
        FROM nodes
        """
        nodes = self.sql(sql).set_index('ID')
        nodes['geometry'] = nodes.apply(
            lambda z: Point(z.XCoordinate, z.YCoordinate), axis=1)

        nodes = geopandas.GeoDataFrame(nodes)
        if outputfile:
            nodes.to_file(outputfile)

        self.nodes = nodes
        return self.nodes

    def zone_list(self, zone_definition='BasGoed 2018'):
        """
        Return list of all zones for given definitionID
        :return:
        """
        sql = f"""
        SELECT zones.Name
        FROM zones
        LEFT JOIN zone_definitions ON zones.ZoneDefinitionID=zone_definitions.ID
        WHERE zone_definitions.Name = "{zone_definition}"
        """
        zones = self.sql(sql)
        return zones

    def zone_timeseries(self, zone_name, trafficScenarioId, zone_definition='BasGoed 2018'):

        dfs = {}
        for d in ['Origin', 'Destination']:

            sql = f"""SELECT ID FROM zone_definitions WHERE Name = "{zone_definition}" """
            zone_definition_id = self.sql(sql).iloc[0, 0]

            sql = f"""
                    SELECT
                    DATE(trips.DateTime) AS "Days",
                    count(*) AS nTrips
                    FROM trips
                    LEFT JOIN zone_node_mapping ON trips.{d}TripEndPointNodeID = zone_node_mapping.NodeID
                    LEFT JOIN zones ON zone_node_mapping.ZoneID = zones.ID
                    LEFT JOIN zone_definitions ON zone_definitions.ID = zone_node_mapping.ZoneID
                    WHERE trips.TrafficScenarioID={trafficScenarioId}
                    AND zones.ZoneDefinitionID={zone_definition_id}
                    AND zone_node_mapping.ZoneDefinitionID={zone_definition_id}
                    AND zones.Name = "{zone_name}"
                    GROUP BY "Days"
            """
            df = self.sql(sql)

            # Format data
            df['Days'] = pd.to_datetime(df['Days'])
            df = df.set_index('Days')
            df = df['nTrips']
            if df.shape[0] == 0:
                continue
            fullyear = pd.date_range('01-01-{}'.format(df.index[0].year), '31-12-{}'.format(df.index[0].year))
            dfs[d] = df.reindex(fullyear, fill_value=0)

        if len(dfs):
            df = pd.concat(dfs, axis=1)
        else:
            df = None
        return df

    def zone_statistics(self, zone_name, zone_definition, trafficScenarioId, groupby_field, groupby_sort, directions):
        """
        Get statistics for trips in traffic scenario at a zone

        zone_name: name of zone
        zone_definition: zone_definition_name
        trafficScenarioId: trafficScenarioId
        groupby_field: like 'nstr_mapping.GroupCode'
        groupby_sort: can be identical to groupby_field, or a different field in the table
        directions: can be either ['Origin', 'Destination'], ['Origin'] or ['Destination']
        """

        sql = f"""SELECT ID FROM zone_definitions WHERE Name = "{zone_definition}" """
        zone_definition_id = self.sql(sql).iloc[0, 0]

        dfs = {}
        for d in directions:
            sql = f"""
                     SELECT
                     {groupby_field} AS groupby,
                     count(*) AS nTrips
                     FROM trips

                     LEFT JOIN ship_types ON trips.ShipTypeID = ship_types.ID
                     LEFT JOIN nstr_mapping ON trips.NstrGoodsClassification = nstr_mapping.GroupCode
                     LEFT JOIN cemt_class ON ship_types.CEMTTypeID = cemt_class.Id
                     LEFT JOIN appearance_types ON trips.AppearanceTypeID = appearance_types.ID
                     LEFT JOIN dangerous_goods_levels ON trips.DangerousGoodsLevelID = dangerous_goods_levels.ID
                     LEFT JOIN load_types ON trips.LoadTypeID = load_types.ID
                     LEFT JOIN zone_node_mapping ON trips.{d}TripEndPointNodeID = zone_node_mapping.NodeID
                     LEFT JOIN zones ON zone_node_mapping.ZoneID = zones.ID
                     LEFT JOIN zone_definitions ON zone_definitions.ID = zone_node_mapping.ZoneID
                     WHERE TrafficScenarioID={trafficScenarioId}
                     AND zones.ZoneDefinitionID={zone_definition_id}
                     AND zone_node_mapping.ZoneDefinitionID={zone_definition_id}
                     AND zones.Name = "{zone_name}"
                     GROUP BY {groupby_field}
                     ORDER BY {groupby_sort}
                     """
            df = self.sql(sql)

            # Format data
            df = df.set_index('groupby')
            dfs[d] = df['nTrips']

        df = pd.concat(dfs, axis=1, sort=False).sum(axis=1)

        if groupby_field == 'nstr_mapping.GroupCode':
            df.rename(self.NSTR_shortnames, inplace=True)
        return df

    def countingpoint_list(self):
        """
        Returns list of all counting points including coordinates
        """
        sql =   """
                SELECT
                counting_points.Name AS Name,
                counting_point_arcs.ArcID as ArcID
                FROM counting_points
                LEFT JOIN counting_point_arcs ON counting_points.ID = counting_point_arcs.CountingPointID
                WHERE counting_points.DirectionID >0
                GROUP BY counting_points.Name
                """
        countingPoints = self.sql(sql)
        arcs = self.network_arcs()
        arcs = arcs[['Name', 'XM', 'YM']]
        countingPoints = countingPoints.join(arcs, how='left', on='ArcID', rsuffix='_arcs')
        return countingPoints

    def countingpoint_timeseries(self, referenceSetId, countingPointName, trafficScenarioId, per_direction=True):
        """
        Create timeserie of all trips passing a countingpoint in the referenceset.
        Possible to differentiate per direction, or have it combined
        """
        if per_direction:
            groupby = '"Days", counting_points.DirectionID'
        else:
            groupby = '"Days"'

        sql = f"""
        SELECT
        DATE(trips.DateTime) AS "Days",
        directions.Label AS Vaarrichting,
        count(*) AS nTrips
        FROM reference_trip_set
        LEFT JOIN trips ON reference_trip_set.TripID == trips.ID
        LEFT JOIN counting_points ON reference_trip_set.CountingPointID == counting_points.ID
        LEFT JOIN directions on counting_points.DirectionID == directions.ID
        WHERE ReferenceSetID = {referenceSetId}
        AND counting_points.Name = "{countingPointName}"
        AND trips.TrafficScenarioID = {trafficScenarioId}
        GROUP BY {groupby}
        """
        df = self.sql(sql)

        df['Days'] = pd.to_datetime(df['Days'])
        df = df.set_index('Days')

        # If not returning here, it will crash
        if df.shape[0] == 0:
            return df

        if per_direction:
            df = df.pivot(columns='Vaarrichting')
            df.rename(mapper=self.directions_dutch, inplace=True)
        df = df['nTrips']
        fullyear = pd.date_range('01-01-{}'.format(df.index[0].year), '31-12-{}'.format(df.index[0].year))
        df = df.reindex(fullyear, fill_value=0)
        return df

    def countingpoint_CEMT_klasse(self, referenceSetId, countingPointName, trafficScenarioId):
        """
        Get statistics on CEMT class at a counting point
        """
        sql = """
        SELECT
        count(*) AS nTrips,
        cemt_class.Description AS CEMT_klasse
        FROM reference_trip_set
        LEFT JOIN trips ON reference_trip_set.TripID == trips.ID
        LEFT JOIN counting_points ON reference_trip_set.CountingPointID == counting_points.ID
        LEFT JOIN ship_types ON trips.ShipTypeID == ship_types.ID
        LEFT JOIN cemt_class ON ship_types.CEMTTypeID == cemt_class.ID
        WHERE ReferenceSetID = {}
        AND counting_points.Name = "{}"
        AND trips.TrafficScenarioID = {}
        GROUP BY CEMT_klasse
        ORDER BY cemt_class.ID
        """.format(referenceSetId, countingPointName, trafficScenarioId)
        df = self.sql(sql)
        df = df.set_index('CEMT_klasse')
        df = df['nTrips']
        return df

    def reference_bivas_comparison(self, countingPointName):
        """
        Get statistics for countingpoint
        """
        sql = f"""
        SELECT
        cemt_class.Description,
        SUM(ReferenceTripCount) AS ReferenceTripCount,
        SUM(BivasRouteCount) AS BivasRouteCount,
        SUM(ReferenceBivasRouteCount) AS ReferenceBivasRouteCount,
        SUM(ReferenceNotBivasRouteCount) AS ReferenceNotBivasRouteCount,
        SUM(NotReferenceBivasRouteCount) AS NotReferenceBivasRouteCount,
        SUM(ReferenceInfeasibleCount) AS ReferenceInfeasibleCount
        FROM reference_comparison_51 AS reference_comparison
        LEFT JOIN counting_points ON reference_comparison.CountingPointID == counting_points.ID
        LEFT JOIN ship_types ON reference_comparison.ShipTypeID = ship_types.ID
        LEFT JOIN cemt_class ON ship_types.CEMTTypeID = cemt_class.Id
        WHERE counting_points.Name = {countingPointName}
        GROUP BY cemt_class.Id
        ORDER BY cemt_class.Id
        """
        df = self.sql(sql)
        return df

    """
    Compare two scenarios
    """

    def sqlCompareScenariosRoutes(self, casescenario):
        """Compare traveltimes of scenarios"""

        sql = """
        SELECT (route_statistics_{0}.TravelTime__min - route_statistics_{1}.TravelTime__min) AS ChangeInTravelTime,
                trips_{0}.NstrGoodsClassification AS NstrTypeCode,
                trips_{0}.TotalWeight__t * trips_{0}.NumberOfTrips AS TotalWeight__t,
                trips_{0}.NumberOfTrips AS nTrips
        FROM route_statistics_{0}
        LEFT JOIN route_statistics_{1} ON route_statistics_{0}.TripID = route_statistics_{1}.TripID
        LEFT JOIN trips_{0} ON route_statistics_{0}.TripID = trips_{0}.ID
        """.format(casescenario, self.scenarioID)
        df = self.sql(sql)
        return df

    def sqlCompareScenariosTrips(self, casescenario):
        """Compare increase in trips of routes in casescenario"""

        sql = """
        SELECT trips_{0}.NumberOfTrips - trips_{1}.NumberOfTrips AS ExtraTrips
        FROM trips_{0}
        RIGHT JOIN route_statistics_{0} ON route_statistics_{0}.TripID = trips_{0}.ID
        LEFT JOIN trips_{1} ON trips_{0}.ID = trips_{1}.ID
        """.format(casescenario, self.scenarioID)
        df = self.sql(sql)
        return df

    def sql(self, sql):
        """ Execute sql on loaded database"""
        logger.debug(f'Executing sql syntax: {sql}')
        return pd.read_sql(sql, self.connection)

    def sql_tableexists(self, table):
        """ Check if table exists in database"""
        sql = f"""SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table}'"""
        df = self.sql(sql)
        return df.iloc[0, 0] > 0

    # Functions without SQL
    def remove_small_ships(self, df, CEMTTypeIDmax=3):
        """
        In the given dataframe, for all ship_types with CEMT lower or equal to CEMTTypeIDmax,
        change the ship type to 'M{cemt}' to reduce the number of classes

        returns:
            ordered_ship_types: the short list of ship types in sorted order
            data_merge_small_ships: dataframe with field 'ship_type_label' updated
        """
        ship_types = self.shiptypes()

        small_ships = ship_types[ship_types['CEMTTypeID'] <= CEMTTypeIDmax]
        replace_label = {}
        # replace_description = {}
        for k, v in small_ships.iterrows():
            # Skip rows which are already M{cent} type
            if not v['Label'] == f'M{v["CEMTTypeID"] - 1}':
                replace_label[v['Label']] = f'M{v["CEMTTypeID"] - 1}'

        ordered_ship_types = ship_types['Label'].replace(replace_label).drop_duplicates()

        data_merge_small_ships = df.copy()
        data_merge_small_ships = data_merge_small_ships.replace({'ship_types_Label': replace_label})
        return ordered_ship_types, data_merge_small_ships

    @staticmethod
    def not_empty(df):
        """
        Returns all ships which are not empty based on the columns AppearanceTypeID and TotalWeight__t
        # TODO: could have used loadTypeID instead...
        """
        df_notempty = df[(df['AppearanceTypeID'] > 0) & (df['TotalWeight__t'] > 0)]
        return df_notempty

    """
    Network function
    """

    def networkx_generate(self):
        """Create Networkx from arcs and nodes"""

        arcs = self.network_arcs().reset_index()
        nodes = self.network_nodes()

        arcs = arcs[['ID', 'FromNodeID', 'ToNodeID', 'Name', 'Length__m']]

        G = nx.from_pandas_edgelist(
            arcs, 'FromNodeID', 'ToNodeID', edge_attr=True)
        for nodeID, nodeValues in nodes.iterrows():
            if nodeID in G.node:
                G.node[nodeID]['X'] = nodeValues['XCoordinate']
                G.node[nodeID]['Y'] = nodeValues['YCoordinate']
            else:
                pass
                print('Node {} is not connected to any edge'.format(nodeID))
        self.NetworkX = G
        return self.NetworkX

    def networkx_findpath(self, nodeidstart, nodeidend):
        """Find the path between two nodes
        Returns list of nodes and edges
        """
        if not hasattr(self, 'NetworkX'):
            self.networkx_generate()

        pathnodes = nx.dijkstra_path(
            self.NetworkX, nodeidstart, nodeidend, weight='Length__m')
        pathedges = []
        for i in range(len(pathnodes) - 1):
            pathedges.append(
                self.NetworkX[pathnodes[i]][pathnodes[i + 1]]['ID'])
        return pathnodes, pathedges

    def networkx_findpath_multiple(self, pathnodes):
        """
        for each set of nodes, find the path between the nodes

        pathnodes={
        'Waal_Upstream':(6855,6799),
        'Waal_Downstream':(6799,7073)}
        """

        if not hasattr(self, 'NetworkX'):
            self.networkx_generate()

        pathedges = {}
        for name, nodes in pathnodes.items():
            _, pathedges[name] = self.networkx_findpath(nodes[0], nodes[1])
        return pathedges
