def classFactory(iface):
    """Load AdvancedSearchPanel class from file configurable_search.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .configurable_search import AdvancedSearchPanel
    return AdvancedSearchPanel(iface)
