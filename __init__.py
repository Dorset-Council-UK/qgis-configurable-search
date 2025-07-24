def classFactory(iface):
    """Load ConfigurableSearch class from file configurable_search.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .configurable_search import ConfigurableSearch
    return ConfigurableSearch(iface)
