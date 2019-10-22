=======
pyFIS
=======

This script queries the FIS or VNDS of Rijkswaterstaat. This is the backend of vaarweginformatie.nl:
(https://vaarweginformatie.nl/frp/main/#/geo/map)

More information on the service that is being queried can be found here:
https://vaarweginformatie.nl/frp/main/#/page/services

To use pyFIS in a project::

    from klimaatbestendige_netwerken.pyFIS import pyFIS


    FIS = pyFIS()

Generate list of all geotypes::

    FIS.list_geotypes()

Get a list of all geotype='chamber' in the model::

    FIS.list_objects('chamber')

After running it once, this data can also be accessed by::

    FIS.chamber

Often multiple tables are related to each other. To get the related tables (sometimes more relations seem to exist than given by this query) ::

    FIS.list_relations('bridge')

As opening is a subset of bridge, get a query of both combined::

    FIS.merge_geotypes('bridge', 'opening')

Get all objects of a certain geotype within a given polygon::

    pol = [(5.774, 51.898),
           (5.742, 51.813),
           (6.020, 51.779),
           (5.951, 51.912),
           (5.774, 51.898),
           ]

    FIS.find_object_by_polygon('bridge', pol)

Or the closest object to a given point::

    FIS.find_closest_object('bridge', pol[0])

