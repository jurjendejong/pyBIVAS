#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `klimaatbestendige_netwerken` package."""


import unittest
import logging
from pathlib import Path

from klimaatbestendige_netwerken import pyFIS

logging.basicConfig(level=logging.DEBUG)


class test_pyFIS(unittest.TestCase):
    """Tests for `klimaatbestendige_netwerken` package."""

    skipSlowRuns = False

    export_dir = Path('export_pyFIS')


    def setUp(self):
        """Set up test fixtures"""
        self.FIS = pyFIS.pyFIS()

        if not self.export_dir.exists():
            self.export_dir.mkdir()

    def test_print_geogeneration(self):
        print(f'Geogeneration: {self.FIS.geogeneration}, Publication Date: {self.FIS.publication_date}')

    def test_000_list_geotypes(self):
        list_geotypes = self.FIS.list_geotypes()
        assert len(list_geotypes) > 0, "Loading failed"
        print(list_geotypes)

    def test_001_list_relations(self):
        list_relations = self.FIS.list_relations('lock')
        assert len(list_relations) > 0, "Loading failed"
        print(list_relations)

    def test_002_list_objects(self):
        self.FIS.list_objects('chamber')
        self.FIS.list_objects('chamber')
        df = self.FIS.chamber
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())

    def test_003_merge_geotypes(self):
        df = self.FIS.merge_geotypes('bridge', 'opening')
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())

    def test_003_merge_geotypes2(self):
        df = self.FIS.merge_geotypes('lock', 'chamber')
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())

    def test_004_find_by_polygon(self):
        pol = [(5.774, 51.898),
               (5.742, 51.813),
               (6.020, 51.779),
               (5.951, 51.912),
               (5.774, 51.898),
               ]
        df = self.FIS.find_object_by_polygon('bridge', pol)
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())

    def test_006_find_closest(self):
        point = (5.774, 51.898)
        df = self.FIS.find_closest_object('bridge', point)
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())

    def test_007_list_all_objects(self):
        if self.skipSlowRuns:
            self.skipTest('Skipping because this test takes very long')
        self.FIS.list_all_objects()
        filepath = self.export_dir / f'Export_geogeneration_{self.FIS.geogeneration}.xlsx'
        self.FIS.export(filepath=filepath)
        self.assertTrue(filepath.is_file())

    def test_008_get_object(self):
        df = self.FIS.get_object('bridge', 1667)
        self.assertGreater(df.shape[0], 0, "Loading failed")
        print(df.head(10).to_string())

    def test_008_get_object2(self):
        df = self.FIS.get_object('section', 24774125)
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())

    def test_009_get_object_subobjects(self):
        list_openings = self.FIS.get_object_subobjects('bridge', 1667, 'opening')
        assert len(list_openings) > 0, "Loading failed"
        print(list_openings.head(10).to_string())

    def test_010_find_object_by_value(self):
        df = self.FIS.find_object_by_value('bridge', 'Spoorbrug HRMK')
        assert df.shape[0] > 0, "Loading failed"
        print(df.head(10).to_string())


if __name__ == '__main__':
    unittest.main()
