from math import atan2, cos, sin, radians
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QPen, QBrush, QPolygonF, QColor, QPainter
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsItem


class GraphEdge(QGraphicsLineItem):
    def __init__(self, source, target, label=None, weight=None, parent=None, arrow_enabled=False, show_label=False):
        super().__init__(parent)

        self.start = source
        self.end = target if isinstance(target, QGraphicsItem) else None
        self.targetPos = target if isinstance(target, QPointF) else None

        self.arrow_enabled = arrow_enabled
        self.show_label = show_label
        self.node_size = 30
        self.arrow_size = 20
        self.label = label
        self.weight = weight

        self.is_hovered = False
        self.is_selected = False

        self._line = QLineF(QPointF(0, 0), QPointF(0, 0))
        self._register_on_nodes()
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsFocusable)

        self.updatePosition()

    def _register_on_nodes(self):
        for node in (self.start, self.end):
            try:
                if node and hasattr(node, "edges") and self not in node.edges:
                    node.edges.append(self)
            except Exception:
                pass

    def _unregister_from_nodes(self):
        for node in (self.start, self.end):
            try:
                if node and hasattr(node, "edges") and self in node.edges:
                    node.edges.remove(self)
            except Exception:
                pass

    def setEnd(self, end: 'GraphItem'):
        self._unregister_from_nodes()
        self.end = end
        self.targetPos = None
        self._register_on_nodes()
        self.updatePosition()

    def setP2(self, point: QPointF):
        if not isinstance(point, QPointF):
            return
        if not hasattr(self, "_line") or self._line is None:
            self._line = QLineF(QPointF(0, 0), point)
        else:
            self._line.setP2(point)
        self.setLine(self._line)

    def getCenterPos(self, item):
        if isinstance(item, QGraphicsItem):
            rect = item.boundingRect()
            return item.scenePos() + QPointF(rect.width() / 2.0, rect.height() / 2.0)
        elif isinstance(item, QPointF):
            return item
        return None

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.update()
        super().mousePressEvent(event)

    def paint(self, painter, option, widget=None):
        painter.save()
        pen_color = QColor("green") if self.is_selected else QColor("blue") if self.is_hovered else QColor("black")
        painter.setPen(QPen(pen_color, 2))
        painter.drawLine(self.line())
        painter.restore()

        if self.arrow_enabled and self.line().length() > 5:
            self._draw_arrow(painter)
        if self.show_label and self.label:
            self._draw_label(painter)

    def controlPoints(self):
        p1 = self.getCenterPos(self.start)
        p2 = self.getCenterPos(self.end) if self.end else self.targetPos
        return p1, p2

    def updateLine(self):
        if not hasattr(self, "_line") or self._line is None:
            self._line = QLineF(QPointF(0, 0), QPointF(0, 0))

        p1, p2 = self.controlPoints()
        if p1 is not None:
            self._line.setP1(p1)
        if p2 is not None:
            self._line.setP2(p2)
        self.setLine(self._line)

    def updatePosition(self):
        p1 = self.getCenterPos(self.start)
        p2 = self.getCenterPos(self.end) if self.end else self.targetPos

        if not p1 or not p2:
            return

        # Adjust line ends to stop at node edge instead of center
        p1_edge = self.adjust_position(p1, p2, self.node_size / 2)
        p2_edge = self.adjust_position(p2, p1, self.node_size / 2)

        self._line = QLineF(p1_edge, p2_edge)
        self.setLine(self._line)

    def adjust_position(self, center, target, radius):
        if not center or not target:
            return center or QPointF()
        angle = atan2(target.y() - center.y(), target.x() - center.x())
        return QPointF(
            center.x() + radius * cos(angle),
            center.y() + radius * sin(angle)
        )

    def _draw_arrow(self, painter):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        line = self.line()
        angle = atan2(line.dy(), line.dx())
        arrow_size = self.arrow_size

        arrow_p1 = line.p2()
        arrow_p2 = arrow_p1 + QPointF(arrow_size * cos(angle + radians(150)),
                                      arrow_size * sin(angle + radians(150)))
        arrow_p3 = arrow_p1 + QPointF(arrow_size * cos(angle - radians(150)),
                                      arrow_size * sin(angle - radians(150)))
        painter.setBrush(QBrush(QColor("black")))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(QPolygonF([arrow_p1, arrow_p2, arrow_p3]))
        painter.restore()

    def _draw_label(self, painter):
        painter.save()
        mid_point = self.line().pointAt(0.5)
        painter.setPen(QPen(QColor("blue")))
        painter.drawText(mid_point, str(self.label))
        painter.restore()

    def remove(self):
        self._unregister_from_nodes()
        if self.scene():
            try:
                self.scene().removeItem(self)
            except Exception:
                pass
        self.start = None
        self.end = None
        self.targetPos = None

    def __del__(self):
        self._unregister_from_nodes()
