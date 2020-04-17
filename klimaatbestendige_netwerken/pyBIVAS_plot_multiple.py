from klimaatbestendige_netwerken.pyBIVAS_plot import pyBIVAS_plot as pyBIVAS
import pandas as pd
import geopandas
import gc
import random
import matplotlib.pyplot as plt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class pyBIVAS_plot_compare:
    BIVAS_connection = {}

    Arcs = pyBIVAS.Arcs
    outputdir = Path('.')

    def __init__(self, BIVAS_simulations: dict, scenarioID=None):
        """
        scenarioID: integer if identical for all simulations. Dictionary if different ID per simulation.
                    Leave empty for auto assign scenario.
        """
        self.BIVAS_simulations = BIVAS_simulations
        self.reference = list(BIVAS_simulations.keys())[0]
        self.scenarioID = scenarioID

    def connect_all(self):
        for name, path in self.BIVAS_simulations.items():
            BIVAS = pyBIVAS()
            BIVAS.connectToSQLiteDatabase(path)

            # Connect to scenario
            if self.scenarioID:
                if isinstance(self.scenarioID, int):
                    BIVAS.set_scenario(self.scenarioID)
                else:
                    BIVAS.set_scenario(self.scenarioID[name])
            else:
                BIVAS.set_scenario()

            self.BIVAS_connection[name] = BIVAS

    def plot_tijdseries(self, label, arcID, includeDischarge=False):

        tripsPerDay = {}
        for name, BIVAS in self.BIVAS_connection.items():
            d = BIVAS.sqlArcDetails(arcID)
            tripsPerDay[name] = d['NumberOfTrips'].groupby(d['DateTime']).sum()

        tripsPerDay = pd.concat(tripsPerDay, axis=1)

        if includeDischarge:
            def getDischargeLobith(BIVAS):
                arcID_Bovenrijn = self.Arcs['BovenRijn']
                sql = f"""
                    SELECT SeasonID, WaterDepth__m, RateOfFlow__m3_s, WaterLevel__m
                    FROM water_scenario_values
                    WHERE ArcID IN ({arcID_Bovenrijn}) AND WaterScenarioID={BIVAS.WaterScenarioID}
                    """
                df = BIVAS.sql(sql)
                df = df.set_index('SeasonID')
                return df['RateOfFlow__m3_s']

            Q = {}
            for name, BIVAS in self.BIVAS_connection.items():
                Q[name] = getDischargeLobith(BIVAS)
            Q = pd.concat(Q, axis=1)
            Q = Q.iloc[:tripsPerDay.shape[0]]
            Q.index = tripsPerDay.index

        year = tripsPerDay.index[0].year

        f, ax = plt.subplots(nrows=2, figsize=(16, 8), sharey=True)

        # First plot
        tripsPerDay[:f'30-june-{year}'].plot(drawstyle='steps', legend=False, ax=ax[0])
        ax[0].set_ylabel('Aantal schepen')
        ax[0].set_xlabel('')
        if includeDischarge:
            Q[:f'30-june-{year}'].plot(ax=ax[0], legend=False, linestyle='-.', secondary_y=True)
            plt.ylabel('Afvoer Lobith (m3/s)')
            plt.xlabel('')
        ax[0].grid()
        ax[0].set_ylim(bottom=0)
        ax[0].legend(loc='center left', bbox_to_anchor=(1.07, 0.5), facecolor='w', title='', )

        ax[0].set_title('Passerende schepen bij Lobith')

        # Second plot
        tripsPerDay[f'01-july-{year}':].plot(drawstyle='steps', legend=False, ax=ax[1])
        ax[1].set_ylabel('Aantal schepen')
        ax[1].set_xlabel('')
        if includeDischarge:
            Q[f'01-july-{year}':].plot(ax=ax[1], secondary_y=True, legend=False, linestyle='-.', )
            plt.ylabel('Afvoer Lobith (m3/s)')
            plt.xlabel('')
        ax[1].grid()
        ax[1].set_ylim(bottom=0)
        ax[1].legend(loc='center left', bbox_to_anchor=(1.07, 0.5), facecolor='w', title='', )
        plt.savefig(self.outputdir / f'Tijdserie_{label}', dpi=300, bbox_inches='tight')

    def plot_routes(self, routes, limit=100, shuffle=True):
        """"
        Compare first and second simulation for routes.
        Possible options for routes:
            'largestIncrease'  -- Get the trips with the largest increase in costs
            'largestIncreaseDate' -- Get trips on the date with the largest increase in costs
            'database' -- Use database sort
            'larger' -- Get the largest routes
            arcID
            [list_of_arcID]

        TODO: include option to only show one simulation, or more than 2
        """

        for name, BIVAS in self.BIVAS_connection.items():
            BIVAS.sqlArcs()
            BIVAS.sqlNodes()

        BIVAS = self.BIVAS_connection[self.reference]

        def getStartEnd(route):
            if route.iloc[0]['OriginalArcDirection']:
                startpoint = route.iloc[:1].join(BIVAS.nodes, on='FromNodeID', lsuffix='_l')
            else:
                startpoint = route.iloc[:1].join(BIVAS.nodes, on='ToNodeID', lsuffix='_l')

            if route.iloc[-1]['OriginalArcDirection']:
                endpoint = route.iloc[-1:].join(BIVAS.nodes, on='ToNodeID', lsuffix='_l')
            else:
                endpoint = route.iloc[-1:].join(BIVAS.nodes, on='FromNodeID', lsuffix='_l')
            return startpoint, endpoint

        if routes == 'larger':
            # Get all larger trips
            sql = """
            SELECT TripID
            FROM route_statistics_{0}
            LEFT JOIN trips_{0} ON route_statistics_{0}.TripID = trips_{0}.ID
            WHERE route_statistics_{0}.VariableDistanceCosts__EUR > 10000
            """.format(self.BIVAS_connection[self.reference].scenarioID)
            all_routes = self.BIVAS_connection[self.reference].sql(sql)
            all_routes = all_routes['TripID'].values
        elif routes == 'database':
            # Get all trips in database order
            sql = f"""
            SELECT TripID
            FROM route_statistics_{self.BIVAS_connection[self.reference].scenarioID}
            """
            all_routes = self.BIVAS_connection[self.reference].sql(sql)
            all_routes = all_routes['TripID'].values
        elif routes == 'largestIncreaseDate':
            # Get all big trips on most changing day
            routeStats = {}
            for name, BIVAS in self.BIVAS_connection.items():
                routeStats[name] = BIVAS.sqlRouteStatistics()["Totale Vaarkosten (EUR)"]
            routeStats = pd.concat(routeStats, axis=1)
            routeStatsDiff = routeStats.diff(axis=1).iloc[:, -1].abs()

            datemax = routeStatsDiff.idxmax()

            sql = """
            SELECT TripID
            FROM route_statistics_{0}
            LEFT JOIN trips_{0} ON route_statistics_{0}.TripID = trips_{0}.ID
            WHERE DATE(trips_{0}.DateTime) = "{1}"
            AND route_statistics_{0}.VariableTimeCosts__EUR > 3000
            """.format(self.BIVAS_connection[self.reference].scenarioID, datemax.strftime('%Y-%m-%d'))
            all_routes = self.BIVAS_connection[self.reference].sql(sql)
            all_routes = all_routes['TripID'].values
        elif routes == 'largestIncrease':
            # Get largest changing trips
            routeStats = {}
            for name, BIVAS in self.BIVAS_connection.items():
                sql = """
                SELECT TripID, {1}
                FROM route_statistics_{0} AS route_statistics
                LEFT JOIN trips_{0} AS trips ON route_statistics.TripID = trips.ID
                GROUP BY TripID
                """.format(BIVAS.scenarioID, BIVAS.compute_route_statistics)
                routeStats[name] = BIVAS.sql(sql)[["TripID", "Totale Vaarkosten (EUR)"]].set_index('TripID')

            routeStats = pd.concat(routeStats, axis=1)
            routeStatsDiff = routeStats.diff(axis=1).iloc[:, -1].abs()
            all_routes = routeStatsDiff.sort_values(axis=0, ascending=False)
            all_routes = all_routes.index.values

        else:
            if isinstance(routes, list):
                all_routes = routes
            elif isinstance(routes, int):
                all_routes = [routes]
            else:
                logger.error('Unknown input')
                all_routes = None

        if shuffle:
            random.shuffle(all_routes)

        background_shapefile = r'c:\Projecten\KBN\klimaatbestendige_netwerken\tests\resources\backgroundmap\\nl_provincies_poly.shp'
        rivers_shapefile = r'c:\Projecten\KBN\klimaatbestendige_netwerken\tests\resources\backgroundmap\rivers_NL.shp'
        background = geopandas.read_file(background_shapefile)
        river_background = geopandas.read_file(rivers_shapefile)

        ref = self.reference
        case = list(self.BIVAS_connection.keys())[1]

        for routes in all_routes[:limit]:
            print('Plotting Route: {}'.format(routes))

            # Background map
            background.plot(figsize=(14, 14), color='#DDDDDD', edgecolor='#BBBBBB')
            ax = plt.gca()
            ax.axis('equal')
            ax.autoscale(False)
            ax.grid()
            river_background.plot(ax=ax, color='b')

            # Data from reference route
            route = self.BIVAS_connection[ref].sqlRoute(routes)
            routestats = self.BIVAS_connection[ref].sqlRouteStats(routes)
            if len(route) == 0:
                print('Skipping because route has not taken place')
                continue
            startpoint, endpoint = getStartEnd(route)
            referencestrips = self.BIVAS_connection[ref].sqlReferenceRoute(routes, route)

            # Plot reference route and data
            route.plot(color='r', ax=ax)
            startpoint.plot(ax=ax, color='k', markersize=7, label='Start')
            plt.annotate(s=startpoint['Name'].iloc[0], xy=startpoint['geometry'].iloc[0].coords[:][0])
            endpoint.plot(ax=ax, color='b', markersize=7, label='End')
            plt.annotate(s=endpoint['Name'].iloc[0], xy=endpoint['geometry'].iloc[0].coords[:][0])
            plt.text(0.05, 0.96, 'RouteID: {}'.format(routestats['TripID'][0]), ma='left', transform=ax.transAxes,
                     size='larger', va='top')

            if not case:
                shipbox = """Date: {r[DateTime]}
NSTR: [{r[NstrTypeCode]}] - {r[nstr_description]}
Vorm: {r[appear_description]}
Kegel: {r[dangerous_description]}
Scheepstype: {r[ship_label]} - {r[ship_description]}
Scheepslengte: {r[Length__m]} m
Scheepsbreedte: {r[Width__m]} m
Diepgang: {r[Depth__m]:.2f} m
TEU:  {r[TwentyFeetEquivalentUnits]:.0f}
TotalWeight: {r[TotalWeight__t]:.1f} ton

Totale reistijd: {r[TravelTime__min]:.0f} min
Totale afstand: {r[Distance__km]:.0f} km
Variabele kosten: {r[VariableCosts__Eur]:.0f} EUR
Vaste kosten: {r[FixedCosts__Eur]:.0f} EUR
Energiegebruik: {r[EnergyUse__kWh]:.0f} kWh
Number of Trips: {r[NumberOfTrips]:.1f}
Load capacity: {r[LoadCapacity__t]:.1f} ton""".format(r=routestats.iloc[0])
            else:
                # Data from case route
                route2 = self.BIVAS_connection[case].sqlRoute(routes)
                routestats2 = self.BIVAS_connection[case].sqlRouteStats(routes)

                if len(route2) == 0:
                    print('Skipping because route has not taken place')
                    continue

                route2.plot(color='purple', ax=ax)

                shipbox = """Date: {r[DateTime]}
NSTR: {r[nstr_description]}
Vorm: {r[appear_description]}
Kegel: {r[dangerous_description]}
Scheepstype: {r[ship_label]} - {r[ship_description]}
Scheepslengte: {r[Length__m]} m
Scheepsbreedte: {r[Width__m]} m
Diepgang: {r[Depth__m]:.2f} m
TEU:  {r[TwentyFeetEquivalentUnits]:.0f}
TotalWeight: {r[TotalWeight__t]:.1f} ton
Load capacity: {r[LoadCapacity__t]:.1f} ton

{s1}
Totale reistijd: {r[TravelTime__min]:.0f} min
Totale afstand: {r[Distance__km]:.0f} km
Variabele-tijd kosten: {r[VariableTimeCosts__Eur]:.0f} EUR
Variabele-afstand kosten: {r[VariableDistanceCosts__Eur]:.0f} EUR
Vaste kosten: {r[FixedCosts__Eur]:.0f} EUR
Energiegebruik: {r[EnergyUse__kWh]:.0f} kWh
Number of Trips: {r[NumberOfTrips]:.1f}

{s2}
Totale reistijd: {r2[TravelTime__min]:.0f} min
Totale afstand: {r2[Distance__km]:.0f} km
Variabele-tijd kosten: {r2[VariableTimeCosts__Eur]:.0f} EUR
Variabele-afstand kosten: {r2[VariableDistanceCosts__Eur]:.0f} EUR
Vaste kosten: {r2[FixedCosts__Eur]:.0f} EUR
Energiegebruik: {r2[EnergyUse__kWh]:.0f} kWh
Number of Trips: {r2[NumberOfTrips]:.1f}""".format(r=routestats.iloc[0], r2=routestats2.iloc[0], s1=ref,
                                                           s2=case)

            plt.text(0.05, 0.93, shipbox, ma='left', transform=ax.transAxes, va='top')
            if len(referencestrips) > 0:
                referencestrips.plot(ax=ax, marker='s', markersize=7, column='PointPassed', cmap='RdYlGn', vmax=1,
                                     vmin=0)

            plt.savefig(self.outputdir / 'route_{:06}.png'.format(routes))
            plt.clf()
            plt.close()

            del route
            gc.collect()
