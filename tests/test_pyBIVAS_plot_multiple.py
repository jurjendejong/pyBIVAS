from unittest import TestCase
from klimaatbestendige_netwerken.pyBIVAS_plot_multiple import pyBIVAS_plot_compare
from klimaatbestendige_netwerken.pyBIVAS_plot import pyBIVAS_plot
from pathlib import Path


class TestpyBIVAS_plot(TestCase):
    skipSlowRuns = True

    database_file_1 = Path(r'resources/Bivas_2018_v3.db')
    database_file_2 = Path(r'resources/Bivas_2018_v3.db')

    arcName = 'BovenRijn'
    arcID = pyBIVAS_plot.Arcs[arcName]

    def setUp(self):
        # Test if database exists
        if not self.database_file_1.exists() or not self.database_file_2.exists():
            self.skipTest('Database could not be found')

        self.B = pyBIVAS_plot_compare(BIVAS_simulations={
            'Sim1': self.database_file_1,
            'Sim2': self.database_file_2
        })
        self.B.connect_all()
        self.B.outputdir = Path('export_pyBIVAS_plot_compare')

        if not self.B.outputdir.exists():
            self.B.outputdir.mkdir()

    def test_plot_tijdseries(self):
        self.B.plot_tijdseries(label=self.arcName, arcID=self.arcID)

    def test_plot_routes(self):
        self.B.plot_routes(routes='largestIncrease', limit=5)
        self.B.plot_routes(routes='largestIncreaseDate', limit=5)
        self.B.plot_routes(routes='database', limit=5)
        self.B.plot_routes(routes='larger', limit=5)
        self.B.plot_routes(routes=355945, limit=5)
        self.B.plot_routes(routes=[355945, 154544], limit=5)
