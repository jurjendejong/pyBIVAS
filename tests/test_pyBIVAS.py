#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `klimaatbestendige_netwerken` package."""


import unittest
from pathlib import Path
from klimaatbestendige_netwerken.pyBIVAS import pyBIVAS
import urllib
import shutil


class test_pyBIVAS(unittest.TestCase):
    """Tests for `klimaatbestendige_netwerken` package."""

    skipSlowRuns=True

    database_file = Path('bivas_LSM_2018_NWMinput_lsm2bivas_v2018_02.db')
    database_url = 'ftp://kbn:geieA8=@ftp.deltares.nl/test/bivas_LSM_2018_NWMinput_lsm2bivas_v2018_02.db'

    arcID = 6332
    arcIDs = [6332, 9204, 8886]
    routeID = 634
    routeIDs = [634, 720]

    # Route from Nijmegen to the Lek
    startNode = 6852
    endNode = 6248

    def setUp(self):
        """Set up test fixtures, if any."""

        # Download external file if missing
        if not self.database_file.exists():
            with urllib.request.urlopen(self.database_url) as fin:
                with open(self.database_file, 'wb') as fout:
                    shutil.copyfileobj(fin, fout)\
        # Connect to database
        self.BIVAS = pyBIVAS(self.database_file)
        self.BIVAS.set_scenario(47)

    def test_overviewScenarios(self):
        df = self.BIVAS.sqlOverviewOfScenarios()
        print(df)

    def test_sqlCountTripsInTrafficScenario(self):
        df = self.BIVAS.sqlCountTripsInTrafficScenario()
        print(df)

    def test_sqlCountTrips(self):
        df = self.BIVAS.sqlCountTrips()
        print(df)

    def test_sqlRouteStatistics(self):
        df = self.BIVAS.sqlRouteStatistics()  # Results (costs, time, distance) per day
        print(df)

    def test_sqlAdvancedRoutes(self):
        # Data results grouped by year (should be identical to self.BIVAS.sqlRouteStatistics() )
        df = self.BIVAS.sqlAdvancedRoutes()

    def test_sqlAdvancedRoutes_2(self):
        # Group by combination of Vorm (bulk/container/overig) and NSTR-class (this is the default DPZW output)
        df = self.BIVAS.sqlAdvancedRoutes(group_by=['Vorm', 'NSTR'])

    def test_sqlAdvancedRoutes_3(self):
        # Previous results, now output per day instead of per year
        df = self.BIVAS.sqlAdvancedRoutes(group_by=['Days', 'Vorm', 'NSTR'])

    def test_sqlTripDetailsExpanded(self):
        df = self.BIVAS.sqlTripDetailsExpanded()

    def test_arcUsage(self):
        df = self.BIVAS.arcUsage()  # Statistics (number of trips, total weight, average cost/km) based on ArcStatistics tabel

    def test_sqlArcRouteStatistics(self):
        df = self.BIVAS.sqlArcRouteStatistics(self.arcID)  # More statistics based on routes table

    def test_sqlArcDetails(self):
        if self.skipSlowRuns:
            return
        df = self.BIVAS.sqlArcDetails(self.arcID)  # list of trips (with details) on given arc

    def test_sqlRouteStats(self):
        self.BIVAS.sqlRouteStats(self.routeID)  # Stats based on table route_statistics

    def test_sqlRoute(self):
        self.BIVAS.sqlArcs()  # Required to have the arcs available
        df = self.BIVAS.sqlRoute(self.routeID)  # Get all arcs that have been passed by route

    def test_sqlRouteStatisticsForListTrips(self):
        df = self.BIVAS.sqlRouteStatisticsForListTrips(self.routeIDs)  # Statistics based on trips

    def test_sqlReferenceRoute(self):
        self.BIVAS.sqlArcs()
        route = self.BIVAS.sqlRoute(self.routeID)
        df = self.BIVAS.sqlReferenceRoute(self.routeID, route, ReferenceSetID=3)

    def test_sqlWaterDepthForArcIDs(self):
        df = self.BIVAS.sqlWaterDepthForArcIDs(self.arcIDs)

    def test_sqlInfeasibleTrips(self):
        df = self.BIVAS.sqlInfeasibleTrips()  # Number of infeasible trips per day

    def test_loadAllInfeasible(self):
        df = self.BIVAS.loadAllInfeasible()  # Get details on all infeasible trips

    def test_export_BIVAS_arcs(self):
        arcs = self.BIVAS.sqlArcs(outputfileshape='arcs.shp', outputfilecsv='arcs.csv')

    def test_findPathInNetworkx(self):
        networkx = self.BIVAS.sqlNetworkToNetworkx()

        list_of_arcs = self.BIVAS.findPathInNetworkx(self.startNode, self.endNode)

    def test_manualSql(self):
        sql = """SELECT * FROM ship_types"""
        ship_types = self.BIVAS.sql(sql)

        sql = """SELECT * FROM cemt_class"""
        cemt_class = self.BIVAS.sql(sql).set_index('Id')

        ship_types = ship_types.join(cemt_class, on='CEMTTypeID', rsuffix='_CEMT').set_index('Label')

if __name__ == '__main__':
    unittest.main()
