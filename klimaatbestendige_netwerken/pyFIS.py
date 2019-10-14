"""
Module to read geodata of the Fairway Information Services of Rijkswaterstaat (http://vaarweginformatie.nl).

Jurjen de Jong, Deltares, 24-9-2019
"""

import requests
import logging
from shapely import wkt
from shapely.geometry import Point, Polygon
import geopandas as gpd
from pathlib import Path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class pyFIS:
    count = 500  # Number of reponses per page. This is also the default maximum

    def __init__(self, url='https://www.vaarweginformatie.nl/wfswms/dataservice/1.3'):
        self.baseurl = url

        response_geogeneration = self._parse_request('geogeneration')
        self.geogeneration = str(response_geogeneration['GeoGeneration'])
        logger.INFO(f"Geogeneration: {self.geogeneration} - {response_geogeneration['PublicationDate']}")

    def list_geotypes(self):
        """Returns list of all geotypes"""
        return self._parse_request('geotype')

    def list_relations(self, geotype):
        """
        Returns list of all relations for given geotype
        Note: Not all relations are explicitly specified
        """
        return self._parse_request([geotype, 'relations'])

    def list_objects(self, geotype):
        """
        Returns dataframe of all objects for given geotype
        """

        # Get list of objects from memory, or load if not accessed yet before
        if hasattr(self, geotype):
            return getattr(self, geotype)

        result = self._parse_request([self.geogeneration, geotype])

        # Store in memory
        setattr(self, geotype, result)

        return result

    def list_all_objects(self):
        """
        Load all objects of all geotypes
        """
        for geotype in self.list_geotype():
            self.list_objects(self, geotype)

    def get_object(self, geotype, objectid):
        """
        Load all data of one object
        
        >> get_object('bridge', 2123)
        return: objectdetails
        
        """
        return self._parse_request([self.geogeneration, geotype, objectid])

    def get_object_subobjects(self, geotype, objectid, geotype2):
        """
        Load all data of one object
        
        >> get_object_subobjects('bridge', 1217, 'opening')
        return: [openingid#1, openingid#2, ...]
        
        """

        return self._parse_request([self.geogeneration, geotype, objectid, geotype2])

    def _parse_request(self, components):
        """
        Internal command to create and send requets of different kind. It combines 
        components with the baseurl and reads the response. If the data contains 
        'Result' it will be processed as a multi-page datasource and converted to DataFrame.
        """

        if not isinstance(components, list): components = [components]
        url = self.baseurl + '/' + '/'.join(components)

        logger.info('Reading: {}'.format(', '.join(components)))

        result = []
        offset = 0

        while True:
            response = requests.get(url + f'?offset={offset}&count={self.count}')
            assert response, f'An error has occured. URL: {url}. Response: {response}'

            response_dict = response.json()

            if 'Result' in response_dict:  # Multi page response
                result.extend(response_dict['Result'])

                if response_dict['Offset'] + response_dict['Count'] < response_dict['TotalCount']:
                    offset += self.count
                    continue
                else:
                    result = gpd.GeoDataFrame(result)
                    result['Geometry'] = result['Geometry'].apply(wkt.loads)
                    return result

            else:  # Single page response
                result = response_dict
                return result

    def find_object_by_value(self, geotype, fieldvalue, fieldname='Name'):
        list_objects = self.list_objects(geotype)

        result = list_objects[list_objects[fieldname] == fieldvalue]
        return result

    def find_object_by_polygon(self, geotype, polygon):
        # TODO
        NotImplementedError()

    def find_closest_object(self, geotype, point):
        # TODO
        NotImplementedError()

    def merge_geotypes(self, left_geotype, right_geotype, left_on=['GeoType', 'Id'],
                       right_on=['ParentGeoType', 'ParentId']):
        df_l = self.list_objects(left_geotype)
        df_r = self.list_objects(right_geotype)
        df_merge = df_l.merge(df_r, left_on=left_on, right_on=right_on, suffixes=('', f'_{right_geotype}'))
        return df_merge

    def export_sqlite(self, sqlite_filepath, force=True):
        # TODO
        sqlite_filepath = Path(sqlite_filepath)

        if sqlite_filepath.exists():
            if not force:
                FileExistsError()
            else:
                sqlite_filepath.unlink()

        self.list_all_objects()

        for geotype in self.list_geotype():
            # Save to database
            pass

        NotImplementedError()


if __name__ == '__main__':
    FIS = pyFIS()
    FIS.list_geotypes()
    FIS.merge_geotypes('bridge', 'opening')
