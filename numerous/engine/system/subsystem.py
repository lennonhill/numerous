from numerous.utils.dict_wrapper import _DictWrapper
from numerous.engine.system.item import Item
import networkx as nx
from numerous.engine.system.connector_item import ConnectorItem


class Subsystem(ConnectorItem):
    """
    Hierarchical representation of a group of items. Subsystems contains  a set of registered items, some
    of such items can be subsystems itself. This allow us to create Subsystems of any complexity.

    """

    def __init__(self, tag):
        self.ports = _DictWrapper({}, Item)
        self.registered_items = {}
        super().__init__(tag)

    def add_port(self, port_tag, item):
        """
        Creates a port for a subsystem. Ports can be used as an elements for binding.

        Parameters
        ----------
        port_tag: string
            Name of the port.
        item: :class:`numerous.engine.system.Item`
            item that is be used as a port.
        """

        if item.id not in self.registered_items.keys():
            raise ValueError(
                "Item {0} cannot be registered as port for subsystem {1}. Item is not registered in subsystem"
                    .format(item.tag, self.tag))
        self.ports[port_tag] = item

    def get_item(self, item_path):
        """
        Get an item using item path.

        Parameters
        ----------
        item_path: :class:`numerous.engine.system.ItemPath`
            hierarchical path to an item inside the subsystem

        Returns
        -------
        Item : :class:`numerous.engine.system.Item`
                returns an item found at given path or None

        """
        current_item = item_path.get_top_item()
        next_item_path = item_path.get_next_item_path()
        if self.tag == current_item and next_item_path:
            for item in self.registered_items.values():
                if item.tag == next_item_path.get_top_item():
                    return item.get_item(next_item_path)
            else:
                return None
        elif self.tag == current_item and next_item_path is None:
            return self
        else:
            return None

    def register_items(self, items):
        """

        Parameters
        ----------
        items : list of :class:`numerous.engine.system.Item`
            List of items to register in the subsystem.
        """
        any(self.register_item(item) for item in items)

    def increase_level(self):
        super().increase_level()
        for item in self.registered_items.values():
            item.increase_level()

    def get_graph_visualisation(self, DG=None, parent=None):
        if DG is None:
            DG = nx.DiGraph()
        DG.add_node(self.id)
        if parent:
            DG.add_edge(parent, self.id)
        for item in self.registered_items.values():
            if isinstance(item, Subsystem):
                item.get_graph_visualisation(DG, self.id)
            else:
                DG.add_edge(self.id, item.id)
        return DG

    def update_variables_path(self, item, c_item):
        for ns in item.registered_namespaces.values():
            for var in ns.variables.values():
                var.path.extend_path(c_item.id, self.id, self.tag)
        if isinstance(item, Subsystem):
            for item in item.registered_items.values():
                self.update_variables_path(item, c_item)

    def register_item(self, item):
        """

        Parameters
        ----------
        item : :class:`numerous.engine.system.Item`
            Item to register in the subsystem.
        """
        if item.tag in [x.tag for x in self.registered_items.values()]:
            raise ValueError('Item with tag {} is already registered in system {}'.format(item.tag, self.tag))
        item._increase_level()
        self.update_variables_path(item, item)

        self.registered_items.update({item.id: item})
