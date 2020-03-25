"""
This function contains generic plotting functions to go with the module pyBIVAS
"""

from klimaatbestendige_netwerken.pyBIVAS import pyBIVAS

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from pathlib import Path
import pandas as pd
import numpy as np
import gc
import random
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

try:
    import geopandas
except:
    logger.warning('Loading of geopandas/shapely failed. Geometric functions will not work')


class pyBIVAS_plot(pyBIVAS):
    """
    Append the class pyBIVAS with plotting functions
    """

    outputdir = Path('.')

    # Arcs in BIVAS 4.4
    Arcs = {
        'BovenRijn': 9204,
        'Waal': 6332,
        'Pannerdensch Kanaal': 8886,
        'Nederrijn': 6645,
        'IJssel': 6510,
        'Zuid-Willemsvaart': 9130,
        'Zandmaas': 7523,
        'Julianakanaal': 8710,
        'Schelde-Rijnkanaal': 8387,
        'Betuwepand (ARK)': 6853,
        'Amsterdam-Rijnkanaal': 6472,
        'Delftse Schie': 6572,
        'Oude Maas': 7121,
        'Nieuwe Maas': 6746,
        'Maasmond': 6452,
        'Maas-Waalkanaal': 7260,
        'Westerschelde': 8516,
        'Lemmer-Delfzijl': 2099,
        'Kanaal Zuid-Beveland': 8361
    }

    def plot_Trips_Arc_all(self):
        for label, arcID in self.Arcs.items():
            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='nstr_Short')
            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vracht (ton)', stacking='nstr_Short')
            self.plot_Trips_Arc(arcID, label, y_unit='Aantal Vaarbewegingen (-)', stacking='nstr_Short')

            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='appearance_types_Description')
            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vracht (ton)', stacking='appearance_types_Description')
            self.plot_Trips_Arc(arcID, label, y_unit='Aantal Vaarbewegingen (-)',
                                stacking='appearance_types_Description')

            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='cemt_class_Description')
            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vracht (ton)', stacking='cemt_class_Description')
            self.plot_Trips_Arc(arcID, label, y_unit='Aantal Vaarbewegingen (-)', stacking='cemt_class_Description')

            # Individuele klassen niet te onderscheiden, dus deze figuren voegen niets toe
            # self.plot_Trips_Arc(arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='ship_types_Label')
            # self.plot_Trips_Arc(arcID, label, y_unit='Totale Vracht (ton)', stacking='ship_types_Label')
            # self.plot_Trips_Arc(arcID, label, y_unit='Aantal Vaarbewegingen (-)', stacking='ship_types_Label')

    def plot_Trips_Arc(self, arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='NstrTypeCode'):
        """
        This function creates multiple barplots of trips passing a given arc as as function on the draft

        :return:
        """
        figdir = self.outputdir / 'figures_Histogram_Diepgang'
        if not figdir.exists():
            figdir.mkdir()

        trips_on_arc = self.sqlArcDetails(arcID)

        # Create pivot table
        bins = np.arange(0, 5, 0.5)
        c = pd.cut(trips_on_arc['Depth__m'], bins)
        trips_on_arc['depth_bin'] = c
        tp = trips_on_arc.pivot_table(values=y_unit, index='depth_bin', columns=stacking, aggfunc='sum')

        # Make labeling more clear
        if y_unit == 'Totale Vaarkosten (EUR)':
            ylabelstring = 'Vaarkosten (mln EUR)'
            titlestring = 'Verhouding Diepgang-Vaarkosten bij {}'.format(label)
            figtype1 = 'Vaarkosten'
            tp = tp / 1e6
        elif y_unit == 'Totale Vracht (ton)':
            ylabelstring = 'Vervoerde vracht (mln ton)'
            titlestring = 'Verhouding Diepgang-Tonnage bij {}'.format(label)
            figtype1 = 'Vracht'
            tp = tp / 1e6
        elif y_unit == 'Aantal Vaarbewegingen (-)':
            ylabelstring = y_unit
            titlestring = 'Verhouding Diepgang-Vaarbewegingen bij {}'.format(label)
            figtype1 = 'Vaarbewegingen'
        else:
            ylabelstring = y_unit
            titlestring = ''
            figtype1 = y_unit

        if stacking == 'nstr_Short':
            figtype2 = 'NSTR'
        elif stacking == 'ship_types_Label':
            figtype2 = 'Scheepvaartklasse'
        elif stacking == 'appearance_types_Description':
            tp = tp.reindex(self.sqlAppearanceTypes()['Description'][::-1], axis=1)
            figtype2 = 'Vorm'
        elif stacking == 'lengte_bin':
            figtype2 = 'Lengte'
        elif stacking == 'cemt_class_Description':
            figtype2 = 'CEMT'
            tp = tp.reindex(self.sqlCEMTclass()['Description'], axis=1).dropna(axis=1, how='all')
        else:
            figtype2 = stacking

        tp.plot.bar(stacked=True, width=0.8, zorder=3, colormap='Paired_r')

        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.grid()
        plt.xlabel('Diepgang (m)')
        plt.ylabel(ylabelstring)
        plt.title(titlestring)
        # plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=tp.sum().sum()))

        plt.savefig(figdir / f'Hist_{label}_Diepgang_{figtype1}_per_{figtype2}.png'.format(figtype1, label, figtype2),
                    dpi=300, bbox_inches='tight')
        plt.savefig(figdir / f'Hist_{label}_Diepgang_{figtype1}_per_{figtype2}.svg'.format(figtype1, label, figtype2),
                    dpi=300, bbox_inches='tight')
        tp.to_csv(figdir / f'Hist_{label}_Diepgang_{figtype1}_per_{figtype2}.csv')

        plt.close()



    def plot_Vrachtanalyse(self):
        figdir = self.outputdir / 'figures_Vrachtanalyse'
        if not figdir.exists():
            figdir.mkdir()

        df = self.sqlAdvancedRoutes(group_by='NSTR')

        for c in [c for c in df.columns if 'Totale' in c]:
            d = c.replace('Totale', 'Gemiddelde')
            df[d] = df[c] / df['Aantal Vaarbewegingen (-)']

        dfnormed = df / df.sum()
        dfnormed.loc[:, ['Aantal Vaarbewegingen (-)',
                         'Totale Reistijd (min)', 'Totale Vaarkosten (EUR)',
                         'Totale Afstand (km)', 'Totale TonKM (TONKM)', 'Totale Vracht (ton)', 'Totale TEU (-)']].plot(
            kind='bar', figsize=(16, 4), zorder=3, width=0.8)
        plt.ylabel('Relatieve verdeling')
        plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        plt.xlabel('')
        plt.title('Verdeling van verschillende commodity')
        plt.ylim(0, 0.5)
        plt.grid()
        plt.savefig(figdir / 'Relatieve verdeling per commodity', kind='png', dpi=300, bbox_inches='tight')
        plt.close()

        # For each commodity how much tons per ship?
        df['Gemiddelde Vracht (ton)'].plot(kind='bar', figsize=(12, 4), zorder=3, color='C0')
        plt.grid()
        plt.ylabel('Gemiddelde belading (tons)')
        plt.savefig(figdir / 'Gemiddelde belading per commodity', kind='png', dpi=300, bbox_inches='tight')
        plt.close()

        df['Totale Vracht (ton)'].plot(kind='bar', figsize=(12, 4), color='C1', zorder=3)
        plt.grid()
        plt.ylabel('Totale vracht (tons)')
        plt.savefig(figdir / 'Totale vracht per commodity', kind='png', dpi=300, bbox_inches='tight')
        plt.close()

        df['Totale Vaarkosten (EUR)'].plot(kind='bar', figsize=(12, 4), color='C2', zorder=3)
        plt.grid()
        plt.ylabel('Totale kosten (EUR)')
        plt.savefig(figdir / 'Totale kosten per commodity', kind='png', dpi=300, bbox_inches='tight')
        plt.close()

        df['Kosten per ton'] = df['Totale Vaarkosten (EUR)'] / df['Totale Vracht (ton)']
        df['Kosten per ton'].plot(kind='bar', figsize=(12, 4), color='C3', zorder=3)
        plt.grid()
        plt.ylabel('Kosten per ton (EUR / ton)')
        plt.savefig(figdir / 'Kosten per ton per commodity', kind='png', dpi=300, bbox_inches='tight')
        plt.close()

        df['Gemiddelde TEU (-)'].plot(kind='bar', figsize=(12, 4), color='C4', zorder=3)
        plt.grid()
        plt.ylabel('Gemiddeld TEU')
        plt.savefig(figdir / 'Gemiddeld TEU per commodity', kind='png', dpi=300, bbox_inches='tight')
        plt.close()

    def plot_vergelijking_vaarwegen(self):
        figdir = self.outputdir / 'figures_Vergelijking_Vaarwegen'
        if not figdir.exists():
            figdir.mkdir()

        # SQL kosten en trips voor alle trips die langs een opgegeven Arc komen
        dfArcs = {}
        for Arc in sorted(self.Arcs):
            sql = """
            SELECT trips_{0}.NstrTypeCode AS NstrTypeCode,
                   SUM(routestat.VariableCosts__Eur) + SUM(routestat.FixedCosts__Eur) AS "Totale Vaarkosten",
                   SUM(trips_{0}.TotalWeight__t) AS "Totale Vracht",
                   COUNT(*) AS "Aantal Vaarbewegingen"
            FROM routes_{0}
            LEFT JOIN trips_{0} ON routes_{0}.TripID = trips_{0}.ID
            LEFT JOIN route_statistics_{0} AS routestat ON routes_{0}.TripID = routestat.TripID
            WHERE ArcID = {1}
            GROUP BY NstrTypeCode
            """.format(self.scenarioID, self.Arcs[Arc])

            dfArcs[Arc] = self.sql(sql)
            dfArcs[Arc] = dfArcs[Arc].replace({'NstrTypeCode': self.NSTR_shortnames})
            dfArcs[Arc] = dfArcs[Arc].set_index('NstrTypeCode')

        dfArcs = pd.concat(dfArcs, axis=1, sort=True)
        dfArcs = dfArcs.sort_index(axis=0)

        # Een totaal regel toevoegen met de totalen
        sql = """
        SELECT trips_{0}.NstrTypeCode AS NstrTypeCode,
               SUM(routestat.VariableCosts__Eur) + SUM(routestat.FixedCosts__Eur) AS "Totale Vaarkosten",
               SUM(trips_{0}.TotalWeight__t) AS "Totale Vracht",
               COUNT(*) AS "Aantal Vaarbewegingen"
        FROM routes_{0}
        LEFT JOIN trips_{0} ON routes_{0}.TripID = trips_{0}.ID
        LEFT JOIN route_statistics_{0} AS routestat ON routes_{0}.TripID = routestat.TripID
        WHERE RouteIndex = 0
        GROUP BY NstrTypeCode
        """.format(self.scenarioID)
        a = self.sql(sql).replace({'NstrTypeCode': self.NSTR_shortnames}).set_index('NstrTypeCode')

        for c in a.columns:
            dfArcs['Totaal', c] = a[c]

        # cols = dfArcs.columns.levels[0].drop('Totaal').tolist()
        # cols.append('Totaal')
        # dfArcs = dfArcs[cols]

        dfArcs = dfArcs.swaplevel(axis=1)

        (dfArcs['Totale Vaarkosten'] / 1e9).transpose().plot(kind='barh', stacked=True, figsize=(14, 8), zorder=3,
                                                             cmap='tab20c')
        plt.grid()
        plt.xlabel('totale vaarkosten (miljarden EUR)')
        plt.legend(loc=1, frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.xlim(0, 2.5)
        plt.savefig(figdir / 'Aandeel totale kosten per vaarweg', kind='png', dpi=300, bbox_inches='tight')

        (dfArcs["Totale Vracht"] / 1e6).transpose().plot(kind='barh', stacked=True, figsize=(14, 8), zorder=3,
                                                         cmap='tab20c')
        plt.grid()
        plt.xlabel('totale vracht (mln ton)')
        plt.legend(loc=1, frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.savefig(figdir / 'Aandeel vracht per vaarweg', kind='png', dpi=300, bbox_inches='tight')

        dfArcs["Aantal Vaarbewegingen"].transpose().plot(kind='barh', stacked=True, figsize=(14, 8), zorder=3,
                                                         cmap='tab20c')
        plt.grid()
        plt.xlabel('Aantal vaarbewegingen')
        plt.legend(loc=1, frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.savefig(figdir / 'Aantal vaarbewegingen per vaarweg', kind='png', dpi=300, bbox_inches='tight')

    def plot_vergelijking_trafficScenarios(self, trafficScenarios: list):
        figdir = self.outputdir / 'figures_Vergelijking_TrafficScenarios'
        if not figdir.exists():
            figdir.mkdir()

        sql = f"""
        SELECT
        SUM(NumberOfTrips) as nTrips,
        SUM(TotalWeight__t * NumberOfTrips) as totalWeight,
        NstrTypeCode,
        traffic_scenarios.Description AS Scheepvaartbestand
        from trips
        LEFT JOIN traffic_scenarios ON TrafficScenarioID = traffic_scenarios.ID
        WHERE TrafficScenarioID IN ({', '.join(str(t) for t in trafficScenarios)})
        GROUP BY NstrTypeCode, Scheepvaartbestand
        ORDER BY TrafficScenarioID
        """
        df = self.sql(sql)
        df = df.replace({'NstrTypeCode': self.NSTR_shortnames})

        trafficScenarios_table = self.sqlCountTripsPerTrafficScenario()
        trafficScenarios_names = trafficScenarios_table['Description'].loc[trafficScenarios]

        ## Vaarbewegingen

        df_pivot = df.pivot_table(columns='Scheepvaartbestand', index='NstrTypeCode', values='nTrips')
        df_pivot = df_pivot.reindex(columns=trafficScenarios_names)
        df_pivot.index.name = ''

        df_pivot.plot.bar(figsize=(12, 4), zorder=3)
        plt.grid()
        plt.title('Toename in aantal vaarbewegingen')
        plt.ylabel('Vaarbewegingen (-)')
        plt.savefig(figdir / 'ToenameVaarbewegingen.png', dpi=150, bbox_inches='tight')
        df_pivot.to_csv(figdir / 'ToenameVaarbewegingen.csv')

        ## Vracht

        df_pivot = df.pivot_table(columns='Scheepvaartbestand', index='NstrTypeCode', values='totalWeight')
        df_pivot = df_pivot.reindex(columns=trafficScenarios_names)
        df_pivot.index.name = ''

        df_pivot = df_pivot / 1e6

        df_pivot.plot.bar(figsize=(12, 4), zorder=3)
        plt.grid()
        plt.title('Toename in vracht')
        plt.ylabel('Vracht (miljoen ton)')
        plt.savefig(figdir / 'ToenameVracht.png', dpi=150, bbox_inches='tight')
        df_pivot.to_csv(figdir / 'ToenameVracht.csv')

    def plot_Beladingsgraad_all(self, **kwargs):
        for label, arcID in self.Arcs.items():
            self.plot_Beladingsgraad(arcID, label, **kwargs)

    def plot_Beladingsgraad(self, arcID, label, limit_to_1=True):
        figdir = self.outputdir / 'figures_Beladingsgraad'
        if not figdir.exists():
            figdir.mkdir()

        df = self.sqlArcDetails(arcID)
        df['Beladingsgraad'] = df['TotalWeight__t'] / df['LoadCapacity__t']
        if limit_to_1:
            df['Beladingsgraad'].loc[df['Beladingsgraad'] > 1] = 1
            bins = np.linspace(-0.000001, 1.0, 21)
        else:
            bins = np.linspace(-0.000001, 1.1, 23)
        df['Beladingsgraad_bins'] = pd.cut(df['Beladingsgraad'], bins, labels=np.round((bins[1:] + bins[:-1]) / 2, 3))

        df_pivot = df.pivot_table(index='Beladingsgraad_bins', columns='appearance_types_Description',
                                  values='NumberOfTrips',
                                  aggfunc='sum')
        df_pivot = df_pivot.reindex(self.sqlAppearanceTypes()['Description'][::-1], axis=1)
        df_pivot.columns.name = 'Vorm'
        df_pivot = df_pivot.fillna(0)

        y_max = df_pivot.sum(axis=1).iloc[1:].max() * 1.1

        # Create plot
        df_pivot.plot.bar(stacked=True, width=0.9, zorder=3)

        plt.ylim(bottom=0, top=y_max)
        if limit_to_1:
            plt.xticks(np.arange(-0.5, 20.51, 2), np.round(np.arange(0, 1.1, 0.1), 1))
        else:
            plt.xticks(np.arange(-0.5, 21.51, 2), np.round(np.arange(0, 1.2, 0.1), 1))
        plt.ylabel('Aantal vaarbewegingen')
        plt.xlabel('Beladingsgraad')
        plt.title(f'{label}')
        plt.grid()
        plt.legend(loc=6, bbox_to_anchor=(1, 0.5))

        plt.annotate(f'{df_pivot.sum(axis=1).iloc[0]:.0f}', xy=(0.025, y_max), xytext=(30, -50),
                     textcoords='offset points',
                     arrowprops=dict(arrowstyle="->"),
                     )

        plt.savefig(figdir / f'Beladingsgraad_{label}.png', dpi=300, bbox_inches='tight')
        plt.savefig(figdir / f'Beladingsgraad_{label}.svg', bbox_inches='tight')
        plt.close()

    def plot_tijdseries_vloot(self, arcID, label, time_start=50, time_end=110):
        figdir = self.outputdir / 'figures_Tijdseries_vloot'
        if not figdir.exists():
            figdir.mkdir()

        df = self.sqlArcDetails(arcID)

        ordered_ship_types, data_merge_small_ships = self.remove_small_ships(df)
        data = data_merge_small_ships.groupby(['DayOfYear', 'ship_types_Label']).count()['Depth__m'].unstack()[
            ordered_ship_types].fillna(0)

        # First some plots of timeseries of the ships passing
        lines_per_plot = 5
        f, ax = plt.subplots(nrows=np.ceil(data.shape[1] / lines_per_plot).astype(int), figsize=(8, 16), sharey=True,
                             sharex=True)
        for ii, n in enumerate(range(0, data.shape[1], lines_per_plot)):
            data.iloc[:, n:n + lines_per_plot].rolling(7, center=True).mean().plot(ax=ax[ii])
            ax[ii].legend(loc='center left', bbox_to_anchor=(1, 0.5))
            ax[ii].grid()
            ax[ii].set_ylabel('Aantal vaarbewegingen')
            ax[ii].set_xlabel('')
        plt.xlim(1, 365)
        plt.xlabel('Dag van het jaar')

        data.to_csv(figdir / f'Tijdserie_shipping_types_{label}.csv')
        plt.savefig(figdir / f'Tijdserie_shipping_types_{label}.png', dpi=300, bbox_inches='tight')

        # Normalised timeseries
        ndays = time_end - time_start
        average_daily = data.loc[time_start:time_end].sum(axis=0) / ndays
        data_normalised = data.divide(average_daily, axis=1)

        lines_per_plot = 5
        f, ax = plt.subplots(nrows=np.ceil(data_normalised.shape[1] / lines_per_plot).astype(int), figsize=(8, 16),
                             sharey=True, sharex=True)
        for ii, n in enumerate(range(0, data_normalised.shape[1], lines_per_plot)):
            data_normalised.iloc[:, n:n + lines_per_plot].rolling(7, center=True).mean().plot(ax=ax[ii])
            ax[ii].legend(loc='center left', bbox_to_anchor=(1, 0.5))
            ax[ii].grid()
            ax[ii].set_ylabel('Genormaliseerde \n aantal vaarbewegingen')
            ax[ii].set_xlabel('')
        plt.ylim(0, 7)
        plt.xlim(1, 365)
        plt.xlabel('Dag van het jaar')

        plt.savefig(figdir / f'Tijdserie_shipping_types_{label}_normalised.png', dpi=300, bbox_inches='tight')

    def plot_Vlootopbouw_all(self):
        for label, arcID in self.Arcs.items():
            self.plot_Vlootopbouw(arcID, label)

    def plot_Vlootopbouw(self, arcID, label):
        figdir = self.outputdir / 'figures_Vlootopbouw'
        if not figdir.exists():
            figdir.mkdir()

        df = self.sqlArcDetails(arcID)
        ship_types = self.sqlShipTypes()

        ordered_ship_types, data_merge_small_ships = self.remove_small_ships(df)
        appearanceTypesOrder = self.sqlAppearanceTypes()['Description'][::-1]
        data = data_merge_small_ships.groupby(['ship_types_Label', 'appearance_types_Description']
                                              ).count()['Depth__m'].unstack().loc[
            ordered_ship_types, appearanceTypesOrder].fillna(0)  # TODO: Change .loc[] to .reindex()
        data.plot.bar(stacked=True, width=0.9, zorder=3, figsize=(8, 6), color=['C0', 'C1', 'C2', '#555555'])
        plt.gca().legend(*map(reversed, plt.gca().get_legend_handles_labels()), loc='center left',
                         bbox_to_anchor=(1, 0.5))
        plt.grid()
        plt.xlabel('')
        plt.ylabel('Aantal vaarbewegingen')

        # Add labels below the figure
        d = ship_types.set_index('Label').loc[ordered_ship_types]
        d['Nummering'] = np.arange(0, d.shape[0])

        range_start = d.groupby('CEMTTypeID')['Nummering'].min()
        range_end = d.groupby('CEMTTypeID')['Nummering'].max()
        CEMT_names = d.iloc[:, 2:].groupby('CEMTTypeID')['Description'].first()

        trans = plt.gca().get_xaxis_transform()
        for name, s, e in zip(CEMT_names, range_start, range_end):
            plt.plot([s - 0.3, e + 0.3], [-0.15, -0.15], c='k', transform=trans, clip_on=False)
            plt.gca().annotate(name, xy=((s + e) / 2, -0.17), ha='center', va='top', xycoords=trans)

        data.to_csv(figdir / f'Shipping_types_{label}.csv')
        plt.savefig(figdir / f'Shipping_types_{label}.png', dpi=300, bbox_inches='tight')
        plt.close()

class IVS90_analyse(pyBIVAS_plot):

    def __init__(self,
                 label_traffic_scenario=[2011, 2013, 2014, 2016, 2017, 2018],
                 reference_trip_ids=[1, 2, 3, 4, 5, 6]
                 ):
        super().__init__()

        sql = """SELECT * FROM traffic_scenarios"""
        traffic_scenarios = self.sql(sql)

        sql = """SELECT * FROM reference_trip_sets"""
        reference_trip_sets = self.sql(sql).set_index('ID')

        traffic_scenarios.index = label_traffic_scenario

        traffic_scenarios['reference_trips_sets_id'] = reference_trip_ids
        traffic_scenarios = traffic_scenarios.join(reference_trip_sets, on='reference_trips_sets_id',
                                                   rsuffix='_reference_trips')

        self.traffic_scenarios = traffic_scenarios

        self.cemt_order = self.sql("""SELECT * FROM cemt_class ORDER BY Id""")['Description']
        self.ship_types_order = self.sqlShipTypes()['Description']

    # Jaarlijkse variatie
    def plot_CountingPointsForYear(self, telpunt='Prins Bernhardsluis', jaar=2018):
        print(telpunt, jaar)

        # Set variables
        referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
        countingPointName = telpunt

        # Query data
        sql = """
        SELECT
        DATE(trips.DateTime) AS "Days",
        directions.Label AS Vaarrichting,
        count(*) AS nTrips
        FROM reference_trip_set
        LEFT JOIN trips ON reference_trip_set.TripID == trips.ID
        LEFT JOIN counting_points ON reference_trip_set.CountingPointID == counting_points.ID
        LEFT JOIN directions on counting_points.DirectionID == directions.ID
        WHERE ReferenceSetID = {}
        AND counting_points.Name = "{}"
        AND trips.TrafficScenarioID = {}
        GROUP BY "Days", counting_points.DirectionID
        """.format(referenceSetId, countingPointName, trafficScenarioId)
        df = self.sql(sql)
        if not len(df):
            return 'No data'

        # Format data
        df['Days'] = pd.to_datetime(df['Days'])
        df = df.set_index('Days')
        df = df.pivot(columns='Vaarrichting')['nTrips']
        fullyear = pd.date_range('01-01-{}'.format(df.index[0].year), '31-12-{}'.format(df.index[0].year))
        df = df.loc[fullyear]
        df[df.isnull()] = 0

        # Plot data
        df.plot(kind='area', stacked=True, figsize=(16, 6), )
        plt.title('{} - {}'.format(telpunt, jaar))
        plt.grid()
        plt.ylabel('Aantal passages')

        plt.savefig('Tijdserie_{}_{}.png'.format(telpunt, jaar), dpi=300)
        df.to_csv('Tijdserie_{}_{}.csv'.format(telpunt, jaar))

        plt.show()
        return

    # Opbouw vaarbewegingen
    def plot_CEMTclassesForYear(self, telpunt='Prins Bernhardsluis', jaar=2018):
        print(telpunt, jaar)

        # Set variables
        referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
        countingPointName = telpunt

        # Query data
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
        if not len(df):
            return 'No data'

        # Format data
        df = df.set_index('CEMT_klasse')
        df = df['nTrips']

        # Plot data
        df.plot.pie(stacked=True, figsize=(6, 6), cmap='coolwarm', wedgeprops={'edgecolor': 'w'})
        plt.title('{} - {}'.format(telpunt, jaar))
        plt.grid()
        plt.ylabel('Verdeling CEMT klasse (naar aantal passages)')

        plt.savefig('CEMT_{}_{}.png'.format(telpunt, jaar), dpi=300)
        df.to_csv('CEMT_{}_{}.csv'.format(telpunt, jaar))

        plt.show()
        return

    def plot_YearlyChanges_Timeseries(self, telpunt='Prins Bernhardsluis'):
        print(telpunt)

        global dfs

        dfs = {}
        for jaar in self.traffic_scenarios.index:
            # Set variables
            referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
            trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
            countingPointName = telpunt

            # Query data
            sql = """
            SELECT
            DATE(trips.DateTime) AS "Days",
            count(*) AS nTrips
            FROM reference_trip_set
            LEFT JOIN trips ON reference_trip_set.TripID == trips.ID
            LEFT JOIN counting_points ON reference_trip_set.CountingPointID == counting_points.ID
            WHERE ReferenceSetID = {}
            AND counting_points.Name = "{}"
            AND trips.TrafficScenarioID = {}
            GROUP BY "Days"
            """.format(referenceSetId, countingPointName, trafficScenarioId)
            df = self.sql(sql)
            if not len(df):
                return 'No data'

            # Format data
            df['Days'] = pd.to_datetime(df['Days'])
            df = df.set_index('Days')
            df = df['nTrips']

            fullyear = pd.date_range('01-01-{}'.format(df.index[0].year), '31-12-{}'.format(df.index[0].year))
            df = df.loc[fullyear]
            df[df.isnull()] = 0

            df = df.resample('M').sum()
            df.index = ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']

            dfs[jaar] = df

        dfs = pd.concat(dfs, axis=1)

        # Plot data
        dfs.plot.bar(figsize=(16, 6), width=0.75)
        plt.title('{}'.format(telpunt))
        plt.grid()
        plt.ylabel('Aantal passages')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.savefig('HistorischVerloop_{}.png'.format(telpunt), dpi=300)
        dfs.to_csv('HistorischVerloop_{}.csv'.format(telpunt))

        plt.show()
        return

    def plot_YearlyChangesCEMT(self, telpunt='Born sluis'):
        print(telpunt)

        global dfs

        dfs = {}
        for jaar in self.traffic_scenarios.index:
            # Set variables
            referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
            trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
            countingPointName = telpunt

            # Query data
            sql = """
            SELECT
            cemt_class.Description AS CEMT_klasse,
            count(*) AS nTrips
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
            if not len(df):
                return 'No data'

            df.set_index('CEMT_klasse', inplace=True)

            dfs[jaar] = df['nTrips']

        dfs = pd.concat(dfs, axis=1, sort=False)
        dfs = dfs.reindex(index=[o for o in self.cemt_order if o in dfs.index])

        # Plot data
        dfs.T.plot.bar(figsize=(6, 6), width=0.75, stacked=True, zorder=3)
        plt.title('{}'.format(telpunt))
        plt.grid()
        plt.ylabel('Aantal passages')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.savefig('HistorischVerloopYearCEMT_{}.png'.format(telpunt), dpi=300, bbox_inches='tight')
        dfs.to_csv('HistorischVerloopYearCEMT_{}.csv'.format(telpunt))

        plt.show()
        return

    def plot_YearlyChangesRWSklasse(self, telpunt='Maasbracht sluis'):
        print(telpunt)

        global dfs

        dfs = {}
        for jaar in self.traffic_scenarios.index:
            # Set variables
            referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
            trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
            countingPointName = telpunt

            # Query data
            sql = """
            SELECT
            cemt_class.Description AS CEMT_klasse,
            ship_types.Label AS RWS_klasse,
            count(*) AS nTrips
            FROM reference_trip_set
            LEFT JOIN trips ON reference_trip_set.TripID == trips.ID
            LEFT JOIN counting_points ON reference_trip_set.CountingPointID == counting_points.ID
            LEFT JOIN ship_types ON trips.ShipTypeID == ship_types.ID
            LEFT JOIN cemt_class ON ship_types.CEMTTypeID == cemt_class.ID
            WHERE ReferenceSetID = {}
            AND counting_points.Name = "{}"
            AND trips.TrafficScenarioID = {}
            GROUP BY RWS_klasse
            ORDER BY RWS_klasse
            """.format(referenceSetId, countingPointName, trafficScenarioId)
            df = self.sql(sql)
            if not len(df):
                return 'No data'

            df.set_index('RWS_klasse', inplace=True)
            dfs[jaar] = df['nTrips']

        dfs = pd.concat(dfs, axis=1, sort=False)
        dfs = dfs.reindex(index=[o for o in self.ship_types_order])

        # Plot data
        dfs.T.plot.bar(figsize=(6, 6), width=0.75, stacked=True, zorder=3)
        plt.title('{}'.format(telpunt))
        plt.grid()
        plt.ylabel('Aantal passages')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.savefig('HistorischVerloopYearRWSklasse_{}.png'.format(telpunt), dpi=300, bbox_inches='tight')
        dfs.to_csv('HistorischVerloopYearRWSklasse_{}.csv'.format(telpunt))

        plt.show()
        return

    def plot_all(self):
        countingPoints = self.listCountingPoints()
        for c in countingPoints['Name']:
            for y in self.traffic_scenarios.index:
                self.plot_CountingPointsForYear(c, y)

        for c in countingPoints['Name']:
            for y in self.traffic_scenarios.index:
                self.plot_CEMTclassesForYear(c, y)

        for c in countingPoints['Name']:
            self.plot_YearlyChanges_Timeseries(c)

        for c in countingPoints['Name']:
            self.plot_YearlyChangesCEMT(c)

        for c in countingPoints['Name']:
            self.plot_YearlyChangesRWSklasse(c)
