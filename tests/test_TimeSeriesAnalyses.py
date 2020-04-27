from klimaatbestendige_netwerken.TimeSeriesAnalyses import TimeSeriesAnalyses as TSA
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import unittest


class test_TimeSeriesAnalyses(unittest.TestCase):

    def test_001(self):

        excelfile = Path('resources') / 'Modelranden_BP18.xls'
        outputfolder = Path(r'export_TimeSeriesAnalyses_Maas')

        if not excelfile.exists():
            self.skipTest('Inputfile does not exist')

        if not outputfolder.exists():
            outputfolder.mkdir()

        simulations = {
            'Referentie2017': 'Ref',
            'Druk2050': 'GL_2050',
            'Warm2050': 'WH_2050',
            'Druk2085': 'GL_2085',
            'Warm2085': 'WH_2085'
        }

        tstart = '1911'
        tend = '2011'

        def read_BP18(excelfile, sheet_name):
            BP18 = pd.read_excel(excelfile, sheet_name=sheet_name, index_col=0)
            BP18 = BP18[list(simulations.keys())].rename(simulations,
                                                         axis=1)  # selection of scenarios. Asign names of klimaatscenarios
            BP18 = BP18[tstart:tend]  # Time selection
            return BP18

        # BP18_RT = read_BP18(excelfile, sheet_name='Rijntakken_Lobith')
        BP18_MS = read_BP18(excelfile, sheet_name='Maas_Eijsden')

        Timeseries = BP18_MS

        discharge_levels = np.array([10, 25, 50, 100, 200])

        EL = TSA(Timeseries, levels=discharge_levels, outputfolder=outputfolder)
        EL.df.to_csv(outputfolder / f'Gemiddelde_kans_voorkomen.csv')

        # Plot de kans van voorkomen voor ieder jaar
        EL.barplot_exceedance_levels()
        plt.savefig(outputfolder / f'Gemiddeld_jaar.png', dpi=150, bbox_inches='tight')
        plt.savefig(outputfolder / f'Gemiddeld_jaar.svg', bbox_inches='tight')

        # Plot de kans van voorkomen voor ieder jaar
        for scenario in simulations.values():
            EL.barplot_exceedance_levels(yearplot_scenario=scenario)
            plt.savefig(outputfolder / f'Jaarlijks_{scenario}.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Jaarlijks_{scenario}.svg', bbox_inches='tight')

        # Plot van alle jaren gesorteerd op 1 level
        EL.sort_df_year_by_one_level(50)
        EL.barplot_exceedance_levels(yearplot_scenario=scenario)
        plt.title(f'Gesorteerde 100-jarige reeks - {scenario}')
        plt.savefig(outputfolder / f'Jaarlijks_{scenario}_sort_1level.png', dpi=150, bbox_inches='tight')
        plt.savefig(outputfolder / f'Jaarlijks_{scenario}_sort_1level.svg', bbox_inches='tight')

        # Plot van alle levels gesorteerd
        EL.sort_df_year_by_all_levels()
        EL.barplot_exceedance_levels(yearplot_scenario=scenario)
        plt.xlabel('Aantal jaren overschrijding')
        plt.title(f'Gesorteerde 100-jarige reeks - {scenario}')
        plt.savefig(outputfolder / f'Jaarlijks_{scenario}_sort_all.png', dpi=150, bbox_inches='tight')
        plt.savefig(outputfolder / f'Jaarlijks_{scenario}_sort_all.svg', bbox_inches='tight')

        # Plot van terugkeertijden
        EL.sort_df_year_by_all_levels(return_period=True)
        for scenario in Timeseries.columns[:1]:
            plt.close()
            EL.plot_return_period(scenario)
            plt.savefig(outputfolder / f'Terugkeertijd_{scenario}.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Terugkeertijd_{scenario}.svg', bbox_inches='tight')

        # Plot van terugkeertijden
        for level in discharge_levels[:1]:
            plt.close()
            EL.plot_return_period_perLevel(level)
            plt.savefig(outputfolder / f'Terugkeertijd_Q{level}.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Terugkeertijd_Q{level}.svg', bbox_inches='tight')

        # Interpolate de 100 jaar naar enkele karakteristieke terugkeertijden
        T_levels = [1, 2, 10, 100]
        EL.interpolate_return_period(T_levels)

        for scenario in EL.df.columns[:1]:
            EL.barplot_exceedance_levels(return_period_scenario=scenario)
            plt.savefig(outputfolder / f'Karakteristieke_jaren_{scenario}.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Karakteristieke_jaren_{scenario}.svg', bbox_inches='tight')
            plt.close()

        for scenario in EL.df.columns[:1]:
            EL.barplot_exceedance_levels(return_period_scenario=scenario, addvalues=True)
            plt.savefig(outputfolder / f'Karakteristieke_jaren_{scenario}_values.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Karakteristieke_jaren_{scenario}_values.svg', bbox_inches='tight')
            plt.close()

        for scenario in T_levels[:1]:
            EL.barplot_exceedance_levels(return_period_scenario=scenario)
            plt.savefig(outputfolder / f'Karakteristieke_jaren_T{scenario}.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Karakteristieke_jaren_T{scenario}.svg', bbox_inches='tight')
            plt.close()

        for scenario in T_levels[:1]:
            EL.barplot_exceedance_levels(return_period_scenario=scenario, addvalues=True)
            plt.savefig(outputfolder / f'Karakteristieke_jaren_T{scenario}_values.png', dpi=150, bbox_inches='tight')
            plt.savefig(outputfolder / f'Karakteristieke_jaren_T{scenario}_values.svg', bbox_inches='tight')
            plt.close()
