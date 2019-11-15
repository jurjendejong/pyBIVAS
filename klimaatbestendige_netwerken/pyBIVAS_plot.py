"""
This function contains generic plotting functions to go with the module pyBIVAS
"""

from pyBIVAS import pyBIVAS

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from pathlib import Path
import pandas as pd
import numpy as np


class pyBIVAS_plot(pyBIVAS):
    """
    Append the class pyBIVAS with plotting functions
    """

    outputdir = Path('.')

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

        def plotAllTrips(t, figname):
            plotTrips(t, figname, y_unit='Totale Vaarkosten (EUR)', stacking='NstrTypeCode')
            plotTrips(t, figname, y_unit='Totale Vracht (ton)', stacking='NstrTypeCode')
            plotTrips(t, figname, y_unit='Aantal Vaarbewegingen (-)', stacking='NstrTypeCode')

            plotTrips(t, figname, y_unit='Totale Vaarkosten (EUR)', stacking='appear_description')
            plotTrips(t, figname, y_unit='Totale Vracht (ton)', stacking='appear_description')
            plotTrips(t, figname, y_unit='Aantal Vaarbewegingen (-)', stacking='appear_description')

            plotTrips(t, figname, y_unit='Totale Vaarkosten (EUR)', stacking='Description_CEMT')
            plotTrips(t, figname, y_unit='Totale Vracht (ton)', stacking='Description_CEMT')
            plotTrips(t, figname, y_unit='Aantal Vaarbewegingen (-)', stacking='Description_CEMT')

            plotTrips(t, figname, y_unit='Totale Vaarkosten (EUR)', stacking='Label')
            plotTrips(t, figname, y_unit='Totale Vracht (ton)', stacking='Label')
            plotTrips(t, figname, y_unit='Aantal Vaarbewegingen (-)', stacking='Label')

        plotAllTrips(t, label)


if __name__ == '__main__':
    BIVAS_path = r'p:\11202240-kpp-dp-zoetwater\EffectmoduleScheepvaart\3_BIVAS_simulaties\BIVAS_finished\bivas_ZW_LSM_LT_191701010100_BP18NW01_000010193_REF2017BP18_lsm2bivas_v2018_02.db'

    BIVAS = pyBIVAS_plot()
    BIVAS.connectToSQLiteDatabase(BIVAS_path)
    BIVAS.set_scenario(47)

    BIVAS.outputdir = Path(r'n:\Projects\11203500\11203738\B. Measurements and calculations\WP5 Hoofdvaarwegennet\Scheepvaartmodellering\Python\BIVAS_output\figures')

    arcID = 6332  # Waal, rond Nijmegen

    BIVAS.plot_Trips_Arc(arcID, label='Nijmegen')
