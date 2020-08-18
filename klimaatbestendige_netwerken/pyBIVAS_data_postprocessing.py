from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.colors import SymLogNorm
from klimaatbestendige_netwerken.pyBIVAS_KBN_plots import read_scenarios

# These are not really classes but I used it to group the functions..
class infeasible_trips:

    @staticmethod
    def compute_all_infeasible_trips(T, IT, Qref, relaxation_per_trip=None, max_distance=2, max_time=3,
                                     max_abs_costs=3, max_rel_costs=5, manual=None):
        """

        :param T: Trips data
        :param IT: Infeasible trips data
        :param Qref
        :param relaxation_per_trip
        :param max_distance:
        :param max_time:
        :param max_abs_costs:
        :param max_rel_costs:
        :return:
        """

        # De relatieve beladingsgraad kleiner dan berekend door BIVAS
        IT_relbeladingsgraad = ~IT.xs('Aantal Vaarbewegingen (-)', axis=1, level=1).isna()
        IT_relbeladingsgraad.sum()

        # Max distance
        IT_distance = {}
        for Q in T.columns.levels[0]:
            IT_distance[Q] = T[Q]['Distance__km'] / T[Qref]['Distance__km'] > max_distance
        IT_distance = pd.concat(IT_distance, axis=1)

        # Max time
        IT_time = {}
        for Q in T.columns.levels[0]:
            IT_time[Q] = T[Q]['TravelTime__min'] / T[Qref]['TravelTime__min'] > max_time
        IT_time = pd.concat(IT_time, axis=1)

        # Max abs costs
        IT_costs_abs = {}
        for Q in T.columns.levels[0]:
            IT_costs_abs[Q] = \
                (T[Q]['FixedCosts__Eur'] + T[Q]['VariableDistanceCosts__Eur'] + T[Q]['VariableTimeCosts__Eur']) / \
                (T[Qref]['FixedCosts__Eur'] + T[Qref]['VariableDistanceCosts__Eur'] + T[Qref]['VariableTimeCosts__Eur']) \
                > max_abs_costs
        IT_costs_abs = pd.concat(IT_costs_abs, axis=1)

        # Max rel costs
        IT_costs_rel = {}
        for Q in T.columns.levels[0]:
            IT_costs_rel[Q] = \
                (T[Q]['Totale Variabele Vaarkosten (EUR)'] / T[Q]['Totale Vracht (ton)']) / \
                (T[Qref]['Totale Variabele Vaarkosten (EUR)'] / T[Qref]['Totale Vracht (ton)']) \
                > max_rel_costs
        IT_costs_rel = pd.concat(IT_costs_rel, axis=1)

        # Combine criteria
        criteria_combined = {
            'Rel beladingsgraad': IT_relbeladingsgraad,
            'Distance': IT_distance,
            'Time': IT_time,
            'Costs abs': IT_costs_abs,
            'Costs rel': IT_costs_rel,
        }

        if relaxation_per_trip is not None:
            delta_relaxation_per_trip = relaxation_per_trip.subtract(relaxation_per_trip[Qref], axis=0)

            infeasible_relaxation = (delta_relaxation_per_trip > 1e5)

            criteria_combined['Relaxation'] = infeasible_relaxation

        if manual is not None:
            criteria_combined['Manual'] = manual

        IT_combined = pd.concat(criteria_combined, axis=1)

        IT_combined = IT_combined.fillna(False)
        IT_combined = IT_combined[IT_combined.any(axis=1)]

        # All trips that should be ignored because it's infeasible in all simulations
        TripID_always_infeasible = pd.concat([
            IT_combined[IT_combined['Rel beladingsgraad'].all(axis=1)],
        ]).index
        always_infeasible = pd.Series(TripID_always_infeasible)

        all_infeasible = IT_combined.any(axis=1, level=1)

        return IT_combined, always_infeasible, all_infeasible

    @staticmethod
    def trips_below_abs_beladingsgraad(T, min_abs_beladingsgraad=0.20):
        IT_absbeladinggraad_drogebulk = {}
        IT_absbeladinggraad_nattebulk = {}

        for Q in T.columns.levels[0]:
            beladingsgraad = T[Q, 'Beladingsgraad']
            vorm = T[Q, 'Vorm']

            IT_absbeladinggraad_drogebulk[Q] = (vorm == 'Droge bulk') & (beladingsgraad < min_abs_beladingsgraad)
            IT_absbeladinggraad_nattebulk[Q] = (vorm == 'Natte bulk') & (beladingsgraad < min_abs_beladingsgraad)

        IT_absbeladinggraad_drogebulk = pd.concat(IT_absbeladinggraad_drogebulk, axis=1)
        IT_absbeladinggraad_nattebulk = pd.concat(IT_absbeladinggraad_nattebulk, axis=1)

        IT_absbeladinggraad = pd.concat({
            'drogebulk': IT_absbeladinggraad_drogebulk,
            'nattebulk': IT_absbeladinggraad_nattebulk
        }, axis=1).any(axis=1, level=1)

        Beladingsgraad_below_criteria = IT_absbeladinggraad[IT_absbeladinggraad.any(axis=1)]
        return Beladingsgraad_below_criteria


class increase_empty_trips:

    @staticmethod
    def relatieve_toename_lege_vaarbewegingen(REF, Q):
        """
        Bereken de toename van het aantal lege vaarbewegingen op basis van de toename in het aantal volle vaarbewegingen

        Hierbij wordt uitgegaan van een gelijke verhouding vol-leeg voor iedere corridor+cemt-klasse.

        REF: dataframe van trips
        Q: dataframe van trips

        """
        # Create copy to prevent changing the original data
        REF = REF.copy()
        Q = Q.copy()

        # Group by corridor and CEMT-class
        REF = REF.groupby(['Vorm', 'cemt_class_Description', 'Origin_Zone', 'Destination_Zone'])
        Q = Q.groupby(['Vorm', 'cemt_class_Description', 'Origin_Zone', 'Destination_Zone'])

        # Only count on number of trips
        Q = Q['Aantal Vaarbewegingen (-)']
        REF = REF['Aantal Vaarbewegingen (-)']

        # Sommering per groep; pivot; sorteren
        REF = REF.sum().unstack(level=[1, 0]).sort_index(axis=1)
        Q = Q.sum().unstack(level=[1, 0]).sort_index(axis=1)

        # Relatieve toename van alle niet-lege schepen
        relatieve_toename = Q.drop('Leeg', axis=1, level=1).sum(axis=1, level=0) / REF.drop('Leeg', axis=1,
                                                                                            level=1).sum(
            axis=1, level=0)
        relatieve_toename = relatieve_toename.fillna(1)

        return relatieve_toename

    @staticmethod
    def plot_and_save_relatieve_toename(relatieve_toename, s, outputdir):
        relatieve_toename.to_pickle(outputdir / f'Toename_lege_vaarbewegingen_{s}.pkl')
        relatieve_toename.to_excel(outputdir / f'Toename_lege_vaarbewegingen_{s}.xlsx')

        per_corridor = (relatieve_toename.sum(axis=1) / relatieve_toename.count(axis=1)).unstack().fillna(1).T
        f, ax = plt.subplots(figsize=(16, 16))
        sns.heatmap(per_corridor, ax=ax, vmin=1, vmax=1.5, norm=SymLogNorm(1), cbar=True, cmap='viridis')

        plt.savefig(outputdir / f'Toename_lege_vaarbewegingen_{s}_heatmap_corridors.png', dpi=300, bbox_inches='tight')
        per_corridor.to_csv(outputdir / f'Toename_lege_vaarbewegingen_{s}_heatmap_corridors.csv')
        plt.close()

        per_cemt = relatieve_toename.sum() / relatieve_toename.count()
        per_cemt.plot.bar(width=0.9, zorder=3)
        plt.ylim(0.9, 1.2)
        plt.ylabel('Relatieve toename aantal vaarbewegingen')
        plt.xlabel('CEMT-klasse')
        plt.grid()
        per_cemt.to_csv(outputdir / f'Toename_lege_vaarbewegingen_{s}_bar_cemtklasse.csv', header=None)
        plt.savefig(outputdir / f'Toename_lege_vaarbewegingen_{s}_bar_cemtklasse.png', dpi=300, bbox_inches='tight')
        plt.close()

    # This function can be used in other scripts
    @staticmethod
    def adjust_trips_lege_schepen(df, s):
        """
        Het toepassen van een lookup table met de relatieve vaarbewegingen (per corridor, en cemt-klasse) op alle trips


        df: dataframe van trips om de toename op toe te passen
        s: name of scenario to load

        """

        df = df.copy()

        ii = df['Vorm'] == 'Leeg'
        df_Leeg = df.loc[ii, ['Origin_Zone', 'Destination_Zone', 'cemt_class_Description']]

        # For each 'leeg' trip in list get the relatieve toename
        toename_per_trip = pd.read_pickle(f'../1_Output_conversion/Lege schepen/Toename_lege_vaarbewegingen_{s}.pkl')
        toename_per_trip = toename_per_trip.stack().reindex(df_Leeg.values)

        # Adjust these columns
        for c in ['NumberOfTrips', 'Aantal Vaarbewegingen (-)', 'Totale Reistijd (min)', 'Totale Vaarkosten (EUR)',
                  'Totale Variabele Vaarkosten (EUR)',
                  'Totale Variabele-Tijd Vaarkosten (EUR)',
                  'Totale Variabele-Afstand Vaarkosten (EUR)',
                  'Totale Vaste Vaarkosten (EUR)', 'Totale Afstand (km)']:
            df.loc[ii, c] *= toename_per_trip.values

        return df




# Minimum example to compute infeasible trips
if __name__ == "__main__":
    scenarios_Q = ['Q1020', 'Q1800']
    Qref = 'Q1800'

    # Read data
    IT = read_scenarios('infeasibletrips.pkl', scenarios_Q, addcolumns=False, dropinfeasible=False, increaseemptytrips=False)
    T = read_scenarios('routestatistics_alltrips.pkl', scenarios_Q, addcolumns=False, dropinfeasible=False, increaseemptytrips=False)

    # Compute infeasible
    always_infeasible, all_infeasible = infeasible_trips.compute_all_infeasible_trips(T, IT, Qref=Qref)
    Beladingsgraad_below_criteria = infeasible_trips.trips_below_abs_beladingsgraad(T)



# Minimum example to compute empty vessels
if __name__ == "__main__":

    scenarios_Q = ['Q1020', 'Q1800']
    Qref = 'Q1800'

    # Read data
    T = read_scenarios('routestatistics_alltrips.pkl', scenarios_Q, increaseemptytrips=False, addcolumns=False)

    # Compute
    for s in scenarios_Q:
        relatieve_toename = increase_empty_trips.relatieve_toename_lege_vaarbewegingen(T[Qref], T[s])
        increase_empty_trips.plot_and_save_relatieve_toename(relatieve_toename, s)

    # Test to apply the newly create files
    s = 'Q1020'
    Q = increase_empty_trips.adjust_trips_lege_schepen(T[s], s)
