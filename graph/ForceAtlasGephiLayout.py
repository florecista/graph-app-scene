from PyQt5.QtCore import QObject, pyqtProperty
import math

class ForceAtlasGephiLayout(QObject):
    def __init__(self, graph=None, height=0, width=0, layout_builder=None):
        super().__init__()
        self.graph = graph
        self.height = height
        self.width = width
        self.layout_builder = layout_builder
        # Properties initialization
        self.inertia = 0.1
        self.repulsion_strength = 200.0
        self.attraction_strength = 10.0
        self.max_displacement = 10.0
        self.freeze_balance = True
        self.freeze_strength = 80.0
        self.freeze_inertia = 0.2
        self.gravity = 30.0
        self.speed = 1.0
        self.cooling = 1.0
        self.outbound_attraction_distribution = False
        self.adjust_sizes = False

    def reset_properties_values(self):
        # Reset properties to default
        self.inertia = 0.1
        self.repulsion_strength = 200.0
        self.attraction_strength = 10.0
        self.max_displacement = 10.0
        self.freeze_balance = True
        self.freeze_strength = 80.0
        self.freeze_inertia = 0.2
        self.gravity = 30.0
        self.outbound_attraction_distribution = False
        self.adjust_sizes = False
        self.speed = 1.0
        self.cooling = 1.0

    def init_algo(self):
        # Prepare algorithm initialization
        if self.graph:
            self.ensure_safe_layout_node_positions()

    def get_edge_weight(self, edge, is_dynamic_weight=False, interval=None):
        return edge.get_weight(interval) if is_dynamic_weight else edge.get_weight()

    def layout(self):  # Renamed from go_algo
        if not self.graph:
            return

        nodes = list(self.graph.nodes)
        edges = list(self.graph.edges)

        for node in nodes:
            # Initialize layout data if not present
            if not hasattr(node, 'layout_data'):
                node.layout_data = {'dx': 0, 'dy': 0, 'freeze': 0}

            node_data = node.layout_data
            node_data['old_dx'] = node_data['dx']
            node_data['old_dy'] = node_data['dy']
            node_data['dx'] *= self.inertia
            node_data['dy'] *= self.inertia

        # Apply repulsion and attraction forces
        for node in nodes:
            for other_node in nodes:
                if node != other_node:
                    repulsion = self.repulsion_strength * (1 + self.graph.degree(node)) * (1 + self.graph.degree(other_node))
                    self.apply_repulsion(node, other_node, repulsion)

        for edge in edges:
            source = edge[0]  # Access the source GraphItem
            target = edge[1]  # Access the target GraphItem
            attraction = self.attraction_strength
            self.apply_attraction(source, target, attraction)

        # Apply gravity force
        for node in nodes:
            self.apply_gravity(node)

        # Apply speed adjustments
        for node in nodes:
            node_data = node.layout_data
            if self.freeze_balance:
                node_data['dx'] *= self.speed * 10.0
                node_data['dy'] *= self.speed * 10.0
            else:
                node_data['dx'] *= self.speed
                node_data['dy'] *= self.speed

            # Apply displacement
            displacement = min(1, self.max_displacement / math.sqrt(node_data['dx'] ** 2 + node_data['dy'] ** 2))
            node_data['dx'] *= displacement / self.cooling
            node_data['dy'] *= displacement / self.cooling

            # Update node position using setPos
            new_x = node.pos().x() + node_data['dx']
            new_y = node.pos().y() + node_data['dy']
            node.setPos(new_x, new_y)

    def apply_repulsion(self, node1, node2, strength):
        # Calculate and apply repulsion forces
        dx = node1.pos().x() - node2.pos().x()
        dy = node1.pos().y() - node2.pos().y()
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance > 0:
            repulsion = strength / (distance ** 2)
            node1.layout_data['dx'] += dx * repulsion
            node1.layout_data['dy'] += dy * repulsion
            node2.layout_data['dx'] -= dx * repulsion
            node2.layout_data['dy'] -= dy * repulsion

    def apply_attraction(self, source, target, strength):
        # Calculate and apply attraction forces
        dx = target.pos().x() - source.pos().x()
        dy = target.pos().y() - source.pos().y()
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance > 0:
            attraction = strength * distance
            source.layout_data['dx'] += dx * attraction
            source.layout_data['dy'] += dy * attraction
            target.layout_data['dx'] -= dx * attraction
            target.layout_data['dy'] -= dy * attraction

    def apply_gravity(self, node):
        # Assuming node is a GraphItem, use pos().x() and pos().y() to get the coordinates
        dx = -node.pos().x()
        dy = -node.pos().y()

        # Apply gravity based on dx, dy (example calculation)
        force = self.gravity * (dx ** 2 + dy ** 2) ** 0.5
        node.setPos(node.pos().x() + dx * force, node.pos().y() + dy * force)

    def end_algo(self):
        if self.graph:
            for node in self.graph.nodes:
                node.layout_data = None

    def can_algo(self):
        return True
