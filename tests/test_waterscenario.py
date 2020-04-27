from pathlib import Path

from klimaatbestendige_netwerken.waterdepthgrid import WaterdepthGrid
from klimaatbestendige_netwerken.pyBIVAS_createwaterscenario import CreateWaterScenario
import logging
import unittest
from shapely.geometry import Point

logging.basicConfig(level=logging.DEBUG)


class test_WaterdepthGrid(unittest.TestCase):
    gridfile = Path('resources/Grid_BR-WL-RD.grd')
    bedlevelfile = Path('resources/bodemgrid2018_BRWL.dep')
    waterlevelfile = Path('resources/wl_BRWL_rmmRef_Q1020.dep')
    waterdepthfile = Path('resources/dep_BRWL_rmmRef_Q1020.dep')

    def setUp(self):
        if not self.gridfile.exists():
            self.skipTest('Files could not be found')

    def test_001(self):
        """Set up test fixtures, if any."""
        WD = WaterdepthGrid()
        WD.load_grid(self.gridfile)
        WD.add_bedlevel(self.bedlevelfile)
        WD.add_waterlevel(self.waterlevelfile)
        WD.add_waterdepth(self.waterdepthfile)

        WD.compute_width_depth_table()
        df = WD.compute_depth_forwidth(150, min_channelwidth=100, min_channel_depth=3)

        self.assertGreater(df.shape[0], 0, "Result is empty")


class test_CreateWaterScenario(unittest.TestCase):
    inputdir = Path(r'resources')

    SOBEK_output_reachsegments = inputdir / 'reachsegments.nc'
    SOBEK_output_gridpoints = inputdir / 'gridpoints.nc'
    SOBEK_network_file = inputdir / 'NetworkDefinition.ini'

    gridfile = Path('resources/Grid_BR-WL-RD.grd')

    BIVAS_database = inputdir / 'bivas_LSM_2018_NWMinput_lsm2bivas_v2018_02.db'

    sobek_reaches = {
        'Bovenrijn': ('BovenLobith', 'Pannerdenschekop'),
    }

    bivas_reaches = {
        'Bovenrijn': (150, 6855),
    }

    gridfiles = {
        'Bovenrijn-Waal': inputdir / 'Grid_BR-WL-RD.grd',
    }

    waterdepth = {
        'Bovenrijn-Waal': inputdir / 'dep_BRWL_rmmRef_Q1020.dep',
    }

    # Input dict. The key is just convenience and is not used anywhere
    sections = {
        'Boven-Rijn': {
            'point_start': Point(207173.038, 428980.794),
            'point_end': Point(200143.318, 431638.797),
            'channel_width': 150,
            'min_channel_width': 100,
            'min_channel_depth': 3,
            'grid': 'Bovenrijn-Waal',
        },
    }

    def setUp(self):
        if not self.SOBEK_output_reachsegments.exists():
            self.skipTest('Files could not be found')

    def test_001(self):
        CWS = CreateWaterScenario()

        CWS.load_sobek(self.SOBEK_output_reachsegments, self.SOBEK_output_gridpoints, self.SOBEK_network_file,
                       exclude_sobek_reaches_from_network=['VeesWap1', 'Ret_Wilpseklei'])

        CWS.load_bivas(self.BIVAS_database)

        CWS.create_mapping(self.bivas_reaches, self.sobek_reaches)

        CWS.waterscenario_from_mapping()

        CWS.load_waterdepthgrids(self.gridfiles, self.waterdepth)

        CWS.waterdepth_from_grids(self.sections)

        self.assertGreater(CWS.waterscenario.shape[0], 0, 'Empty result')


if __name__ == '__main__':
    unittest.main()
