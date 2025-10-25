import base64
import uuid
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QRect, QPointF, QByteArray, QRectF, QPoint
from PyQt5.QtGui import QPainter, QColor, QPixmap, QPainterPath
from PyQt5.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
import constants


class GraphItem(QGraphicsPixmapItem):
    pen = QtGui.QPen(Qt.red, 2)
    brush = QtGui.QBrush(QtGui.QColor(31, 176, 224))
    controlBrush = QtGui.QBrush(QtGui.QColor(214, 13, 36))

    def __init__(self, pixmap=None, label="", attributes=None, position=QPointF(), image=None, image_scale=False):
        super().__init__(pixmap)

        self.identifier = uuid.uuid4()
        self.show_label = False
        self.label_position = constants.LabelPosition.Below
        self.label_size = 8
        self.node_size = 30
        self.node_shape = constants.NodeShapes.Circle
        self.show_icon = True
        self.use_image = False
        self._is_hovered = False

        self.node_foreground_color = QColor(255, 0, 0)
        self.node_background_color = QColor(255, 255, 0)
        self.node_highlight_color = QColor(0, 0, 255)
        self.node_label_text_color = QColor(0, 255, 0)

        self.startPosition = None
        self.lines = []
        self.edges = []  # connected GraphEdge objects

        self.parent = None
        self.children = []

        self.label = label
        self.attributes = attributes or {}
        self.image = image
        self.image_scale = image_scale
        self._cached_pixmap = None
        self.setPos(position)

        self.node_type = None

        # Enable movement, selection, and geometry notifications
        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        self.setAcceptHoverEvents(True)

    # ---------------- Image Handling ----------------

    def decode_base64_image(self, base64_string):
        """Decode base64 to QPixmap and cache result."""
        if self._cached_pixmap:
            return self._cached_pixmap
        image_data = base64.b64decode(base64_string)
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self._cached_pixmap = pixmap
        return pixmap

    def clear_cache(self):
        """Clear cached pixmap."""
        self._cached_pixmap = None

    # ---------------- Hover Events ----------------

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    # ---------------- Painting ----------------

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        # Highlight if hovered or selected
        if self._is_hovered or self.isSelected():
            highlight_pen = QtGui.QPen(self.node_highlight_color, 2, Qt.DashLine)
            painter.setPen(highlight_pen)
        else:
            painter.setPen(QtGui.QPen(self.node_background_color, 2))

        # Draw node image
        if self.use_image and self.image:
            image_pixmap = self.decode_base64_image(self.image)
            if not image_pixmap.isNull():
                if self.node_shape == constants.NodeShapes.Circle:
                    clip = QPainterPath()
                    rect = QRectF(0, 0, self.node_size, self.node_size)
                    clip.addEllipse(rect)
                    painter.setClipPath(clip)

                if self.image_scale:
                    scaled_pixmap = image_pixmap.scaled(
                        self.node_size, self.node_size,
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    painter.drawPixmap(0, 0, scaled_pixmap)
                else:
                    painter.drawPixmap(0, 0, image_pixmap)

        elif self.show_icon:
            super().paint(painter, option, widget)
        else:
            painter.setBrush(QtGui.QBrush(self.node_foreground_color))
            rect = QRect(0, 0, self.node_size, self.node_size)
            if self.node_shape == constants.NodeShapes.Circle:
                painter.drawEllipse(rect)
            elif self.node_shape == constants.NodeShapes.Square:
                painter.drawRect(rect)
            else:
                painter.drawEllipse(rect)

        # Draw label
        if self.show_label and self.label:
            label_text = ''
            attributes_list = self.attributes.get('Attributes', [])
            if isinstance(attributes_list, list):
                label_text = next(
                    (attr.get('description', '') for attr in attributes_list if attr.get('name') == self.label),
                    ''
                )

            if label_text:
                font = painter.font()
                font.setPointSize(int(self.label_size))
                painter.setFont(font)
                painter.setPen(QtGui.QPen(Qt.black))

                text_rect = painter.boundingRect(QRect(0, 0, self.node_size, self.node_size), Qt.AlignCenter, label_text)
                if self.label_position == constants.LabelPosition.Below:
                    text_rect.moveTop(self.node_size + 5)
                elif self.label_position == constants.LabelPosition.Above:
                    text_rect.moveBottom(-5)
                else:
                    text_rect.moveCenter(QPoint(self.node_size / 2, self.node_size / 2))
                painter.drawText(text_rect, Qt.AlignCenter, label_text)

        painter.restore()

    # ---------------- Scene Interaction ----------------

    def itemChange(self, change, value):
        """Ensure connected edges update when node moves."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in getattr(self, "edges", []):
                if hasattr(edge, "updatePosition"):
                    edge.updatePosition()
        return super().itemChange(change, value)

    # ---------------- Edge Management ----------------

    def addLine(self, lineItem):
        if lineItem not in self.lines:
            self.lines.append(lineItem)
            if lineItem not in self.edges:
                self.edges.append(lineItem)
            return True
        return False

    def removeLine(self, lineItem):
        if lineItem in self.lines:
            try:
                self.scene().removeItem(lineItem)
            except Exception:
                pass
            self.lines.remove(lineItem)
            if lineItem in self.edges:
                self.edges.remove(lineItem)
            return True
        return False

    # ---------------- Parent-Child ----------------

    def has_parent(self):
        return self.parent is not None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def get_children(self):
        return self.children
