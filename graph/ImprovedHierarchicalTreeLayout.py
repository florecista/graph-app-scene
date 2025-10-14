import math
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsScene

class ImprovedHierarchicalTreeLayout:
    def __init__(self, scene: QGraphicsScene, canvas_width: int, canvas_height: int):
        self.scene = scene
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.initial_spacing_ratio = 0.8  # Fraction of canvas width used for level 1
        self.spacing_decay_factor = 0.6   # Multiplier to reduce width at each level
        self.extra_spacing_factor = 1.5   # Extra spacing factor for level 2 if depth >= 4

    def layout(self, root_node):
        depth = self.calculate_depth(root_node)
        root_position_x = self.canvas_width / 2
        self.position_nodes(root_node, 0, root_position_x, self.canvas_width * self.initial_spacing_ratio, depth)

    def calculate_depth(self, node, depth=0):
        if not node.children:
            return depth
        return max(self.calculate_depth(child, depth + 1) for child in node.children)

    def position_nodes(self, node, generation, position, level_width, max_depth):
        if node is None:
            return

        # Calculate y position for the node, relative to depth
        y_pos = (generation / (max_depth + 1)) * self.canvas_height
        node.setPos(QPointF(position, y_pos))

        # Update the lines for the node
        self.update_lines_for_node(node)

        # Adjust level width for spacing if at level 2 and the tree is deep
        if generation == 1 and max_depth >= 4:
            level_width *= self.extra_spacing_factor

        # Calculate positions for children with adjusted width
        num_children = len(node.children)
        if num_children > 0:
            # Reduce the width for each level, keeping the layout within canvas width
            child_width = level_width * self.spacing_decay_factor
            angle_offset = math.pi / 8  # Default angle offset

            # Adjust angle offset for deeper levels to make edges more vertical
            if generation >= 2:
                angle_offset = math.pi / (8 + generation)

            # Determine starting position for child nodes
            start_position = position - (child_width / 2)
            for index, child in enumerate(node.children):
                child_position = start_position + (index + 1) * (child_width / (num_children + 1))
                self.position_nodes(child, generation + 1, child_position, child_width, max_depth)

    def update_lines_for_node(self, node):
        """Update the lines connected to the node."""
        for line in node.lines:
            line.updateLine()
