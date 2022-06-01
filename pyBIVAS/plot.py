"""
This function contains generic plotting functions to go with the module pyBIVAS
"""

from pyBIVAS.SQL import pyBIVAS

import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from typing import Optional

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

    # Arcs in BIVAS
    Arcs = {
        'BovenRijn': 9204,
        'Waal': 6332,
        'Pannerdensch Kanaal': 8886,
        'Nederrijn': 6645,
        'Lek': 6717,
        'IJssel': 6510,
        'Zuid-Willemsvaart': 9130,
        'Maas (Oost-West)': 7523,
        'Maasroute': 9166,
        'Julianakanaal': 8710,
        'Schelde-Rijnverbinding': 8387,
        'Betuwepand (ARK)': 6853,
        'Amsterdam-Rijnkanaal': 1645,
        'Merwedekanaal': 6330,
        'Delftse Schie': 6572,
        'Oude Maas': 7121,
        'Nieuwe Maas': 6746,
        'Maasmond': 6452,
        'Maas-Waalkanaal': 7260,
        'Westerschelde': 8516,
        'Lemmer-Delfzijl': 2099,
        'Kanaal Zuid-Beveland': 8361
    }

    # Added some more arcs
    Arcs_overig = {
        'Ondiepte St. Andries': 7362,
        'Ondiepte Nijmegen': 6320,
        'Kanaal van St. Andries': 7378,
        'Prins Bernhardsluizen in Betuwepand': 1705
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outputdir = Path('.')


    def plot_Trips_Arc_all(self):
        for label, arcID in self.Arcs.items():
            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='NSTR')
            self.plot_Trips_Arc(arcID, label, y_unit='Totale Vracht (ton)', stacking='NSTR')
            self.plot_Trips_Arc(arcID, label, y_unit='Aantal Vaarbewegingen (-)', stacking='NSTR')

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

    def plot_Trips_Arc(self, arcID, label, y_unit='Totale Vaarkosten (EUR)', stacking='NSTR'):
        """
        This function creates multiple barplots of trips passing a given arc as as function on the draft

        :return:
        """
        figdir = self.outputdir / 'figures_Histogram_Diepgang'
        if not figdir.exists():
            figdir.mkdir()

        trips_on_arc = self.arc_tripdetails(arcID)

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

        if stacking == 'NSTR':
            figtype2 = 'NSTR'
        elif stacking == 'ship_types_Label':
            figtype2 = 'Scheepvaartklasse'
        elif stacking == 'appearance_types_Description':
            tp = tp.reindex(self.appearancetypes()['Description'][::-1], axis=1)
            figtype2 = 'Vorm'
        elif stacking == 'lengte_bin':
            figtype2 = 'Lengte'
        elif stacking == 'cemt_class_Description':
            figtype2 = 'CEMT'
            tp = tp.reindex(self.CEMTclass()['Description'], axis=1).dropna(axis=1, how='all')
        else:
            figtype2 = stacking

        tp.plot.bar(stacked=True, width=0.8, zorder=3, colormap='Paired_r')

        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.grid()
        plt.xlabel('Diepgang (m)')
        plt.ylabel(ylabelstring)
        plt.title(titlestring)
        # plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=tp.sum().sum()))

        plt.savefig(figdir / f'Hist_{label}_Diepgang_{figtype1}_per_{figtype2}.png',
                    dpi=300, bbox_inches='tight')
        # plt.savefig(figdir / f'Hist_{label}_Diepgang_{figtype1}_per_{figtype2}.svg',
        #             dpi=300, bbox_inches='tight')
        tp.to_csv(figdir / f'Hist_{label}_Diepgang_{figtype1}_per_{figtype2}.csv')

        plt.close()

    def plot_Vrachtanalyse(self):
        figdir = self.outputdir / 'figures_Vrachtanalyse'
        if not figdir.exists():
            figdir.mkdir()

        df = self.routestatistics_advanced(group_by='NSTR')

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

        # Do not take into account the number of trips as a result of the BIVAS computation! (temporary)
        compute_route_statistics_original = self.compute_route_statistics
        self.compute_route_statistics = compute_route_statistics_original.replace('trips.NumberOfTrips', '1')

        # SQL kosten en trips voor alle trips die langs een opgegeven Arc komen
        dfArcs = {}
        for ArcName, ArcID in self.Arcs.items():
            df = self.arc_tripdetails(ArcID, group_by='NSTR')
            dfArcs[ArcName] = df[["Totale Vaarkosten (EUR)", "Totale Vracht (ton)", "Aantal Vaarbewegingen (-)"]]

        # Reset settings
        self.compute_route_statistics = compute_route_statistics_original

        dfAllArcs = self.routestatistics_advanced(group_by='NSTR')
        dfAllArcs = dfAllArcs[["Totale Vaarkosten (EUR)", "Totale Vracht (ton)", "Aantal Vaarbewegingen (-)"]]

        dfArcs['Totaal'] = dfAllArcs

        arc_order = list(self.Arcs.keys()) + ['Totaal']
        dfArcs = pd.concat(dfArcs, axis=1, sort=False)[arc_order]
        dfArcs = dfArcs.sort_index(axis=0)

        dfArcs = dfArcs.swaplevel(axis=1)

        # Plot vaarkosten
        (dfArcs['Totale Vaarkosten (EUR)'] / 1e9).transpose().plot(kind='barh', stacked=True, figsize=(14, 8), zorder=3,
                                                                   cmap='tab20c')
        plt.grid()
        plt.xlabel('totale vaarkosten (miljarden EUR)')
        plt.legend(loc='center right', frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.xlim(0, 2.5)
        plt.savefig(figdir / 'Aandeel totale kosten per vaarweg', kind='png', dpi=300, bbox_inches='tight')
        dfArcs["Totale Vaarkosten (EUR)"].transpose().to_csv(figdir / 'Aandeel totale kosten per vaarweg.csv')
        plt.close()

        # Plot vracht
        (dfArcs["Totale Vracht (ton)"] / 1e6).transpose().plot(kind='barh', stacked=True, figsize=(14, 8), zorder=3,
                                                               cmap='tab20c')
        plt.grid()
        plt.xlabel('totale vracht (mln ton)')
        plt.legend(loc='center right', frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.savefig(figdir / 'Aandeel vracht per vaarweg', kind='png', dpi=300, bbox_inches='tight')
        dfArcs["Totale Vracht (ton)"].transpose().to_csv(figdir / 'Aandeel vracht per vaarweg.csv')
        plt.close()

        # Plot aantal vaarbeweingen
        dfArcs["Aantal Vaarbewegingen (-)"].transpose().plot(kind='barh', stacked=True, figsize=(14, 8), zorder=3,
                                                             cmap='tab20c')
        plt.grid()
        plt.xlabel('Aantal vaarbewegingen')
        plt.legend(loc='center right', frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.savefig(figdir / 'Aantal vaarbewegingen per vaarweg', kind='png', dpi=300, bbox_inches='tight')
        dfArcs["Aantal Vaarbewegingen (-)"].transpose().to_csv(figdir / 'Aantal vaarbewegingen per vaarweg.csv')
        plt.close()

    def plot_vergelijking_trafficScenarios(self, trafficScenarios: list):
        figdir = self.outputdir / 'figures_Vergelijking_TrafficScenarios'
        if not figdir.exists():
            figdir.mkdir()

        sql = f"""
        SELECT
        SUM(NumberOfTrips) as nTrips,
        SUM(TotalWeight__t * NumberOfTrips) as totalWeight,
        NstrGoodsClassification AS NSTR,
        traffic_scenarios.Description AS Scheepvaartbestand
        FROM trips
        LEFT JOIN traffic_scenarios ON TrafficScenarioID = traffic_scenarios.ID
        WHERE TrafficScenarioID IN ({', '.join(str(t) for t in trafficScenarios)})
        GROUP BY NstrGoodsClassification, Scheepvaartbestand
        ORDER BY TrafficScenarioID
        """
        df = self.sql(sql)
        df = df.replace({'NSTR': self.NSTR_shortnames})

        trafficScenarios_table = self.trafficscenario_numberoftrips()
        trafficScenarios_names = trafficScenarios_table['Description'].loc[trafficScenarios]

        ## Vaarbewegingen

        df_pivot = df.pivot_table(columns='Scheepvaartbestand', index='NSTR', values='nTrips')
        df_pivot = df_pivot.reindex(columns=trafficScenarios_names)
        df_pivot.index.name = ''

        df_pivot.plot.bar(figsize=(12, 4), zorder=3)
        plt.grid()
        plt.title('Toename in aantal vaarbewegingen')
        plt.ylabel('Vaarbewegingen (-)')
        plt.savefig(figdir / 'ToenameVaarbewegingen.png', dpi=150, bbox_inches='tight')
        df_pivot.to_csv(figdir / 'ToenameVaarbewegingen.csv')
        plt.close()

        ## Vracht

        df_pivot = df.pivot_table(columns='Scheepvaartbestand', index='NSTR', values='totalWeight')
        df_pivot = df_pivot.reindex(columns=trafficScenarios_names)
        df_pivot.index.name = ''

        df_pivot = df_pivot / 1e6

        df_pivot.plot.bar(figsize=(12, 4), zorder=3)
        plt.grid()
        plt.title('Toename in vracht')
        plt.ylabel('Vracht (miljoen ton)')
        plt.savefig(figdir / 'ToenameVracht.png', dpi=150, bbox_inches='tight')
        df_pivot.to_csv(figdir / 'ToenameVracht.csv')
        plt.close()

    def plot_Beladingsgraad_all(self, **kwargs):
        for label, arcID in self.Arcs.items():
            self.plot_Beladingsgraad(arcID, label, **kwargs)

    def plot_Beladingsgraad(self, arcID, label, limit_to_1=True):
        figdir = self.outputdir / 'figures_Beladingsgraad'
        if not figdir.exists():
            figdir.mkdir()

        df = self.arc_tripdetails(arcID)
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
        df_pivot = df_pivot.reindex(self.appearancetypes()['Description'][::-1], axis=1)
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
        # plt.savefig(figdir / f'Beladingsgraad_{label}.svg', bbox_inches='tight')
        plt.close()

    def plot_tijdseries_vloot(self, arcID, label, time_start='2018-03', time_end='2018-06'):
        """

        :param arcID:
        :param label: Label for filename and title
        :param time_start: Time start of normalised period
        :param time_end: Time end of normalised period
        :return:
        """
        figdir = self.outputdir / 'figures_Tijdseries_vloot'
        if not figdir.exists():
            figdir.mkdir()

        df = self.arc_tripdetails(arcID)

        ordered_ship_types, data_merge_small_ships = self.remove_small_ships(df)
        data = data_merge_small_ships.groupby(['DateTime', 'ship_types_Label']).count()['Depth__m'].unstack().reindex(
            ordered_ship_types, axis=1).fillna(0)

        fullyear = pd.date_range('01-01-{}'.format(data.index[0].year), '31-12-{}'.format(data.index[0].year))
        data = data.reindex(fullyear, fill_value=0)

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
        # plt.xlim(1, 365)
        plt.xlabel('')

        data.to_csv(figdir / f'Tijdserie_shipping_types_{label}.csv')
        plt.savefig(figdir / f'Tijdserie_shipping_types_{label}.png', dpi=300, bbox_inches='tight')

        # Normalised timeseries
        average_daily = data[time_start:time_end].mean(axis=0)
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
        # plt.xlim(1, 365)
        plt.xlabel('')

        plt.savefig(figdir / f'Tijdserie_shipping_types_{label}_normalised.png', dpi=300, bbox_inches='tight')

    def plot_Vlootopbouw_all(self):
        for label, arcID in self.Arcs.items():
            self.plot_Vlootopbouw(arcID, label)

    def plot_Vlootopbouw(self, arcID, label, userealtrips=True):
        """



        :param arcID:
        :param label:
        :param userealtrips: Either use the number of tracks in the database (so real trips) or the NumberOfTrips of the BIVAS result
        :return:
        """

        figdir = self.outputdir / 'figures_Vlootopbouw'
        if not figdir.exists():
            figdir.mkdir()

        df = self.arc_tripdetails(arcID)
        ship_types = self.shiptypes()

        ordered_ship_types, data_merge_small_ships = self.remove_small_ships(df)
        appearanceTypesOrder = self.appearancetypes()['Description'][::-1]
        if userealtrips:
            data = data_merge_small_ships.groupby(['ship_types_Label', 'appearance_types_Description']
                                                  ).count()['Depth__m']\
                .unstack().\
                reindex(ordered_ship_types, axis=0, fill_value=0).\
                reindex(appearanceTypesOrder, axis=1, fill_value=0)

        else:
            data = data_merge_small_ships.groupby(['ship_types_Label', 'appearance_types_Description']
                                                  ).sum()["Aantal Vaarbewegingen (-)"]\
                .unstack().\
                reindex(ordered_ship_types, axis=0, fill_value=0).\
                reindex(appearanceTypesOrder, axis=1, fill_value=0)
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
                 databasefile=None,
                 traffic_scenario_ids=None,
                 traffic_scenario_labels=[2011, 2013, 2014, 2016, 2017, 2018],
                 reference_trip_ids=[1, 2, 3, 4, 5, 6]
                 ):
        super().__init__(databasefile=databasefile)

        sql = """SELECT * FROM traffic_scenarios"""
        traffic_scenarios = self.sql(sql)

        if traffic_scenario_ids:
            traffic_scenarios.set_index('ID', inplace=True)
            traffic_scenarios = traffic_scenarios.loc[traffic_scenario_ids]
            traffic_scenarios.reset_index(inplace=True)

        sql = """SELECT * FROM reference_trip_sets"""
        reference_trip_sets = self.sql(sql).set_index('ID')

        if traffic_scenario_labels:
            traffic_scenarios.index = traffic_scenario_labels
        else:
            traffic_scenarios.index = traffic_scenarios['Description']

        traffic_scenarios['reference_trips_sets_id'] = reference_trip_ids
        traffic_scenarios = traffic_scenarios.join(reference_trip_sets, on='reference_trips_sets_id',
                                                   rsuffix='_reference_trips')

        self.traffic_scenarios = traffic_scenarios

        self.cemt_order = self.CEMTclass()['Description']
        self.ship_types_order = self.shiptypes()['Description']


    # Jaarlijkse variatie
    def plot_countingpoint_timeseries(self, telpunt='Prins Bernhardsluis', jaar=2018, param="Aantal Vaarbewegingen (-)"):
        figdir = self.outputdir / 'figures_CountingPointsForYear'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting CountingPointsForYear voor telpunt: {telpunt}, jaar: {jaar}')

        # Set variables
        referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
        countingPointName = telpunt

        # Query data
        df = self.countingpoint_timeseries(referenceSetId, countingPointName, trafficScenarioId, param=param)
        if not len(df):
            return 'No data'

        # Plot data

        if param == "Aantal Vaarbewegingen (-)":
            df.plot(kind='area', stacked=True, figsize=(16, 6), )
        elif param == "Totale Vracht (ton)":
            df.plot(kind='area', stacked=True, figsize=(16, 6), color=['C2', 'C3'])

        plt.title('{} - {}'.format(telpunt, jaar))
        plt.grid()

        if param == "Aantal Vaarbewegingen (-)":
            plt.ylabel('Aantal passages')

            plt.savefig(figdir / 'Tijdserie_{}_{}.png'.format(telpunt, jaar), dpi=300)
            df.to_csv(figdir / 'Tijdserie_{}_{}.csv'.format(telpunt, jaar))

        elif param == "Totale Vracht (ton)":
            plt.ylabel("Totale Vracht (ton)")

            plt.savefig(figdir / 'TijdserieVracht_{}_{}.png'.format(telpunt, jaar), dpi=300)
            df.to_csv(figdir / 'TijdserieVracht_{}_{}.csv'.format(telpunt, jaar))

        plt.close()

    # Jaarlijkse variatie
    def plot_countingpoint_timeseries_weekly(self, telpunt='Prins Bernhardsluis', jaar=2018,
                                             param="Aantal Vaarbewegingen (-)", opdeling='Vaarrichting',
                                             relatief: Optional[tuple] = None):
        """


        :param telpunt:
        :param jaar:
        :param param:
        :param opdeling: None, "Vaarrichting", "Bestemming", "Herkomst", "Scheepvaartklasse", "CEMT-klasse"
        :param relatief:
        :return:
        """

        # Extend query with zones instead of vaarrichting
        figdir = self.outputdir / 'figures_CountingPointsPerWeek'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting CountingPointsForYear voor telpunt: {telpunt}, jaar: {jaar} ({param}, {opdeling}, {relatief})')

        # Set variables
        referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
        countingPointName = telpunt

        # Query data
        df = self.countingpoint_timeseries(referenceSetId, countingPointName, trafficScenarioId, param=param,
                                           pivot=opdeling)
        if df is None:
            return 'No data'

        postfix = ''
        if relatief is not None:
            reference_period = df[relatief[0]:relatief[1]].sum(axis=1).mean(axis=0)
            df = df.divide(reference_period, axis='columns')
            postfix = '_rel'

        df = df.resample('W').mean()
        df.index = pd.Int64Index(df.index.isocalendar().week)

        if np.isin(opdeling, ['Herkomst', 'Bestemming', 'Scheepvaartklasse', 'CEMT-klasse']):
            df_uncompressed = df.copy()
            if df.shape[1] > 20:
                # Only select top 19 + Overig
                sorted_opdeling = df_uncompressed.sum().sort_values(ascending=False)
                # df = df_uncompressed.loc[:, sorted_opdeling.index[:19]]
                df = df_uncompressed.drop(sorted_opdeling.index[19:], axis=1)
                df.loc[:, 'Overig'] = df_uncompressed.loc[:, sorted_opdeling.index[19:]].sum(axis=1)

                # # Only select regions larger than 1%
                # aandeel_per_zone = (df.sum() / df.sum().sum())
                # df2 = df.loc[:, aandeel_per_zone >= 0.01].copy()
                # df2.loc[:, 'Overig'] = df.loc[:, aandeel_per_zone < 0.01].sum(axis=1)

        # Make stacked barplot
        bars = df.plot.bar(stacked=True, figsize=(10, 4), zorder=3, width=0.85, cmap='tab20', linewidth=0)

        if np.isin(opdeling, ['Herkomst', 'Bestemming', 'Scheepvaartklasse', 'CEMT-klasse']):
            if 'Overig' in df.columns:
                for ii, bar in enumerate(bars.patches):
                    if (ii // df.shape[0]) == (df.shape[1] -1):
                        bar.set_hatch('\\\\\\\\', )
                        bar.set_edgecolor([0.5, 0.5, 0.5])

        plt.title('{} - {}'.format(telpunt, jaar))
        plt.grid()

        param_name = param.split(' (')[0]
        plt.xlabel(f'Weeknummer')

        if relatief is None:
            plt.ylabel(param + ' per dag')
        else:
            plt.ylabel(param_name + ' per dag (relatief)')

        if np.isin(opdeling, ['Herkomst', 'Bestemming', 'Scheepvaartklasse', 'CEMT-klasse']):
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4, title=opdeling)
            plt.savefig(figdir / 'Tijdserie_{}_{}_{}_{}{}.png'.format(telpunt, jaar, param_name, opdeling, postfix), dpi=300, bbox_inches='tight')
            df_uncompressed.to_csv(figdir / 'Tijdserie_{}_{}_{}_{}{}.csv'.format(telpunt, jaar, param_name, opdeling, postfix))
        else:
            plt.savefig(figdir / 'Tijdserie_{}_{}_{}_{}{}.png'.format(telpunt, jaar, param_name, opdeling, postfix),
                        dpi=300)
            df.to_csv(figdir / 'Tijdserie_{}_{}_{}_{}{}.csv'.format(telpunt, jaar, param_name, opdeling, postfix))
        plt.close()


    def plot_countingpoint_piechart_CEMTclasses(self, telpunt='Prins Bernhardsluis', jaar=2018):
        """
        Opbouw vaarbewegingen voor telpunt en jaar
        """
        figdir = self.outputdir / 'figures_CEMTclassesForYear'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting CEMTclassesForYear voor telpunt: {telpunt}, jaar: {jaar}')

        # Set variables
        referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
        countingPointName = telpunt

        # Query data
        df = self.countingpoint_CEMT_klasse(referenceSetId, countingPointName, trafficScenarioId)
        if not len(df):
            return 'No data'

        # Plot data

        # Only label where the bin is larger than 5%
        only_large_labels = [k if v / df.max() > 0.03 else '' for k, v in df.iteritems()]

        df.plot.pie(stacked=True, figsize=(6, 6), cmap='coolwarm', wedgeprops={'edgecolor': 'w'},
                    labels=only_large_labels)
        plt.title('{} - {}'.format(telpunt, jaar))
        plt.grid()
        plt.ylabel('Verdeling CEMT klasse (naar aantal passages)')

        plt.savefig(figdir / 'CEMT_{}_{}.png'.format(telpunt, jaar), dpi=300)
        df.to_csv(figdir / 'CEMT_{}_{}.csv'.format(telpunt, jaar), header=False)

        plt.close()

    def plot_countingpoint_montlytimeseries_yearlychanges(self, telpunt='Prins Bernhardsluis'):
        figdir = self.outputdir / 'figures_YearlyChanges_Timeseries'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting YearlyChanges_Timeseries voor telpunt: {telpunt}')

        dfs = {}
        for jaar in self.traffic_scenarios.index:
            # Set variables
            referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
            trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
            countingPointName = telpunt

            # Query data
            df = self.countingpoint_timeseries(referenceSetId, countingPointName, trafficScenarioId, pivot=None)

            if not len(df):
                continue

            # Format data
            df = df.resample('M').sum()
            df.index = ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']

            dfs[jaar] = df

        if not len(dfs):
            return 'No data'

        dfs = pd.concat(dfs, axis=1)

        # Plot data
        dfs.plot.bar(figsize=(16, 6), width=0.75)
        plt.title('{}'.format(telpunt))
        plt.grid()
        plt.ylabel('Aantal passages')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.savefig(figdir / 'HistorischVerloop_{}.png'.format(telpunt), dpi=300)
        dfs.to_csv(figdir / 'HistorischVerloop_{}.csv'.format(telpunt))

        plt.close()

    def plot_countingpoint_YearlyChangesCEMT(self, telpunt='Born sluis'):
        figdir = self.outputdir / 'figures_YearlyChangesCEMT'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting YearlyChangesCEMT voor telpunt: {telpunt}')

        dfs = {}
        for jaar in self.traffic_scenarios.index:
            # Set variables
            referenceSetId = self.traffic_scenarios.loc[jaar, 'reference_trips_sets_id']
            trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
            countingPointName = telpunt

            # Query data
            df = self.countingpoint_CEMT_klasse(referenceSetId, countingPointName, trafficScenarioId)
            if not len(df):
                continue

            dfs[jaar] = df

        if not len(dfs):
            return 'No data'

        dfs = pd.concat(dfs, axis=1, sort=False)
        dfs = dfs.reindex(index=[o for o in self.cemt_order if o in dfs.index])

        # Plot data
        dfs.T.plot.bar(figsize=(6, 6), width=0.75, stacked=True, zorder=3)
        plt.title('{}'.format(telpunt))
        plt.grid()
        plt.ylabel('Aantal passages')
        plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        plt.savefig(figdir / 'HistorischVerloopYearCEMT_{}.png'.format(telpunt), dpi=300, bbox_inches='tight')
        dfs.to_csv(figdir / 'HistorischVerloopYearCEMT_{}.csv'.format(telpunt))

        plt.close()

    def export_node_stats_shapefile(self, jaar):
        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']
        nodes = self.network_nodes()
        stats = self.node_statistics_all(trafficScenarioId)

        nodes_stats = nodes.join(stats)

        outputfile_csv = self.outputdir / f'node_statistics_{jaar}.csv'
        outputfile_shp = self.outputdir / f'node_statistics_{jaar}.shp'
        nodes_stats.to_csv(outputfile_csv)
        nodes_stats.to_file(outputfile_shp)



    def plot_node_timeseries(self, jaar=2011, NodeID=21639, label=None):
        """
        Create timeserie of the number of ships departing and arriving at given node in given year.

        jaar: labeled traffic scenario
        nodeId: Node in BIVAS
        label: give label for plot and file. Leave empty to autogenerate label from neighbouring arc

        """
        figdir = self.outputdir / 'figures_timeseries_node'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting timeseries_node voor node: {NodeID}, jaar: {jaar}')

        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']

        # Query data
        df = self.node_timeseries(NodeID, trafficScenarioId)
        if df is None:
            return 'No data'

        # Format
        rename_mapper = {'Origin': 'Herkomst', 'Destination': 'Bestemming'}
        df = df.rename(mapper=rename_mapper, axis=1).reindex(rename_mapper.values(), axis=1)

        if not label:
            label = self.node_label(NodeID)

        # Plot
        df.plot(kind='area', stacked=True, figsize=(16, 6))
        plt.title(f'Locatie: {label}, jaar: {jaar}')
        plt.grid()
        plt.ylabel('Aantal schepen')
        plt.ylim(bottom=0)

        plt.savefig(figdir / f'TijdserieNode_{NodeID}_{label}_{jaar}.png', dpi=300, bbox_inches='tight')
        df.to_csv(figdir / f'TijdserieNode_{NodeID}_{label}_{jaar}.csv')

        plt.close()

    def plot_zone_timeseries(self, jaar, zone_name):
        """
        Create timeserie of the number of ships departing and arriving at given node in given year.

        jaar: labeled traffic scenario
        zone

        """
        figdir = self.outputdir / 'figures_timeseries_zone'
        if not figdir.exists():
            figdir.mkdir()

        logger.info(f'Plotting timeseries_node voor zone: {zone_name}, jaar: {jaar}')

        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']

        # Query data
        df = self.zone_timeseries(zone_name, trafficScenarioId)
        if df is None:
            return 'No data'

        # Format
        rename_mapper = {'Origin': 'Herkomst', 'Destination': 'Bestemming'}
        df = df.rename(mapper=rename_mapper, axis=1).reindex(rename_mapper.values(), axis=1)

        # Plot
        df.plot(kind='area', stacked=True, figsize=(16, 6))
        plt.title(f'Locatie: {zone_name}, jaar: {jaar}')
        plt.grid()
        plt.ylabel('Aantal schepen')
        plt.ylim(bottom=0)

        zone_name = zone_name.replace('/', '-')
        plt.savefig(figdir / f'TijdserieZone_{zone_name}_{jaar}.png', dpi=300, bbox_inches='tight')
        df.to_csv(figdir / f'TijdserieZone_{zone_name}_{jaar}.csv')

        plt.close()

    def plot_nodezone_piechart(self, groupby='NSTR', jaar=2011, NodeID=None, zone_name=None, label=None,
                               zone_definition='BasGoed 2018', directions=['Origin', 'Destination']):
        """
        Create timeserie of the number of ships departing and arriving at given node in given year.

        jaar: labeled traffic scenario
        nodeId: Node in BIVAS
        label: give label for plot and file. Leave empty to autogenerate label from neighbouring arc
        groupby: 'ship_types' or 'NSTR'
        directions: can be either ['Origin', 'Destination'], ['Origin'] or ['Destination']
        """


        if NodeID is not None:
            figdir = self.outputdir / 'figures_piechart_node'
            logger.info(f'Plotting piechart voor node: {NodeID}, jaar: {jaar}')
        else:
            figdir = self.outputdir / 'figures_piechart_zone'
            logger.info(f'Plotting piechart voor zone: {zone_name}, jaar: {jaar}')
        figdir.mkdir(exist_ok=True)


        # Query
        if groupby == 'ship_types':
            groupby_field = 'ship_types.Label'
            groupby_sort = 'CEMTTypeID, ship_types.ID'
        elif groupby == 'NSTR':
            groupby_field = 'nstr_mapping.GroupCode'
            groupby_sort = 'nstr_mapping.GroupCode'
        else:
            logger.error(f'Groupby {groupby} not implemented')
            return

        trafficScenarioId = self.traffic_scenarios.loc[jaar, 'ID']

        if NodeID is not None:
            df = self.node_statistics(NodeID=NodeID, trafficScenarioId=trafficScenarioId, groupby_field=groupby_field,
                                  groupby_sort=groupby_sort, directions=directions)

            if not label:
                label = self.node_label(NodeID)
        else:
            df = self.zone_statistics(zone_name=zone_name, zone_definition=zone_definition,
                                      trafficScenarioId=trafficScenarioId, groupby_field=groupby_field,
                                      groupby_sort=groupby_sort, directions=directions)
            label = zone_name

        if len(df)==0:
            return 'No data'

        # Plot
        # Only label where the bin is larger than 5%
        only_large_labels = [k if v / df.max() > 0.03 else '' for k, v in df.iteritems()]

        df.plot.pie(wedgeprops={'width': 1.0, 'edgecolor': 'w'}, labels=only_large_labels, counterclock=False, startangle=90,
                    cmap='tab20c')
        plt.ylabel('')
        plt.title(f'Scheepvaart van en naar: {label}')



        if NodeID is not None:
            plt.savefig(figdir / f'PiechartNode_{NodeID}_{label}_{groupby}_{jaar}.png', dpi=300, bbox_inches='tight')
            df.to_csv(figdir / f'PiechartNode_{NodeID}_{label}_{groupby}_{jaar}.csv', header=False)
        else:
            zone_name = zone_name.replace('/', '-')
            plt.savefig(figdir / f'PiechartZone_{zone_name}_{groupby}_{jaar}.png', dpi=300, bbox_inches='tight')
            df.to_csv(figdir / f'PiechartZone_{zone_name}_{groupby}_{jaar}.csv', header=False)

        plt.close()

    def plot_all(self):
        countingPoints = self.countingpoint_list()
        zones = self.zone_list()['Name']
        nodes = self.network_nodes().index
        years = self.traffic_scenarios.index
        #
        # for c in countingPoints['Name']:
        #     for y in self.traffic_scenarios.index:
        #         # self.plot_countingpoint_timeseries(c, y)
        #         self.plot_countingpoint_timeseries(c, y, param="Totale Vracht (ton)")


        for c in countingPoints['Name']:
            for y in self.traffic_scenarios.index:
                for param in ['Aantal Vaarbewegingen (-)', "Totale Vracht (ton)"]:
                    for opdeling in ['Scheepvaartklasse', 'CEMT-klasse', 'Bestemming', 'Herkomst', None]:  # , 'Vaarrichting'
                        for relatief in [None]:  # , ('2018-03-07', '2018-06-15')
                            self.plot_countingpoint_timeseries_weekly(c, y, param=param, opdeling=opdeling, relatief=relatief)


        #
        # for c in countingPoints['Name']:
        #     for y in self.traffic_scenarios.index:
        #         self.plot_countingpoint_piechart_CEMTclasses(c, y)
        #
        # for c in countingPoints['Name']:
        #     self.plot_countingpoint_montlytimeseries_yearlychanges(c)
        #
        # for c in countingPoints['Name']:
        #     self.plot_countingpoint_YearlyChangesCEMT(c)
        #
        # for y in years:
        #     self.export_node_stats_shapefile(jaar=y)
        #
        # for z in zones:
        #     for y in years:
        #         self.plot_zone_timeseries(jaar=y, zone_name=z)

        # for z in zones:
        #     for y in years:
        #         self.plot_nodezone_piechart(groupby='NSTR', jaar=y, zone_name=z)
        #         self.plot_nodezone_piechart(groupby='ship_types', jaar=y, zone_name=z)
        #
        # for n in nodes:
        #     for y in years:
        #         self.plot_node_timeseries(jaar=y, NodeID=n)
        #
        # for n in nodes:
        #     for y in years:
        #         self.plot_nodezone_piechart(groupby='NSTR', jaar=y, NodeID=n)
        #         self.plot_nodezone_piechart(groupby='ship_types', jaar=y, NodeID=n)
        #


