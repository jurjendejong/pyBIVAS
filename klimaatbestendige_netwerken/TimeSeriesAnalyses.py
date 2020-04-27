"""
This script includes combines a couple of functions for time-series analysis.
All script require Pandas Series or DataFrames as input

Developed for usage in Klimaat Bestendige Netwerken, Rijkswaterstaat.

Jurjen de Jong, Deltares, 17-10-2019
"""

import pandas as pd
from pandas.core.frame import DataFrame
import numpy as np
import logging
import matplotlib.pyplot as plt
from pathlib import Path

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)


class ExceedanceLevels:
    return_periods_active = False
    T = None

    def __init__(self, timeseries: DataFrame, levels: list, outputfolder=Path('Figuren')):
        """

        :param timeseries: Pandas DataFrame (time-series)
        :param levels: list of levels
        :return:
        """

        self.outputfolder = outputfolder

        df = pd.DataFrame(index=levels, )
        df.index.name = 'Afvoerniveau'

        for scenario in timeseries:
            logger.info(f'Computing exceedance_levels for scenario: {scenario}')
            df[scenario] = _get_frequency_below_levels(timeseries[scenario], levels)

        self.df = df
        self.df.to_excel(self.outputfolder / 'Non_exceedance.xlsx')

        # And per year
        df_year = {}
        for scenario in timeseries:
            logger.info(f'Computing exceedance_levels per year for scenario: {scenario}')
            df_year[scenario] = _get_frequency_below_levels_per_year(timeseries[scenario], levels)

        self.df_year = df_year
        pd.concat(df_year, axis=1).stack(level=0).to_excel(self.outputfolder / 'Non_exceedance_yearly.xlsx')

    def sort_df_year_by_one_level(self, level):
        """
        Sort the dataframe by one level
        :param level: FLOAT, level to sort on. Must already exist in levels from init
        :return:
        """
        for scenario in self.df_year:
            self.df_year[scenario].sort_values(axis=1, by=level, inplace=True)

    def sort_df_year_by_all_levels(self, return_period=False):
        """
        Sort the dataframe by all levels individualy. The link to real years gets lost, so the axis is renamed

        :param return_period: BOOL, translates the axis to a return period
        :return:
        """
        for scenario in self.df_year:
            df = self.df_year[scenario]
            for level in df.index:
                df.loc[level] = df.loc[level].sort_values().values[:]

            df.columns = np.arange(101, 0, -1)

            if return_period:
                n_years = df.shape[1]
                df.columns = 1 / (df.columns / n_years)

                self.return_periods_active = True
                df.to_csv(self.outputfolder / f'Return_period_{scenario}.csv')

            self.df_year[scenario] = df

    def interpolate_return_period(self, return_period_levels: list, include_average=True):
        """
        Function to interpolate the discharge_levels of the earlier imported years to given return periods

        :param return_period_levels: LIST, array of return periods
        :param include_average: BOOL, where or not to include the average year to compare to the return periods
        :return:
        """
        if not self.return_periods_active:
            logger.error('Return periods should be computed first using sort_df_year_by_all_levels(return_period=True)')
            return

        df = self.df
        ret_period = {}
        for scenario in self.df_year:
            df_year = self.df_year[scenario]
            df_karakterstiek = pd.DataFrame(index=df.index, columns=return_period_levels)
            for l in df.index:
                df_karakterstiek.loc[l, :] = np.interp(return_period_levels, df_year.columns, df_year.loc[l])

            if include_average:
                df_karakterstiek['Gemiddeld'] = df[scenario]  # Toevoegen gemiddelde ter vergelijking

            ret_period[scenario] = df_karakterstiek

        self.T = pd.concat(ret_period, axis=1)
        self.T.to_excel(self.outputfolder / 'Return_periods.xlsx')

    def barplot_exceedance_levels(self, unit_days=True, include_full=True, yearplot_scenario=None,
                                  return_period_scenario=False, addvalues=False):
        """
        Script to make all barplots with exceedance levels
        :param unit_days: BOOL, scale from 0 to 1, or 0 to 365
        :param include_full: BOOL, include the 100% level
        :param yearplot_scenario: STR, to plot the yearplot of the given scenario
        :param return_period_scenario: STR, to plot the return_period plot for given scenario
        :param addvalues: BOOL, write values in the graph

        yearplot_scenario and return_period_scenario cannot be combined
        """

        if yearplot_scenario:
            df = self.df_year[yearplot_scenario].copy()
        elif return_period_scenario:
            if return_period_scenario in self.T.columns.levels[1]:
                df = self.T.xs(return_period_scenario, axis=1, level=1).copy()
                return_period_scenario = f'T{return_period_scenario}'
            else:
                df = self.T[return_period_scenario].copy()
        else:
            df = self.df.copy()

        levels = df.index
        labels_diff = [f'{t1} tot {t2} $m^3/s$' for t1, t2 in zip(levels[:-1], levels[1:])]
        labels_diff.insert(0, f'Tot {levels[0]} $m^3/s$')

        if include_full:
            labels_diff.append(f'Groter dan {levels[-1]} $m^3/s$')
            df.loc[np.inf] = 1
        df_diff = df.diff()
        df_diff.iloc[0, :] = df.iloc[0, :]
        df_diff.index = labels_diff

        if unit_days:
            df_diff = df_diff * 365
            df = df * 365

        if not yearplot_scenario:
            df_diff.T.plot(kind='bar', stacked=True, figsize=(4, 5), colormap='plasma', zorder=3, width=0.7)
        else:
            df_diff.T.plot(kind='bar', stacked=True, figsize=(20, 5), colormap='plasma', zorder=3)

        if addvalues:
            for ii, c in enumerate(df.columns):
                for i in df.index:
                    v = df.loc[i, c]
                    if v < 1 or v > 364:
                        continue
                    plt.text(ii, v, f'{v:.0f}', va='bottom', ha='center')

        if 'Gemiddeld' in df:
            plt.axvline(len(df.columns) - 1.5, color='k', linestyle='-.')

        if unit_days:
            plt.ylabel('Dagen per jaar')
            plt.ylim(0, 1.01 * 365)
        else:
            plt.ylabel('Onderschrijdingskans')
            plt.ylim(0, 1.01)
        plt.legend(loc=6, bbox_to_anchor=(1, 0.5))
        plt.grid()

        if yearplot_scenario:
            plt.title(f'100-jarige reeks - {yearplot_scenario}')
        elif return_period_scenario:
            plt.title(f'Karakteristieke jaren - {return_period_scenario}')
        else:
            plt.title(f"Gemiddeld jaar in klimaatscenario's")

    def plot_return_period(self, yearplot_scenario):

        df = self.df_year[yearplot_scenario].copy()

        levels = df.index
        labels_diff = [f'{t} $m^3/s$' for t in levels]
        df.index = labels_diff
        # Plot van terugkeertijden
        f, ax = plt.subplots(1, 1, figsize=(12, 5))
        (df.T * 365).plot(logx=True, ax=ax, colormap='plasma', marker='o', markersize=2)

        plt.xlabel('Herhalingstijd')
        plt.ylim(0, 1.01 * 365)
        plt.xlim(1, 100)
        plt.grid(True, 'both')
        plt.ylabel('Dagen onderschrijding')
        plt.legend(loc=6, bbox_to_anchor=(1, 0.5))
        ax.set_xticklabels([0, 1, 10, 100])
        plt.title(f'Terugkeertijd - {yearplot_scenario}')

    def plot_return_period_perLevel(self, level):

        d = {}
        for s in self.df_year:
            d[s] = self.df_year[s].loc[level]
        df = pd.concat(d, axis=1)

        # Plot van terugkeertijden
        f, ax = plt.subplots(1, 1, figsize=(12, 5))
        (df * 365).plot(logx=True, ax=ax, marker='o', markersize=2)

        plt.xlabel('Herhalingstijd')
        plt.ylim(0, 1.01 * 365)
        plt.xlim(1, 100)
        plt.grid(True, 'both')
        plt.ylabel('Dagen onderschrijding')
        plt.legend(loc=6, bbox_to_anchor=(1, 0.5))
        ax.set_xticklabels([0, 1, 10, 100])
        plt.title(f'Terugkeertijd - {level} $m^3/s$')


# Private functions

def _get_frequency_below(df, threshold):
    """Return the fraction of the dataframe where the value is lower than the threshold"""
    return len(df[df < threshold]) / len(df)


def _get_frequency_below_levels(series, levels):
    freq = [_get_frequency_below(series, l) for l in levels]
    return freq


def _get_frequency_below_levels_per_year(series, levels):
    c = series.groupby(series.index.year)
    values = [c.agg(_get_frequency_below, l) for l in levels]
    df = pd.DataFrame(values, index=levels)
    return df
