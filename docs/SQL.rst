===
SQL
===

To use pyBIVAS in a project::
	
    from pyBIVAS.SQL import pyBIVAS

The scripts allow for connection to a database service (MariaDB) or a database file (SQLite). In this example we assume the latter::

    BIVAS_file = 'path/to/BIVAS.db'
    BIVAS = pyBIVAS(BIVAS_file)

Get a list of the scenario's in the model and set the one you want to analyse::

    BIVAS.scenario_parameters()
    BIVAS.set_scenario(47)


Now you can use any of the predefined queries on the database. Unless stated differently, the returned data is a Pandas DataFrame.

Basic Queries
#############

Total number of trips per day in the Traffic Scenario, and in the model results::

    df = BIVAS.sqlCountTripsInTrafficScenario()
    df = BIVAS.sqlCountTrips()

Statistics
**********

Some basis statistics::

    df = BIVAS.sqlRouteStatistics()  # Results (costs, time, distance) per day

More advanced statistics based on the route_statistics. Use a group_by syntax to request results in a certain format right away.

    - TripsID: Generate statistics for all individual trips
    - Days: Generate output on daily frequency
    - NSTR: Classification of loads
    - Vorm: Classification of appearance type
    - Origin_Node: Group by node of origin port
    - Destination_Node: Group by node of destination port
    - Origin_NUTS3: Group by NUTS3 area of origins
    - Destination_NUTS3: Group by NUTS3 area of destinations

Some examples::

    # Data results grouped by year (should be identical to BIVAS.sqlRouteStatistics() )
    df = BIVAS.sqlAdvancedRoutes()

    # Group by combination of Vorm (bulk/container/overig) and NSTR-class (this is the default DPZW output)
    df = BIVAS.sqlAdvancedRoutes(group_by=['Vorm', 'NSTR'])

    # Previous results, now output per day instead of per year
    df = BIVAS.sqlAdvancedRoutes(group_by=['Days', 'Vorm', 'NSTR'])

Return raw output of all trips with all details (heavy action!)::

    df = BIVAS.sqlTripDetailsExpanded()


Arc Details
***********

Generate output of the trips on a specific location::


    df = BIVAS.arcUsage()  # Statistics (number of trips, total weight, average cost/km) based on ArcStatistics tabel

    arcID = 6332
    df = BIVAS.sqlArcRouteStatistics(arcID)  # More statistics based on routes table

    df = BIVAS.sqlArcDetails(arcID)  # list of trips (with details) on given arc


Trip and route details
**********************

For a given tripId get information::

    routeID = 123
    BIVAS.sqlRouteStats(routeID)  # Stats based on table route_statistics

    BIVAS.arcs()  # Required to have the arcs available
    df = BIVAS.sqlRoute(routeID)  # Get all arcs that have been passed by route

    tripID = [123, 456]
    df = BIVAS.sqlRouteStatisticsForListTrips(tripID)  # Statistics based on trips


For a given routeID, the choosen route and referencesetID, validate if it passed the correct points::

    routeID = 123
    route = BIVAS.sqlRoute(routeID)
    df = BIVAS.sqlReferenceRoute(routeID, route, ReferenceSetID=3)

Water scenario
**************

Get the timeseries of the waterdepth for a list of arcs::

    arcIDs = [1,2,3,4]
    df = BIVAS.sqlWaterDepthForArcIDs(arcIDs)


Infeasible trips
****************

Get more info on the trips that have not been executed in the simulation::

    df = BIVAS.sqlInfeasibleTrips()  # Number of infeasible trips per day
    df = BIVAS.loadAllInfeasible()  # Get details on all infeasible trips





Network routines
################

Write arcs to shapefile::

    arcs = BIVAS.sqlArcs(outputfileshape='arcs.shp')

Return networkx and get shortest route based on Dijkstra algorithm::

    networkx = BIVAS.sqlNetworkToNetworkx()

    Node_start = 1
    Node_end = 2
    list_of_arcs = BIVAS.findPathInNetworkx(Node_start, Node_end)


Manual queries
##############

For more specific actions, or missing features, use the manual query mode::

    sql = """SELECT * FROM ship_types"""
    ship_types = BIVAS.sql(sql)

    sql = """SELECT * FROM cemt_class"""
    cemt_class = BIVAS.sql(sql).set_index('Id')

    ship_types = ship_types.join(cemt_class, on='CEMTTypeID', rsuffix='_CEMT').set_index('Label')

