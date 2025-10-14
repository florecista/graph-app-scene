import math
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsScene

class ReingoldTilfordTreeLayout:
    def __init__(self, scene: QGraphicsScene, canvas_width: int, canvas_height: int):
        self.scene = scene
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.x_positions = {}  # Stores x positions for nodes
        self.y_positions = {}  # Stores y positions for nodes
        self.modifiers = {}    # Used in second pass for conflict adjustment

    def layout(self, root_node):
        """Initiates the Reingold-Tilford layout."""
        depth = self.calculate_depth(root_node)

        # Perform the first walk to calculate preliminary positions
        self.first_walk(root_node, 0)

        # Perform the second walk to adjust positions and finalize layout
        self.second_walk(root_node, 0)

        # Apply positions to nodes
        for node, x in self.x_positions.items():
            y = self.y_positions[node]
            node.setPos(QPointF(x, y))

    def calculate_depth(self, node, depth=0):
        """Recursively calculates the depth of the tree."""
        if not node.children:
            return depth
        return max(self.calculate_depth(child, depth + 1) for child in node.children)

    def first_walk(self, node, depth):
        """First pass: Assign preliminary x-positions to nodes."""
        # Assign initial y-position based on the depth (generational spacing)
        self.y_positions[node] = depth * (self.canvas_height / (self.calculate_depth(node) + 1))

        if not node.children:
            # Leaf node case
            self.x_positions[node] = 0  # Set x-position for leaves initially
            return 0

        # Position each child and calculate subtree width
        subtree_width = 0
        for i, child in enumerate(node.children):
            subtree_width += self.first_walk(child, depth + 1)
            self.x_positions[child] += subtree_width

        # Center current node above its children
        mid_x = (self.x_positions[node.children[0]] + self.x_positions[node.children[-1]]) / 2
        self.x_positions[node] = mid_x

        return subtree_width + 1  # Increment width for the next node placement

    def second_walk(self, node, modifier):
        """Second pass: Adjust nodes to resolve conflicts."""
        # Adjust the x position with modifier
        self.x_positions[node] += modifier
        self.modifiers[node] = modifier  # Store the modifier for children

        # Recursively apply to children with updated modifier
        for child in node.children:
            self.second_walk(child, modifier + self.modifiers.get(child, 0))

    def update_lines_for_node(self, node):
        """Update the lines connected to the node."""
        for line in node.lines:  # Assuming node has a list of connected lines
            line.updateLine()  # Correct method to update line position

