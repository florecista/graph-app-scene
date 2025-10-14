import math
import random
from PyQt5.QtCore import QPointF, QPoint
from graph.GraphLayout import GraphLayout

class ForceAtlasLayout(GraphLayout):
    def __init__(self, node_list, edge_list, height, width, gravity=0.05, scaling_ratio=0.05, speed=0.05):
        self.nodes = node_list
        self.edges = edge_list
        self.canvas_height = height
        self.canvas_width = width
        self.gravity = gravity
        self.scaling_ratio = scaling_ratio
        self.speed = speed

        # Adjust k to a smaller portion of the canvas area
        self.k = math.sqrt((self.canvas_height * self.canvas_width) / len(self.nodes)) * 0.5
        self.force_map = {node.identifier: QPointF(0, 0) for node in self.nodes}

        self.initialize_positions()

    def initialize_positions(self):
        for node in self.nodes:
            new_pos = QPointF(random.uniform(0, self.canvas_width), random.uniform(0, self.canvas_height))
            node.setPos(new_pos)

    def layout(self):
        """Calculate repulsive and attractive forces, then update node positions."""
        # Scale down based on canvas and node density
        size_scaling = min(self.canvas_width, self.canvas_height) / (len(self.nodes) * 10)
        self.calculate_repulsive_forces(size_scaling)
        self.calculate_attractive_forces(size_scaling)
        self.apply_forces()

    def calculate_repulsive_forces(self, size_scaling):
        for v in self.nodes:
            force = QPoint(0, 0)
            for u in self.nodes:
                if u != v:
                    dist_vector = v.pos() - u.pos()
                    dist = max(math.hypot(dist_vector.x(), dist_vector.y()), 0.01)  # Avoid zero-distance
                    repulsive_force = (self.scaling_ratio * self.k ** 2) / dist * size_scaling

                    dx = int(dist_vector.x() / dist * repulsive_force)
                    dy = int(dist_vector.y() / dist * repulsive_force)

                    force += QPoint(dx, dy)
            self.force_map[v.identifier] = force

    def calculate_attractive_forces(self, size_scaling):
        for edge in self.edges:
            dist_vector = edge.end.pos() - edge.start.pos()
            dist = max(math.hypot(dist_vector.x(), dist_vector.y()), 0.01)  # Avoid zero-distance
            attractive_force = (dist ** 2) / self.k * size_scaling

            dx = int(dist_vector.x() * attractive_force)
            dy = int(dist_vector.y() * attractive_force)

            self.force_map[edge.start.identifier] -= QPoint(dx, dy)
            self.force_map[edge.end.identifier] += QPoint(dx, dy)

    def apply_forces(self):
        for node in self.nodes:
            force = self.force_map[node.identifier]

            # Integrate gravity to bring nodes toward the center
            center_x = (self.canvas_width / 2 - node.pos().x()) * self.gravity
            center_y = (self.canvas_height / 2 - node.pos().y()) * self.gravity
            force += QPointF(center_x, center_y)

            # Control node movement speed, add damping, and apply position update
            new_x = node.pos().x() + force.x() * self.speed * 0.5
            new_y = node.pos().y() + force.y() * self.speed * 0.5
            node.setPos(QPointF(new_x, new_y))

        # Update edges to match node movement
        for edge in self.edges:
            edge.updateLine()

    def run_iterations(self, num_iterations=50):
        for _ in range(num_iterations):
            self.layout()
