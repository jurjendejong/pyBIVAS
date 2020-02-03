"""
This function contains generic plotting functions to go with the module pyBIVAS
"""

from klimaatbestendige_netwerken.pyBIVAS import pyBIVAS

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from pathlib import Path
import pandas as pd
import numpy as np
import geopandas
import gc
import random

class pyBIVAS_plot(pyBIVAS):
    """
    Append the class pyBIVAS with plotting functions
    """

    outputdir = Path('.')

    # Arcs in BIVAS 4.4
    Arcs = {
        'BovenRijn': 9204,
        'Waal' : 6332,
        'Pannerdensch Kanaal' : 8886,
        'Nederrijn' : 6645,
        'IJssel' :6510,
        'Zuid-Willemsvaart': 9130,
        'Zandmaas' : 7523,
        'Julianakanaal': 8710,
        'Schelde-Rijnkanaal' : 8387,
        'Betuwepand (ARK)' : 6853,
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




    def plot_Trips_Arc(self, arcID, label):
        """
        This function creates multiple barplots of trips passing a given arc as as function on the draft

        :return:
        """
        routes = self.sqlAdvancedRoutes(group_by='TripsID')
        trips_on_arc = self.sqlArcDetails(arcID)

        sql = """SELECT * FROM ship_types"""
        ship_types = self.sql(sql)

        sql = """SELECT * FROM cemt_class ORDER BY Id"""
        cemt_class = self.sql(sql)

        ship_types = ship_types.join(cemt_class.set_index('Id'), on='CEMTTypeID', rsuffix='_CEMT').set_index('Label')

        t = trips_on_arc.join(routes)
        t = t.join(ship_types, on='Label', rsuffix='_ship_types')
        t = t.replace({'NstrTypeCode': self.NSTR_shortnames})

        def plotTrips(t, figname, y_unit='Totale Vaarkosten (EUR)', stacking='NstrTypeCode'):

            # Create pivot table
            bins = np.arange(0, 5, 0.5)
            c = pd.cut(t['Depth__m'], bins)
            t['depth_bin'] = c
            tp = t.pivot_table(values=y_unit, index='depth_bin', columns=stacking, aggfunc='sum')

            # Make labeling more clear
            if y_unit == 'Totale Vaarkosten (EUR)':
                ylabelstring = 'Vaarkosten (mln EUR)'
                titlestring = 'Verhouding Diepgang-Vaarkosten bij {}'.format(figname)
                figtype1 = 'Vaarkosten'
                tp = tp / 1e6
            elif y_unit == 'Totale Vracht (ton)':
                ylabelstring = 'Vervoerde vracht (mln ton)'
                titlestring = 'Verhouding Diepgang-Tonnage bij {}'.format(figname)
                figtype1 = 'Vracht'
                tp = tp / 1e6
            elif y_unit == 'Aantal Vaarbewegingen (-)':
                ylabelstring = y_unit
                titlestring = 'Verhouding Diepgang-Vaarbewegingen bij {}'.format(figname)
                figtype1 = 'Vaarbewegingen'
            else:
                ylabelstring = y_unit
                titlestring = ''

            if stacking == 'NstrTypeCode':
                figtype2 = 'NSTR'
            elif stacking == 'Label':
                figtype2 = 'Scheepvaartklasse'
            elif stacking == 'appear_description':
                figtype2 = 'Vorm'
            elif stacking == 'lengte_bin':
                figtype2 = 'Lengte'
            elif stacking == 'Description_CEMT':
                figtype2 = 'CEMT'
                tp = tp.reindex(cemt_class['Description'], axis=1).dropna(axis=1, how='all')
            else:
                figtype2 = stacking

            tp.plot.bar(stacked=True, width=0.8, zorder=3, colormap='Paired_r')

            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
            plt.grid()
            plt.xlabel('Diepgang (m)')
            plt.ylabel(ylabelstring)
            plt.title(titlestring)
            # plt.gca().yaxis.set_major_formatter(PercentFormatter(xmax=tp.sum().sum()))

            plt.savefig(self.outputdir / 'Verhouding Diepgang-{} op de {}_{}.png'.format(figtype1, figname, figtype2),
                        dpi=300, bbox_inches='tight')
            plt.savefig(self.outputdir / 'Verhouding Diepgang-{} op de {}_{}.svg'.format(figtype1, figname, figtype2),
                        dpi=300, bbox_inches='tight')
            tp.to_csv(self.outputdir / 'Verhouding Diepgang-{} op de {}_{}.csv'.format(figtype1, figname, figtype2))

            plt.close()

        def plotAllTrips(t, label):
            plotTrips(t, label, y_unit='Totale Vaarkosten (EUR)', stacking='NstrTypeCode')
            plotTrips(t, label, y_unit='Totale Vracht (ton)', stacking='NstrTypeCode')
            plotTrips(t, label, y_unit='Aantal Vaarbewegingen (-)', stacking='NstrTypeCode')

            plotTrips(t, label, y_unit='Totale Vaarkosten (EUR)', stacking='appear_description')
            plotTrips(t, label, y_unit='Totale Vracht (ton)', stacking='appear_description')
            plotTrips(t, label, y_unit='Aantal Vaarbewegingen (-)', stacking='appear_description')

            plotTrips(t, label, y_unit='Totale Vaarkosten (EUR)', stacking='Description_CEMT')
            plotTrips(t, label, y_unit='Totale Vracht (ton)', stacking='Description_CEMT')
            plotTrips(t, label, y_unit='Aantal Vaarbewegingen (-)', stacking='Description_CEMT')

            plotTrips(t, label, y_unit='Totale Vaarkosten (EUR)', stacking='Label')
            plotTrips(t, label, y_unit='Totale Vracht (ton)', stacking='Label')
            plotTrips(t, label, y_unit='Aantal Vaarbewegingen (-)', stacking='Label')

        plotAllTrips(t, label)

    def plot_Vrachtanalyse(self):
        df = self.sqlAdvancedRoutes(group_by='NSTR')

        for c in [c for c in df.columns if 'Totale' in c]:
            d = c.replace('Totale', 'Gemiddelde')
            df[d] = df[c] / df['Aantal Vaarbewegingen (-)']

        dfnormed = df / df.sum()
        dfnormed.loc[:,['Aantal Vaarbewegingen (-)',
               'Totale Reistijd (min)', 'Totale Vaarkosten (EUR)',
               'Totale Afstand (km)', 'Totale TonKM (TONKM)', 'Totale Vracht (ton)', 'Totale TEU (-)']].plot(kind='bar',figsize=(16,4), zorder=3, width=0.8)
        plt.ylabel('Relatieve verdeling')
        plt.legend(loc='center left', bbox_to_anchor=(1.0, 0.5))
        plt.xlabel('')
        plt.title('Verdeling van verschillende commodity')
        plt.ylim(0,0.5)
        plt.grid()
        plt.savefig(self.outputdir / 'Relatieve verdeling per commodity', kind='png', dpi=300,bbox_inches='tight')

        # For each commodity how much tons per ship?
        df['Gemiddelde Vracht (ton)'].plot(kind='bar',figsize=(12,4), zorder=3, color='C0')
        plt.grid()
        plt.ylabel('Gemiddelde belading (tons)')
        plt.savefig(self.outputdir / 'Gemiddelde belading per commodity',kind='png',dpi=300,bbox_inches='tight')
        plt.close()

        df['Totale Vracht (ton)'].plot(kind='bar',figsize=(12,4), color='C1', zorder=3)
        plt.grid()
        plt.ylabel('Totale vracht (tons)')
        plt.savefig(self.outputdir / 'Totale vracht per commodity',kind='png',dpi=300,bbox_inches='tight')
        plt.close()

        df['Totale Vaarkosten (EUR)'].plot(kind='bar',figsize=(12,4), color='C2', zorder=3)
        plt.grid()
        plt.ylabel('Totale kosten (EUR)')
        plt.savefig(self.outputdir / 'Totale kosten per commodity',kind='png',dpi=300,bbox_inches='tight')
        plt.close()

        df['Kosten per ton'] = df['Totale Vaarkosten (EUR)'] / df['Totale Vracht (ton)']
        df['Kosten per ton'].plot(kind='bar',figsize=(12,4),color='C3', zorder=3)
        plt.grid()
        plt.ylabel('Kosten per ton (EUR / ton)')
        plt.savefig(self.outputdir / 'Kosten per ton per commodity',kind='png',dpi=300,bbox_inches='tight')
        plt.close()

        df['Gemiddelde TEU (-)'].plot(kind='bar',figsize=(12,4),color='C4', zorder=3)
        plt.grid()
        plt.ylabel('Gemiddeld TEU')
        plt.savefig(self.outputdir / 'Gemiddeld TEU per commodity', kind='png',dpi=300,bbox_inches='tight')
        plt.close()


    def plot_vergelijking_vaarwegen(self):
        # SQL kosten en trips voor alle trips die langs een opgegeven Arc komen
        dfArcs={}
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


            dfArcs[Arc]=self.sql(sql)
            dfArcs[Arc]=dfArcs[Arc].replace({'NstrTypeCode': self.NSTR_shortnames})
            dfArcs[Arc]=dfArcs[Arc].set_index('NstrTypeCode')

        dfArcs = pd.concat(dfArcs,axis=1)
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

        (dfArcs['Totale Vaarkosten'] / 1e9).transpose().plot(kind='barh',stacked=True,figsize=(14,8), zorder=3, cmap='tab20c')
        plt.grid()
        plt.xlabel('totale vaarkosten (miljarden EUR)')
        plt.legend(loc=1,frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.xlim(0,2.5)
        plt.savefig(self.outputdir / 'Aandeel totale kosten per vaarweg',kind='png',dpi=300,bbox_inches='tight')

        (dfArcs["Totale Vracht"] / 1e6).transpose().plot(kind='barh',stacked=True,figsize=(14,8), zorder=3, cmap='tab20c')
        plt.grid()
        plt.xlabel('totale vracht (mln ton)')
        plt.legend(loc=1,frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.savefig(self.outputdir / 'Aandeel vracht per vaarweg' ,kind='png',dpi=300,bbox_inches='tight')

        dfArcs["Aantal Vaarbewegingen"].transpose().plot(kind='barh',stacked=True,figsize=(14,8), zorder=3, cmap='tab20c')
        plt.grid()
        plt.xlabel('Aantal vaarbewegingen')
        plt.legend(loc=1,frameon=True)
        plt.gca().invert_yaxis()
        plt.gca().get_yticklabels()[-1].set_weight("bold")
        plt.axhline(len(self.Arcs) - 0.5, c='k', ls='--')
        plt.savefig(self.outputdir / 'Aantal vaarbewegingen per vaarweg', kind='png',dpi=300,bbox_inches='tight')


    def plot_vergelijking_trafficScenario(self, trafficScenarios: list):
        sql = f"""
        SELECT
        SUM(NumberOfTrips) as nTrips,
        SUM(TotalWeight__t * NumberOfTrips) as totalWeight,
        NstrTypeCode,
        traffic_scenarios.Description AS Scheepvaartbestand
        from trips
        LEFT JOIN traffic_scenarios ON TrafficScenarioID = traffic_scenarios.ID
        WHERE TrafficScenarioID IN ({', '.join(trafficScenarios)})
        GROUP BY NstrTypeCode, Scheepvaartbestand
        """
        df = self.sql(sql)
        df = df.replace({'NstrTypeCode': self.NSTR_shortnames})
        df.head()

        ## Vaarbewegingen

        df_pivot = df.pivot_table(columns='Scheepvaartbestand', index='NstrTypeCode', values='nTrips')
        df_pivot = df_pivot.reindex(columns=['WLO_2014', 'WLO_2050L', 'WLO_2050H'])
        df_pivot.index.name = ''

        df_pivot.plot.bar(figsize=(12,4), zorder=3)
        plt.grid()
        plt.title('Toename in aantal vaarbewegingen in WLO2050')
        plt.ylabel('Vaarbewegingen (-)')
        plt.savefig(self.outputdir / 'WLO2050H_ToenameVaarbewegingen.png', dpi=150, bbox_inches='tight')
        df_pivot.to_csv(self.outputdir / 'WLO2050H_ToenameVaarbewegingen.csv')

        ## Vracht

        df_pivot = df.pivot_table(columns='Scheepvaartbestand', index='NstrTypeCode', values='totalWeight')
        df_pivot = df_pivot.reindex(columns=['WLO_2014', 'WLO_2050L', 'WLO_2050H'])
        df_pivot.index.name = ''

        df_pivot = df_pivot / 1e6

        df_pivot.plot.bar(figsize=(12,4), zorder=3)
        plt.grid()
        plt.title('Toename in vracht in WLO2050')
        plt.ylabel('Vracht (miljoen ton)')
        plt.savefig(self.outputdir / 'WLO2050H_ToenameVracht.png', dpi=150, bbox_inches='tight')
        df_pivot.to_csv(self.outputdir / 'WLO2050H_ToenameVracht.csv')



    def plot_Beladingsgraad(self):
        df = pd.read_excel('Vaarbewegingen_Nijmegen.xlsx')
        df['Beladingsgraad'] = df['TotalWeight__t'] / df['LoadCapacity__t']
        bins = np.linspace(-0.000001,1.1,23)
        df['Beladingsgraad_bins'] = pd.cut(df['Beladingsgraad'], bins)

        df_pivot = df.pivot_table(index='Beladingsgraad_bins', columns='appear_description', values='NumberOfTrips', aggfunc='sum')
        df_pivot.columns.name = 'Vorm'
        df_pivot.index = np.round((bins[1:] + bins[:-1]) /2,3)
        df_pivot = df_pivot.fillna(0)

        df_pivot.plot.bar(stacked=True, width=0.9, zorder=3)

        plt.ylim(top=8000)
        plt.ylabel('Aantal vaarbewegingen')
        plt.xlabel('Beladingsgraad')
        plt.grid()
        plt.legend(loc=6, bbox_to_anchor=(1,0.5))
        plt.xticks(np.arange(-0.5,21.51,2), np.round(np.arange(0,1.2,0.1),1))

        plt.annotate(f'{df_pivot.sum(axis=1)[0.025]:.0f}', xy=(0.025, 8000), xytext=(30, -50), textcoords='offset points',
                    arrowprops=dict(arrowstyle="->"),
                    )

        plt.savefig(self.outputdir / f'Beladingsgraad.png', dpi=300, bbox_inches='tight')
        plt.savefig(self.outputdir / f'Beladingsgraad.svg', bbox_inches='tight')

# if __name__ == '__main__':
    # BIVAS_path = r'p:\11202240-kpp-dp-zoetwater\EffectmoduleScheepvaart\3_BIVAS_simulaties\BIVAS_finished\bivas_ZW_LSM_LT_191701010100_BP18NW01_000010193_REF2017BP18_lsm2bivas_v2018_02.db'

    # BIVAS = pyBIVAS_plot()
    # BIVAS.connectToSQLiteDatabase(BIVAS_path)
    # BIVAS.set_scenario(47)

    # BIVAS.outputdir = Path(r'n:\Projects\11203500\11203738\B. Measurements and calculations\WP5 Hoofdvaarwegennet\Scheepvaartmodellering\Python\BIVAS_output\figures')

    # arcID = 6332  # Waal, rond Nijmegen

    # BIVAS.plot_Trips_Arc(arcID, label='Nijmegen')
