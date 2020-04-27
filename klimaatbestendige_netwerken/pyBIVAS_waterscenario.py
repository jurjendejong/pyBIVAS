"""

This script converts different inputs to a waterscenario for BIVAS

Jurjen de Jong, 24 april 2020

"""

from pathlib import Path
from klimaatbestendige_netwerken.pyBIVAS import pyBIVAS
from klimaatbestendige_netwerken.waterdepthgrid import WaterdepthGrid
from klimaatbestendige_netwerken.externals.SOBEK_to_Pandas import read_nc as read_sobek_nc
from klimaatbestendige_netwerken.externals.dini_to_json_via_xml import ini_to_json
import logging
import numpy as np
import networkx as nx
import pandas as pd
from shapely.ops import nearest_points
from shapely.geometry import Point


class CreateWaterScenario:
    def __init__(self):
        pass

    def load_sobek(self, SOBEK_output_reachsegments: Path, SOBEK_output_gridpoints: Path, SOBEK_network_file: Path,
                   exclude_sobek_reaches_from_network=[]):
        logging.info('Loading SOBEK results')

        self.gridpoints_data, self.gridpoints = read_sobek_nc(SOBEK_output_gridpoints, return_attributes=True)
        self.reachseg_data, self.reachseg = read_sobek_nc(SOBEK_output_reachsegments, return_attributes=True)

        self.gridpoints['branchname'] = self.gridpoints['gridpoint_id'].str.rsplit('_', 1, expand=True)[0]
        self.reachseg['branchname'] = self.reachseg['reach_segment_id'].str.rsplit('_', 1, expand=True)[0]

        logging.info('Create networkx')
        self.sobek_networkx = self.networkx_from_sobek3(SOBEK_network_file, exclude_sobek_reaches_from_network)

        logging.info('Computing stats')

        def sobek_stats(df):
            time_end = df.index[-1]
            time_start = time_end - pd.Timedelta(hours=24, minutes=50)
            df = df.loc[time_start:time_end]

            df_stats = df.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).drop('count').stack().unstack(level=0)
            return df_stats

        self.gridpoint_stats = sobek_stats(self.gridpoints_data)
        self.reachseg_stats = sobek_stats(self.reachseg_data)

    def load_bivas(self, BIVAS_database):
        logging.info('Loading BIVAS network')
        # Read BIVAS-network to networkx
        self.BIVAS = pyBIVAS(BIVAS_database)
        self.BIVAS.set_scenario()
        self.BIVAS_networkx = self.BIVAS.sqlNetworkToNetworkx()
        self.BIVAS_arcs = self.BIVAS.sqlArcs()
        self.BIVAS_nodes = self.BIVAS.sqlNodes()

    def create_mapping(self, bivas_reaches, sobek_reaches):
        logging.info('Creating koppeling')
        koppeling = []
        for reach, (node_start, node_end) in bivas_reaches.items():
            logging.info(f'Branch: {reach}')
            _, bivas_arcs = self.shortestpath(self.BIVAS_networkx, node_start, node_end, weight_col='Length__m',
                                              edge_name='ID')

            SOBEK_node_start, SOBEK_node_end = sobek_reaches[reach]

            _, sobek_branches = self.shortestpath(self.sobek_networkx, SOBEK_node_start, SOBEK_node_end,
                                                  weight_col='length',
                                                  edge_name='id')

            gridpoint_subset = self.gridpoints[self.gridpoints['branchname'].isin(sobek_branches)]
            gridpoint_subset_coordinates = gridpoint_subset[['x_coordinate', 'y_coordinate']].apply(tuple, axis=1)

            reachseg_subset = self.reachseg[self.reachseg['branchname'].isin(sobek_branches)]
            reachseg_subset_coordinates = reachseg_subset[['x_coordinate', 'y_coordinate']].apply(tuple, axis=1)

            for arc in bivas_arcs:
                BIVAS_arc = self.BIVAS_arcs.loc[arc]
                bivas_arcs_center = tuple(BIVAS_arc[['XM', 'YM']])

                closestgridpoint = self.closestpoint(node1=bivas_arcs_center,
                                                     list_node2=list(gridpoint_subset_coordinates),
                                                     labels_node2=gridpoint_subset_coordinates.index)
                closestreachseg = self.closestpoint(node1=bivas_arcs_center,
                                                    list_node2=list(reachseg_subset_coordinates),
                                                    labels_node2=reachseg_subset_coordinates.index)

                koppeling.append({
                    'Branch': arc,
                    'BIVAS_arc_name': BIVAS_arc['Name'],
                    'BIVAS_arc_id': arc,
                    'SOBEK_gridpoint': closestgridpoint,
                    'SOBEK_reachseg': closestreachseg,
                    'koppeling_gridpoint': 'LINESTRING ({b[0]:.0f} {b[1]:.0f}, {s[0]:.0f} {s[1]:.0f})'.format(
                        b=bivas_arcs_center,
                        s=gridpoint_subset_coordinates.loc[closestgridpoint]
                    ),
                    'koppeling_reachseg': 'LINESTRING ({b[0]:.0f} {b[1]:.0f}, {s[0]:.0f} {s[1]:.0f})'.format(
                        b=bivas_arcs_center,
                        s=reachseg_subset_coordinates.loc[closestreachseg]
                    )
                })

        self.mapping = pd.DataFrame(koppeling)
        self.mapping.to_csv('koppeling.csv')

    def mapping_load(self, koppeling_csv):
        # TODO

        self.koppeling = pd.read_csv(koppeling_csv)

    def waterscenario_from_mapping(self):
        logging.info('Apply mapping')
        # Use koppeling

        waterscenario = {}

        for _, mapping_row in self.mapping.iterrows():
            arc = mapping_row['BIVAS_arc_id']
            gridpoint_id = mapping_row['SOBEK_gridpoint']
            reachseg_id = mapping_row['SOBEK_reachseg']

            water_level_cell = self.gridpoint_stats.loc[gridpoint_id, ('water_level', 'max')]
            # water_depth_cell = self.gridpoint_stats.loc[gridpoint_id, ('water_depth', 'max')]
            water_discharge_cell = self.reachseg_stats.loc[reachseg_id, ('water_discharge', 'mean')]
            water_velocity_cell = self.reachseg_stats.loc[reachseg_id, ('water_velocity', 'mean')]

            waterscenario[arc] = {
                'SeasonID': 1,
                'WaterLevel__m': water_level_cell,
                'RateOfFlow__m3_s': water_discharge_cell,
                'WaterSpeed__m_s': water_velocity_cell,
                'WaterDepth__m': np.nan, # water_depth_cell
            }

        self.waterscenario = pd.DataFrame(waterscenario).T
        self.waterscenario.index.name = 'ArcID'
        self.waterscenario['SeasonID'] = self.waterscenario['SeasonID'].astype(int)

        self.waterscenario.to_csv('waterscenario.csv')

    def load_waterdepthgrids(self, gridfiles, waterdepth):
        logging.info('Loading and processing waterlevel grids')

        assert gridfiles.keys() == waterdepth.keys(), 'Should have equal keys'
        datagrids = {}

        for g in waterdepth:
            WD = WaterdepthGrid()
            WD.load_grid(gridfiles[g])

            WD.add_waterdepth(waterdepth[g])

            WD.compute_width_depth_table()
            datagrids[g] = WD

        self.datagrids = datagrids

    def waterdepth_from_grids(self, sections, add_extra_columns=True):
        logging.info('Getting waterdepth from grids')
        # Project results on the grid
        for label, section in sections.items():
            logging.info(f'  {label}')
            # logging.info(f'  {section}')
            df_depth = self.datagrids[section['grid']].compute_depth_forwidth(
                channelwidth=section['channel_width'],
                min_channelwidth=section['min_channel_width'],
                min_channel_depth=section['min_channel_depth']
            )

            # Find current reach
            ii_start = self.nearest_df_row(df_depth, section['point_start'])
            ii_end = self.nearest_df_row(df_depth, section['point_end'])
            reach = df_depth.loc[ii_start: ii_end]

            # Get stats
            min_depth = reach['depth'].min()
            min_width = reach['width'].min()

            # Get list of BIVAS arcs that need to be updated
            BIVAS_node_start = self.nearest_df_row(self.BIVAS_nodes, section['point_start'])
            BIVAS_node_end = self.nearest_df_row(self.BIVAS_nodes, section['point_end'])

            _, bivas_arcs = self.shortestpath(self.BIVAS_networkx, BIVAS_node_start, BIVAS_node_end,
                                              weight_col='Length__m', edge_name='ID')

            for arc in bivas_arcs:
                self.waterscenario.loc[arc, 'WaterDepth__m'] = min_depth

                # Add some extra columns for convenvenience. Should not be loaded to BIVAS
                if add_extra_columns:
                    self.waterscenario.loc[arc, 'Width'] = min_width

                    BIVAS_arc = self.BIVAS_arcs.loc[arc]

                    self.waterscenario.loc[arc, 'geometry'] = \
                        'LINESTRING ({b.X1:.0f} {b.Y1:.0f}, {b.X2:.0f} {b.Y2:.0f})'.format(
                            b=BIVAS_arc
                        )

        self.waterscenario.to_csv('waterscenario.csv')

    @staticmethod
    def networkx_from_sobek3(SOBEK_network_file, exclude_sobek_reaches_from_network=None):
        """
        Build a networkx from a SOBEK3 network file
        Only includes nodes and branches not intermediate gridpoints

        :param SOBEK_network_file:
        :return: networkx
        """
        network_json = ini_to_json(SOBEK_network_file)
        network_pd = pd.DataFrame(network_json['data']['Branch'])
        length = [float(o.split(' ')[-1]) for o in network_pd['gridPointOffsets']]
        network_pd['length'] = length

        network_pd = network_pd[['id', 'fromNode', 'toNode', 'length']]

        network_pd.set_index('id', inplace=True)
        network_pd.drop(exclude_sobek_reaches_from_network, axis=0, inplace=True)

        sobek_networkx = nx.from_pandas_edgelist(
            network_pd.reset_index(), 'fromNode', 'toNode', edge_attr=True)

        # Is this necessary?
        # for n in network_json['data']['Node']:
        #     sobek_networkx.node[n['id']]['X'] = n['x']
        #     sobek_networkx.node[n['id']]['Y'] = n['y']

        return sobek_networkx

    @staticmethod
    def shortestpath(networkx, node_start, node_end, weight_col='Length__m', edge_name='ID'):
        # List of nodes for shortest path
        pathnodes = nx.dijkstra_path(
            networkx, node_start, node_end, weight=weight_col)

        # Name of edges between those nodes
        pathedges = []
        for i in range(len(pathnodes) - 1):
            pathedges.append(
                networkx[pathnodes[i]][pathnodes[i + 1]][edge_name])
        return pathnodes, pathedges

    @staticmethod
    def nearest_df_row(gdf, point):
        queried_geom, nearest_geom = nearest_points(point, gdf.unary_union)
        row_index = gdf.index[gdf['geometry'] == nearest_geom][0]
        return row_index

    @staticmethod
    def closestpoint(node1, list_node2, labels_node2=None):
        from scipy.spatial.distance import cdist
        id = cdist([node1], list_node2).argmin()

        if labels_node2 is None:
            return list_node2[id]
        else:
            return labels_node2[id]


if __name__ == '__main__':
    # from klimaatbestendige_netwerken.pyBIVAS_waterscenario import CreateWaterScenario
    from pathlib import Path

    inputdir = Path(r'../notebooks/waterscenario_input')

    CWS = CreateWaterScenario()

    SOBEK_output_reachsegments = inputdir / 'sobek' / 'output' / '2018' / 'Q1020' / 'reachsegments.nc'
    SOBEK_output_gridpoints = inputdir / 'sobek' / 'output' / '2018' / 'Q1020' / 'gridpoints.nc'
    SOBEK_network_file = inputdir / 'sobek' / 'NetworkDefinition.ini'

    CWS.load_sobek(SOBEK_output_reachsegments, SOBEK_output_gridpoints, SOBEK_network_file,
                   exclude_sobek_reaches_from_network=['VeesWap1', 'Ret_Wilpseklei'])

    BIVAS_database = Path(r'..\..\..\Results\Bivas_2018_v3.db')

    CWS.load_bivas(BIVAS_database)

    sobek_reaches = {
        'Bovenrijn': ('BovenLobith', 'Pannerdenschekop'),
        'Waal': ('Pannerdenschekop', 'Hardinxveldboven'),
        'Pannerdensch Kanaal': ('Pannerdenschekop', 'IJsselkop'),
        'Nederrijn-Lek': ('IJsselkop', 'Ridderkerk'),
        'IJssel': ('IJsselkop', 'IJsselmond')
    }

    bivas_reaches = {
        'Bovenrijn': (150, 6855),
        'Waal': (6855, 7083),
        'Pannerdensch Kanaal': (6855, 6290),
        'Nederrijn-Lek': (6290, 6775),
        'IJssel': (6290, 2065)
    }

    CWS.create_mapping(bivas_reaches, sobek_reaches)

    CWS.waterscenario_from_mapping()

    gridfiles = {
        'Bovenrijn-Waal': inputdir / 'grid' / 'Grid_BR-WL-RD.grd',
        'Pannerdensch Kanaal': inputdir / 'grid' / 'Grid_PK-RD.grd',
        'Nederrijn-Lek': inputdir / 'grid' / 'Grid_NR-LK-RD.grd',
        'IJssel': inputdir / 'grid' / 'Grid_YS-RD.grd',
    }

    # waterdepth = {
    #     'Bovenrijn-Waal': inputdir / 'waterdepth' / '2018' / 'Bovenrijn-Waal' / 'dep_BRWL_rmmRef_Q1020.dep',
    #     'Pannerdensch Kanaal': inputdir / 'waterdepth' / '2018' / 'PannerdenschKanaal' / 'dep_PK_rmmRef_Q1020.dep',
    #     'Nederrijn-Lek': inputdir / 'waterdepth' / '2018' / 'Nederrijn-Lek' / 'dep_NRLK_rmmRef_Q1020.dep',
    #     'IJssel': inputdir / 'waterdepth' / '2018' / 'IJssel' / 'dep_YS_rmmRef_Q1020.dep',
    # }
    waterdepth = {
        'Bovenrijn-Waal': inputdir / 'waterdepth' / 'dep_BRWL_rmmRef_Q1020.dep',
        'Pannerdensch Kanaal': inputdir / 'waterdepth' / 'dep_PK_rmmRef_Q1020.dep',
        'Nederrijn-Lek': inputdir / 'waterdepth' / 'dep_NRLK_rmmRef_Q1020.dep',
        'IJssel': inputdir / 'waterdepth' / 'dep_YS_rmmRef_Q1020.dep',
    }

    CWS.load_waterdepthgrids(gridfiles, waterdepth)


    # Input dict. The key is just convenience and is not used anywhere
    sections = {
        'Boven-Rijn': {
            'point_start': Point(207173.038, 428980.794),
            'point_end': Point(200143.318, 431638.797),
            'channel_width': 150,
            'min_channel_width': 0,
            'min_channel_depth': 0,
            'grid': 'Bovenrijn-Waal',
        },
        'Waal': {
            'point_start': Point(200143.318, 431638.797),
            'point_end': Point(120797.078, 425747.021),
            'channel_width': 150,
            'min_channel_width': 0,
            'min_channel_depth': 0,
            'grid': 'Bovenrijn-Waal',
        },
        'Pannerdensch Kanaal': {
            'point_start': Point(200143.318, 431638.797),
            'point_end': Point(193925.918, 440312.965),
            'channel_width': 70,
            'min_channel_width': 0,
            'min_channel_depth': 0,
            'grid': 'Pannerdensch Kanaal',
        },
        'Nederrijn_totDriel': {
            'point_start': Point(193925.918, 440312.965),
            'point_end': Point(183832.261,441768.265),
            'channel_width': 70,
            'min_channel_width': 20,
            'min_channel_depth': 2.5,
            'grid': 'Pannerdensch Kanaal',
        },
        'Nederrijn_vanafDriel': {
            'point_start': Point(183832.261,441768.265),
            'point_end': Point(102723.085, 433720.133),
            'channel_width': 80,
            'min_channel_width': 40,
            'min_channel_depth': 2.5,
            'grid': 'Nederrijn-Lek',
        },
        'IJssel_1': {
            'point_start': Point(193925.918, 440312.965),
            'point_end': Point(210029.578, 464734.952),
            'channel_width': 40,
            'min_channel_width': 20,
            'min_channel_depth': 2.5,
            'grid': 'IJssel',
        },
        'IJssel_2': {
            'point_start': Point(210029.578, 464734.952),
            'point_end': Point(205247.154, 489608.577),
            'channel_width': 50,
            'min_channel_width': 20,
            'min_channel_depth': 2.5,
            'grid': 'IJssel',
        },
        'IJssel_3': {
            'point_start': Point(205247.154, 489608.577),
            'point_end': Point(185908.998, 510582.501),
            'channel_width': 65,
            'min_channel_width': 30,
            'min_channel_depth': 2.5,
            'grid': 'IJssel',
        },
    }

    CWS.waterdepth_from_grids(sections)
