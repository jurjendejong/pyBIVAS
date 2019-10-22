#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `klimaatbestendige_netwerken` package."""


import unittest

from klimaatbestendige_netwerken.pyFIS import pyFIS


class test_pyFIS(unittest.TestCase):
    """Tests for `klimaatbestendige_netwerken` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        self.FIS = pyFIS()
        print(f'Geogeneration: {self.FIS.geogeneration}, Publication Date: {self.FIS.publication_date}')

    def test_000_list_geotypes(self):
        response = self.FIS.list_geotypes()
        assert len(response) > 0, "Loading failed"

    def test_001_list_relations(self):
        response = self.FIS.list_relations('lock')
        assert len(response) > 0, "Loading failed"

    def test_002_list_objects(self):
        df = self.FIS.list_objects('chamber')
        assert df.shape[0] > 0, "Loading failed"

    def test_003_merge_geotypes(self):
        df = self.FIS.merge_geotypes('bridge', 'opening')
        assert df.shape[0] > 0, "Loading failed"

    def test_004_find_by_polygon(self):
        pol = [(5.774, 51.898),
               (5.742, 51.813),
               (6.020, 51.779),
               (5.951, 51.912),
               (5.774, 51.898),
               ]
        df = self.FIS.find_object_by_polygon('bridge', pol)
        assert df.shape[0] > 0, "Loading failed"

    def test_006_find_closest(self):
        point = (5.774, 51.898)
        df = self.FIS.find_closest_object('bridge', point)
        assert df.shape[0] > 0, "Loading failed"


if __name__ == '__main__':
    unittest.main()
