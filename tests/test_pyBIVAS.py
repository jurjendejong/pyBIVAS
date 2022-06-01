#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `klimaatbestendige_netwerken` package."""

import unittest
from pathlib import Path
from pyBIVAS.SQL import pyBIVAS


class test_pyBIVAS(unittest.TestCase):
    """Tests for `klimaatbestendige_netwerken` package."""

    skipSlowRuns = False

    database_file = Path(r'resources/Bivas_2018_v2.db')

    arcID = 6332
    arcIDs = [6332, 9204, 8886]
    routeID = 634
    routeIDs = [634, 720]

    # Route from Nijmegen to the Lek
    startNode = 6852
    endNode = 6248

    exportdir = Path('export_pyBIVAS')

    def setUp(self):
        # Test if database exists
        if not self.database_file.exists():
            self.skipTest('Database could not be found')

        # Connect to database
        self.BIVAS = pyBIVAS(self.database_file)
        self.BIVAS.set_scenario()

        if not self.exportdir.exists():
            self.exportdir.mkdir()

    def test_overviewScenarios(self):
        df = self.BIVAS.scenario_parameters()
        print(df.to_string())

    def test_sqlCountTripsInTrafficScenario(self):
        df = self.BIVAS.trafficscenario_timeseries()
        print(df.head(10).to_string())

    def test_sqlCountTrips(self):
        df = self.BIVAS.trips_timeseries()
        print(df.head(10).to_string())

    def test_sqlRouteStatistics(self):
        df = self.BIVAS.routestatistics_timeseries()  # Results (costs, time, distance) per day
        print(df.head(10).to_string())

    def test_sqlAdvancedRoutes(self):
        # Data results grouped by year (should be identical to self.BIVAS.sqlRouteStatistics() )
        df = self.BIVAS.routestatistics_advanced()
        print(df.head(10).to_string())

    def test_sqlAdvancedRoutes_2(self):
        # Group by combination of Vorm (bulk/container/overig) and NSTR-class (this is the default DPZW output)
        df = self.BIVAS.routestatistics_advanced(group_by=['Vorm', 'NSTR'])
        print(df.head(10).to_string())

    def test_sqlAdvancedRoutes_3(self):
        # Previous results, now output per day instead of per year
        df = self.BIVAS.routestatistics_advanced(group_by=['Days', 'Vorm', 'NSTR'])
        print(df.head(10).to_string())

    def test_sqlTripDetailsExpanded(self):
        df = self.BIVAS.trips_details()
        print(df.head(10).to_string())

    def test_arcUsage(self):
        df = self.BIVAS.arc_usagestatistics()  # Statistics (number of trips, total weight, average cost/km)
        print(df.head(10).to_string())

    def test_sqlArcRouteStatistics(self):
        df = self.BIVAS.arc_routestatistics(self.arcID)  # More statistics based on routes table
        print(df.head(10).to_string())

    def test_sqlArcDetails(self):
        if self.skipSlowRuns:
            self.skipTest('Skipping because this test takes very long')
        df = self.BIVAS.arc_tripdetails(self.arcID)  # list of trips (with details) on given arc
        print(df.head(10).to_string())

    def test_sqlArcDetails2(self):
        df = self.BIVAS.arc_tripdetails(self.arcID, extended=False)  # list of trips (without details) on given arc
        print(df.head(10).to_string())

    def test_sqlRouteStats(self):
        df = self.BIVAS.route_stats(self.routeID)  # Stats based on table route_statistics
        print(df.head(10).to_string())

    def test_sqlRoute(self):
        self.BIVAS.network_arcs()  # Required to have the arcs available
        df = self.BIVAS.route_arcs(self.routeID)  # Get all arcs that have been passed by route
        print(df.head(10).to_string())

    def test_sqlRouteStatisticsForListTrips(self):
        df = self.BIVAS.trips_statistics(self.routeIDs)  # Statistics based on trips
        print(df.head(10).to_string())

    def test_sqlReferenceRoute(self):
        self.BIVAS.network_arcs()
        route = self.BIVAS.route_arcs(self.routeID)
        df = self.BIVAS.route_countingpoints(self.routeID, route)
        print(df.head(10).to_string())

    def test_sqlWaterDepthForArcIDs(self):
        df = self.BIVAS.waterscenario_arcs_waterdepth(self.arcIDs)
        print(df.head(10).to_string())

    def test_sqlInfeasibleTrips(self):
        df = self.BIVAS.infeasibletrips_timeseries()  # Number of infeasible trips per day
        print(df.head(10).to_string())

    def test_loadAllInfeasible(self):
        df = self.BIVAS.infeasibletrips_tripdetails()  # Get details on all infeasible trips
        print(df.head(10).to_string())

    def test_export_BIVAS_arcs(self):
        arcs = self.BIVAS.network_arcs(outputfileshape=self.exportdir / 'arcs.shp',
                                       outputfilecsv=self.exportdir / 'arcs.csv')
        print(arcs.head(10).to_string())

    def test_findPathInNetworkx(self):
        networkx = self.BIVAS.networkx_generate()
        list_of_arcs = self.BIVAS.networkx_findpath(self.startNode, self.endNode)
        print(list_of_arcs)

    def test_manualSql(self):
        sql = """SELECT * FROM ship_types"""
        ship_types = self.BIVAS.sql(sql)

        sql = """SELECT * FROM cemt_class"""
        cemt_class = self.BIVAS.sql(sql).set_index('Id')

        ship_types = ship_types.join(cemt_class, on='CEMTTypeID', rsuffix='_CEMT').set_index('Label')
        print(ship_types.head(10).to_string())

    def test_routesFromArc(self):
        df = self.BIVAS.arc_routes_on_network(self.arcID)
        print(df.head(10).to_string())

    def test_routesFromArc2(self):
        if self.skipSlowRuns:
            self.skipTest('Skipping because this test takes very long')

        df = self.BIVAS.arc_routes_on_network(self.arcIDs[:2], not_passing_arcID=self.arcIDs[-1])
        print(df.head(10).to_string())


if __name__ == '__main__':
    unittest.main()
