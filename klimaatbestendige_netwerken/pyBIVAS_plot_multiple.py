from klimaatbestendige_netwerken.pyBIVAS_plot import pyBIVAS_plot as pyBIVAS
import pandas as pd
import numpy as np
import geopandas
import gc
import random
import matplotlib.pyplot as plt
from pathlib import Path

class pyBIVAS_plot_compare:

    BIVAS_connection = {}

    Arcs = pyBIVAS.Arcs
    outputdir = pyBIVAS.outputdir

    def __init__(self, BIVAS_simulations: dict, scenarioID: int):
        self.BIVAS_simulations = BIVAS_simulations
        self.scenarioID = scenarioID  # Assumed constant for all scenarios for now.
        self.reference = list(BIVAS_simulations.keys())[0]

    def connect_all(self):
        for name, path in self.BIVAS_simulations.items():
            BIVAS = pyBIVAS()
            BIVAS.connectToSQLiteDatabase(path)
            BIVAS.set_scenario(self.scenarioID)

            self.BIVAS_connection[name] = BIVAS


    def plot_tijdseries(self, location='Bovenrijn'):
        arcID = self.Arcs[location]
        Q = {}
        for name, BIVAS in self.BIVAS_connection.items():
            sql = """
            SELECT SeasonID, WaterDepth__m, RateOfFlow__m3_s, WaterLevel__m
            FROM water_scenario_values
            WHERE ArcID IN ({}) AND WaterScenarioID={}
            """.format(arcID, BIVAS.WaterScenarioID)
            df = BIVAS.sql(sql)
            df = df.set_index('SeasonID')
            Q[name] = df['RateOfFlow__m3_s']

        Q = pd.concat(Q, axis=1)

        tripsPerDay = {}
        for name, BIVAS in self.BIVAS_connection.items():

            d = BIVAS.sqlArcDetails(arcID)
            tripsPerDay[name] = d['NumberOfTrips'].groupby(d['DateTime']).sum()

        tripsPerDay = pd.concat(tripsPerDay, axis=1)

        Q = Q.iloc[:365]

        Q.index = tripsPerDay.index

        ax = tripsPerDay[:'30-june-14'].plot(figsize=(16,4), drawstyle='steps', legend=False)
        plt.ylabel('Aantal schepen')
        plt.ylim(0, 700)
        plt.xlabel('')
        Q[:'30-june-14'].plot(ax=plt.gca(), secondary_y=True, legend=False, linestyle='-.', color=plt.rcParams['axes.prop_cycle'].by_key()['color'][:4], )
        plt.grid()
        ax.legend(loc='center left', bbox_to_anchor=(1.07,0.5), facecolor='w', title='', )
        plt.ylabel('Afvoer Lobith (m3/s)')
        plt.xlabel('')
        plt.ylim(0, 7000)
        plt.title('Passerende schepen bij Lobith')
        plt.savefig(self.outputdir / 'Voorbeeldresultaten_deel1', dpi=300, bbox_inches='tight')


        ax = tripsPerDay['01-july-14':].plot(figsize=(16,4), drawstyle='steps', legend=False)
        plt.ylabel('Aantal schepen')
        plt.ylim(0, 700)
        plt.xlabel('')
        Q['01-july-14':].plot(ax=plt.gca(), secondary_y=True, legend=False, linestyle='-.', color=plt.rcParams['axes.prop_cycle'].by_key()['color'][:4], )
        plt.grid()
        ax.legend(loc='center left', bbox_to_anchor=(1.07,0.5), facecolor='w', title='', )
        plt.ylabel('Afvoer Lobith (m3/s)')
        plt.xlabel('')
        plt.ylim(0, 7000)
        plt.title('Passerende schepen bij Lobith')
        plt.savefig(self.outputdir / 'Voorbeeldresultaten_deel2', dpi=300, bbox_inches='tight')



    def plot_routes(self):
        for name, BIVAS in self.BIVAS_connection:
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

        # n = scenarios[0]['name']

        # # Get all trips in database order
        # sql = """
        # SELECT TripID
        # FROM route_statistics_{0}
        # """.format(scenarios[0]['ID'])
        # all_routes =  BIVAS[n].sql(sql)

        # # Get all big trips on most changing day
        # a = BIVAS['REF2015S1'].sqlRouteStatistics()
        # b = BIVAS['W2050S1'].sqlRouteStatistics()

        # datemax = (b - a)['SumDistance'].idxmax()
        # datemax = datetime.datetime.date(datemax)

        # sql = """
        # SELECT TripID
        # FROM route_statistics_{0}
        # LEFT JOIN trips_{0} ON route_statistics_{0}.TripID = trips_{0}.ID
        # WHERE DATE(trips_{0}.DateTime) = "{1}"
        # AND route_statistics_{0}.VariableCosts__EUR > 30000
        # """.format(scenarios[0]['ID'], datemax)
        # all_routes =  BIVAS[n].sql(sql)

        # Get all larger trips

        sql = """
        SELECT TripID
        FROM route_statistics_{0}
        LEFT JOIN trips_{0} ON route_statistics_{0}.TripID = trips_{0}.ID
        WHERE route_statistics_{0}.VariableCosts__EUR > 10000
        """.format(self.scenarioID)
        all_routes =  self.BIVAS_connection[self.reference].sql(sql)


        random.shuffle(all_routes['TripID'].values)

        background_shapefile = r'backgroundmap\nl_provincies_poly.shp'
        rivers_shapefile = r'backgroundmap\rivers_NL.shp'
        # background_shapefile = r'n:\Projects\11200500\11200588\B. Measurements and calculations\013_pilotBIVAS\6_Uitvoer_voor_Ecorys\NUTS_2013_01M_SH\data\NUTS_RG_01M_2013_RD_stat3.shp'
        background = geopandas.read_file(background_shapefile)
        river_background = geopandas.read_file(rivers_shapefile)


        # # Testfunction
        # routeID = 127813

        # route = BIVAS.sqlRoute(routeID)
        # routestats = BIVAS.sqlRouteStats(routeID)
        # startpoint, endpoint = getStartEnd(route)
        # referencestrips = BIVAS.sqlReferenceRoute(routeID, route)

        ref = self.reference
        case = list(self.BIVAS_connection.keys())[1]
        for routeID in all_routes['TripID']:
            print('Plotting Route: {}'.format(routeID))

            # Background map
            background.plot(figsize=(14 ,14), color='#DDDDDD', edgecolor='#BBBBBB')
            ax = plt.gca()
            ax.axis('equal')
            ax.autoscale(False)
            ax.grid()
            river_background.plot(ax=ax, color='b')

            # Data from reference route
            route = self.BIVAS_connection[ref].sqlRoute(routeID)
            routestats = self.BIVAS_connection[ref].sqlRouteStats(routeID)
            if len(route)== 0:
                print('Skipping because route has not taken place')
                continue
            startpoint, endpoint = getStartEnd(route)
            referencestrips = self.BIVAS_connection[ref].sqlReferenceRoute(routeID, route)

            # Plot reference route and data
            route.plot(color='r', ax = ax)
            startpoint.plot(ax=ax, color='k', markersize=7, label='Start')
            plt.annotate(s=startpoint['Name'].iloc[0] ,xy=startpoint['geometry'].iloc[0].coords[:][0])
            endpoint.plot(ax=ax, color='b',  markersize = 7, label='End')
            plt.annotate(s=endpoint['Name'].iloc[0] ,xy=endpoint['geometry'].iloc[0].coords[:][0])
            plt.text(0.05 ,0.96 ,'RouteID: {}'.format(routestats['TripID'][0]), ma='left', transform=ax.transAxes, size='larger', va='top')

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
                route2 = self.BIVAS_connection[case].sqlRoute(routeID)
                routestats2 = self.BIVAS_connection[case].sqlRouteStats(routeID)

                if len(route2) ==0:
                    print('Skipping because route has not taken place')
                    continue

                route2.plot(color='purple', ax = ax)

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
        Variabele kosten: {r[VariableCosts__Eur]:.0f} EUR
        Vaste kosten: {r[FixedCosts__Eur]:.0f} EUR
        Energiegebruik: {r[EnergyUse__kWh]:.0f} kWh
        Number of Trips: {r[NumberOfTrips]:.1f}

        {s2}
        Totale reistijd: {r2[TravelTime__min]:.0f} min
        Totale afstand: {r2[Distance__km]:.0f} km
        Variabele kosten: {r2[VariableCosts__Eur]:.0f} EUR
        Vaste kosten: {r2[FixedCosts__Eur]:.0f} EUR
        Energiegebruik: {r2[EnergyUse__kWh]:.0f} kWh
        Number of Trips: {r2[NumberOfTrips]:.1f}""".format(r=routestats.iloc[0], r2=routestats2.iloc[0], s1=ref, s2=case)

            plt.text(0.05 ,0.93 ,shipbox, ma='left', transform=ax.transAxes, va='top')
            if len(referencestrips) > 0:
                referencestrips.plot(ax=ax, marker='s', markersize=7, column='PointPassed', cmap='RdYlGn', vmax=1, vmin=0)
            #     plt.legend()
            plt.savefig(self.outputdir / 'route_{:06}.png'.format(routeID))
            plt.clf()
            plt.close()

            del route
            gc.collect()
