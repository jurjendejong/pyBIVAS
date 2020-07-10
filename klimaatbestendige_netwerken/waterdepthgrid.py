"""

This class contains a gridded approach on computing waterdepth

Jurjen de Jong, 26-4-2020

"""

import geopandas as gpd
import logging
from klimaatbestendige_netwerken.externals.dep import Dep
from klimaatbestendige_netwerken.externals.grid import Grid
from shapely.geometry import Polygon, LineString, MultiPoint, Point
from shapely.ops import split
import numpy as np

logging.basicConfig(level=logging.INFO)


class WaterdepthGrid:


    def __init__(self):
        self.grid = None
        self.bedlevel = None
        self.waterlevel = None
        self.waterdepth = None

        self.gpd = None
        self.ZW_table = {}
        self.pd_sections = None

    def load_grid(self, gridfile):
        logging.info(f'Loading grid: {gridfile}')
        self.grid = Grid.fromfile(gridfile)
        self.gpd = self.grid_to_geopandas(self.grid)

    def add_bedlevel(self, bedlevelfile):
        # Load bedlevel
        # Option 1: From .dep file
        # Option 2: From samples (TODO)
        if not self.grid:
            Exception('Grid has not been loaded yet')

        logging.info(f'Loading bedlevel: {bedlevelfile}')
        self.bedlevel = Dep.read(bedlevelfile, self.grid.shape)
        self.gpd['bedlevel'] = self.gpd_add_coverage(self.gpd, self.bedlevel)

    def add_waterlevel(self, waterlevelgrid):
        # Option 1: From .dep file
        # Option 2: From samples (TODO)
        logging.info(f'Loading waterlevel: {waterlevelgrid}')
        self.waterlevel = Dep.read(waterlevelgrid, self.grid.shape)
        self.gpd['waterlevel'] = self.gpd_add_coverage(self.gpd, self.waterlevel)

    def add_waterlevel_from_points(self, x: list, y: list, waterlevel: list):
        NotImplementedError('TODO')
        pass

        # df[x,y,wl]
        #

        # For each point, find the closest n_row

        # Set value for each row. Mean value in row if multiple exist. Linear interpolation, no extrapolation.

        # Create into dep layer
        #
        #
        #
        # self.waterlevel = Dep()
        # self.waterlevel.val = [asd]
        # self.waterlevel.shape = (self.grid.shape[0]+1, self.grid.shape[1]+1)
        # self.gpd['waterlevel'] = self.gpd_add_coverage(self.gpd, self.waterlevel)

    def add_waterdepth(self, waterdepthgrid):
        logging.info(f'Loading waterdepth: {waterdepthgrid}')
        self.waterdepth = Dep.read(waterdepthgrid, self.grid.shape)
        self.gpd['waterdepth'] = self.gpd_add_coverage(self.gpd, self.waterdepth)

        # Now remove all dry and nans
        self.gpd.dropna(inplace=True)
        self.gpd = self.gpd[self.gpd['waterdepth'] > 0.01]

    def compute_waterdepth(self):
        logging.warning('This function is not tested yet')
        if not self.waterlevel and not self.bedlevel:
            Exception('Either waterlevel of bedlevel has not been loaded yet')

        logging.info(f'Compute waterdepth')
        self.waterdepth = self.waterlevel.copy()
        self.waterdepth.val = self.waterlevel.val - self.bedlevel.val
        self.waterdepth[self.waterdepth < 0] = 0

        self.gpd['waterdepth'] = self.gpd_add_coverage(self.gpd, self.waterdepth)

    def compute_width_depth_table(self):
        """
        Multiple functions to compute properties of waterdepth and corresponding width for each crosssection
        in the grid. It assumes that the grid is moved in n-direction

        :return:
        """
        logging.info(f'Computing width-depth tables per n-row')

        all_n_rows = sorted(self.gpd['n'].unique())

        for n_row in all_n_rows:
            logging.debug(f'Processing n-row: {n_row}')

            ii = self.gpd['n'] == n_row
            gpd_row = self.gpd.loc[ii]
            gpd_row = gpd_row.dropna(how='any')

            depths = []
            widths = []
            for ii in range(1, gpd_row.shape[0]+1):
                depths.append(gpd_row['waterdepth'].rolling(window=ii).min().max())
                widths.append(ii * gpd_row['width'].mean())  # Assuming the widths are equal

            self.ZW_table[n_row] = {
                'Z': depths,
                'W': widths,
                'Centroid': gpd_row.geometry.unary_union.centroid
            }

    def compute_depth_forwidth(self, channelwidth,
                               min_channelwidth=0, min_channel_depth=0,  # Old params
                               sideslope=0, depth_at_fullwidth=0,  # New params
                               ):
        """

        :param channelwidth: Base width
        :param min_channelwidth: Minimum width when narrowing
        :param min_channel_depth: Only do narrowing if width gets lower than this depth
        :return:
        """
        logging.info(f'Computing depth per n-row')

        channel_depth = {}
        channel_width = {}
        for n_row, ZW_table in self.ZW_table.items():

            if sideslope == 0: # Old mode
                depth_fullwidth = np.interp(channelwidth, ZW_table['W'][::-1], ZW_table['Z'][::-1])
                if depth_fullwidth > min_channel_depth:
                    width_n = channelwidth
                    depth_n = depth_fullwidth
                else:
                    width_n = np.interp(min_channel_depth, ZW_table['Z'], ZW_table['W'])
                    depth_n = min_channel_depth

                    if width_n < min_channelwidth:
                        width_n = min_channelwidth
                        depth_n = np.interp(min_channelwidth, ZW_table['W'][::-1], ZW_table['Z'][::-1])
            else:  # New mode

                # Construct curve that illustrates the desired depth-width ratio. First compute the depth based on the
                # sideslode when the width converges to 0
                D_lowest = depth_at_fullwidth - (channelwidth - 0) / 2 * (1 / sideslope)

                Lookupcurve_x = [0, channelwidth, channelwidth]
                Lookupcurve_y = [D_lowest, depth_at_fullwidth, 99]

                # Find where on this line this map is
                first_line = LineString(np.column_stack((ZW_table['W'], ZW_table['Z'])))
                second_line = LineString(np.column_stack((Lookupcurve_x, Lookupcurve_y)))
                intersection = first_line.intersection(second_line)

                if isinstance(intersection, Point):
                    width_n = intersection.x
                    depth_n = intersection.y
                else:
                    # If no intersection, than take last row of ZW-table (so max width)
                    width_n = first_line.coords[-1][0]
                    depth_n = first_line.coords[-1][1]

            channel_depth[n_row] = depth_n
            channel_width[n_row] = width_n

        return gpd.GeoDataFrame({
            'width': channel_width,
            'depth': channel_depth,
            'geometry': {n_row: ZW_table['Centroid'] for n_row, ZW_table in self.ZW_table.items()}
        })


    def export_shapefile(self, filepath):
        self.gpd.to_file(filepath)

    def __repr__(self):
        return f'WaterdepthGrid. Shape: {self.grid.shape}'

    ##################
    # STATIC METHODS #
    ##################

    @staticmethod
    def grid_to_geopandas(grid: Grid):

        # Obtain the total number of vertexec (always 2) plus junctions in both the horizontal (cols) and
        # vertical directions (rows) of the water depth grid.
        rows, cols = grid.shape

        # Reconstruct the grid and all coverages to a list of polygons and coverages
        polygons = []
        m = []
        n = []
        for i in range(rows - 1):
            for j in range(cols - 1):
                polygons.append(Polygon(
                    [[grid.x[i, j], grid.y[i, j]],
                     [grid.x[i, j + 1], grid.y[i, j + 1]],
                     [grid.x[i + 1, j + 1], grid.y[i + 1, j + 1]],
                     [grid.x[i + 1, j], grid.y[i + 1, j]]]
                ))
                m.append(i)
                n.append(j)

        # Construct geopandas
        polygons = gpd.GeoDataFrame({
            'm': m,
            'n': n,
            'geometry': polygons, })

        # Drop empty rows
        polygons = polygons.dropna(how='any')

        # Compute width: h = 2*A/(a+b)
        for ii, p in polygons.geometry.items():
            segments = split(p.boundary, MultiPoint(p.boundary.coords[1:]))
            side_lengths = sorted([s.length for s in segments])

            h = 2 * p.area / (side_lengths[2] + side_lengths[3])

            polygons.loc[ii, 'width'] = h

        return polygons

    @staticmethod
    def gpd_add_coverage(gpd_grid, coverage):
        c = []
        for _, row in gpd_grid.iterrows():
            m = row['m']
            n = row['n']

            c.append(coverage.val[m + 1, n + 1])

        return c

    @staticmethod
    def compute_largest_width_for_depth(W, Z, depth):
        """
        For a given cross-section (Z-W-profile) compute the width of
        the channel for a given depth.

        W: list of horizontal coordinates
        Z: list of vertical coordinates (same shape as W)
        depth: the required water depth
        """
        logging.debug(f'Running depth: {depth:.2f}')

        # Find all locations where a crossing of [depth] occurs
        crossings = np.nonzero(np.diff(Z >= depth))[0]

        # Local minima and maxima
        local_minmax = np.nonzero(np.abs(np.diff(np.sign(np.diff(Z)))) == 2)[0] + 1

        # Find exact value of the widths at these crossings
        W_crossings = []
        for ii in crossings:
            if (Z[ii] == depth) and (ii in local_minmax):
                # If point is exactly a point and this point is the local minimum or maximum, skip
                continue
            else:
                # Interpolate
                W_crossing = W[ii] + (W[ii + 1] - W[ii]) / (Z[ii + 1] - Z[ii]) * (depth - Z[ii])

                W_crossings.append(W_crossing)

        if len(W_crossings) == 0:
            logging.error(f'Cross-section not reaching depth: {depth}')
            return None

        W_crossings = np.reshape(W_crossings, (-1, 2))

        # Find largest width in the dataset
        Widths = np.diff(W_crossings)
        Width_max = np.max(Widths)
        return Width_max


if __name__ == '__main__':
    from pathlib import Path

    # Include example
    WD = WaterdepthGrid()
    WD.load_grid(Path('../tests/resources/Grid_BR-WL-RD.grd'))
    WD.add_bedlevel(Path('../tests/resources/bodemgrid2018_BRWL.dep'))
    WD.add_waterlevel(Path('../tests/resources/wl_BRWL_rmmRef_Q1020.dep'))
    WD.add_waterdepth(Path('../tests/resources/dep_BRWL_rmmRef_Q1020.dep'))

    WD.compute_width_depth_table()
    WD.compute_depth_forwidth(150, min_channelwidth=100, min_channel_depth=3)
