import io
import os

from PyQt5 import QtGui
from PyQt5.QtGui import QKeyEvent

import constants
from managers import js_manager
from PIL import Image
from PyQt5.QtCore import Qt, QBuffer, QByteArray, QPoint, QPointF
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QGraphicsScene, QGraphicsPixmapItem

from widgets.GraphEdge import GraphEdge
from widgets.GraphItem import GraphItem

from .GraphSceneProperties import GraphSceneProperties


class GraphScene(QGraphicsScene):

    def __init__(self, parent):
        super().__init__(parent)
        self.graphSceneProperties = GraphSceneProperties()
        self.graphSceneProperties.application_icon_size = constants.ApplicationIconSize.Small

        # Track created items for cleanup
        self._node_items = []
        self._edge_items = []

    def add_node(self, position, attributes):
        offset = 50
        position = QPoint(position.x() - offset, position.y() - offset)

        image = ''
        for item in js_manager.data[attributes["Group"]]:
            if item['label'] == attributes["Type"]:
                image = item['icon']
                break

        attributes["Label"] = "Node Name"
        attributes["Position"] = self.__pos_to_str([position.x(), position.y()])
        attributes["Image"] = {"name": "", "image": ""}
        attributes["Image Scale"] = True

        # build pixmap
        icon_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + r"\images\\" + image
        pixmap = QPixmap(icon_path)
        pixmap = pixmap.scaled(
            self.graphSceneProperties.application_icon_size,
            self.graphSceneProperties.application_icon_size,
            Qt.KeepAspectRatio
        )

        # build graph item
        graphItem = GraphItem(pixmap)
        graphItem.setZValue(1)
        graphItem.label = attributes["Type"]
        graphItem.attributes = attributes
        graphItem.setPos(position)
        graphItem.setAcceptHoverEvents(True)

        fullscreen_canvas_width = self.parent().width()
        fullscreen_canvas_height = self.parent().height()
        self.setSceneRect(0, 0, fullscreen_canvas_width - offset, fullscreen_canvas_height - offset)

        # add item to scene
        self.addItem(graphItem)
        self._node_items.append(graphItem)  # track for cleanup

    @staticmethod
    def __pos_to_str(position):
        return ";".join(map(str, position))

    @staticmethod
    def __str_to_pos(text):
        return list(map(float, text.split(";")))

    @staticmethod
    def __str_to_image(val: str) -> Image:
        img = QImage.fromData(GraphScene.__str_to_q_byte_array(val))
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        img.save(buffer, "PNG")
        pil_im = Image.open(io.BytesIO(buffer.data()))
        buffer.close()
        return pil_im

    @staticmethod
    def __str_to_q_byte_array(val: str) -> QByteArray:
        q_byte_array = QByteArray(val.encode())
        q_byte_array = QByteArray.fromBase64(q_byte_array)
        return q_byte_array

    def dragEnterEvent(self, event):
        if event.mimeData().hasImage():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        pos = event.pos()
        mimeData = event.mimeData()
        pixMap = QPixmap(mimeData)

        newPix = QGraphicsPixmapItem(pixMap)
        event.setDropAction(Qt.DropActions.MoveAction)
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasImage():
            event.accept()
        else:
            event.ignore()

    startItem = newConnection = None

#    def controlPointAt(self, pos):
#        mask = QtGui.QPainterPath()
#        mask.setFillRule(Qt.WindingFill)
#        for item in self.items(pos):
#            if mask.contains(pos):
#                return
#            if isinstance(item, GraphItem):
#                return item
#            if not isinstance(item, GraphEdge):
#                mask.addPath(item.shape().translated(item.scenePos()))


    def controlPointAt(self, pos):
        for item in self.items(pos):
            if isinstance(item, GraphItem):
                return item
        return None


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.ShiftModifier:
            item = self.controlPointAt(event.scenePos())
            if item:
                self.startItem = item
                centerPos = self.getCenterPos(item)
                self.newConnection = GraphEdge(item, centerPos)
                self.newConnection.setZValue(-1)
                self.addItem(self.newConnection)
                self._edge_items.append(self.newConnection)  # track edge for cleanup

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.newConnection:
            item = self.controlPointAt(event.scenePos())
            if item and item != self.startItem:
                p2 = self.getCenterPos(item)
            else:
                p2 = event.scenePos()
            self.newConnection.setP2(p2)
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        item = self.controlPointAt(event.scenePos())
        if self.newConnection:
            if item and item != self.startItem:
                self.newConnection.setEnd(item)
                if self.startItem.addLine(self.newConnection):
                    item.addLine(self.newConnection)
                    if not item.has_parent():
                        self.startItem.add_child(item)
                else:
                    self.startItem.removeLine(self.newConnection)
                    self.removeItem(self.newConnection)
                    if self.newConnection in self._edge_items:
                        self._edge_items.remove(self.newConnection)
            else:
                self.removeItem(self.newConnection)
                if self.newConnection in self._edge_items:
                    self._edge_items.remove(self.newConnection)

        self.startItem = self.newConnection = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            selected_items = self.selectedItems()
            for item in selected_items:
                if isinstance(item, GraphItem):
                    self.delete_node(item)
                elif isinstance(item, GraphEdge):
                    self.remove_edge(item)

            self.clearSelection()
            self.update()
        else:
            super().keyPressEvent(event)

    def getCenterPos(self, item):
        """Helper method to get the center of the item"""
        rect = item.boundingRect()
        return item.scenePos() + QPointF(rect.width() / 2, rect.height() / 2)

    # 🧹 Cleanup Method
    def clear_scene_and_references(self):
        """Safely remove all items and release Python-side references."""
        # Remove all edge and node items
        for edge in getattr(self, "_edge_items", []):
            try:
                self.removeItem(edge)
                del edge
            except Exception:
                pass
        self._edge_items.clear()

        for node in getattr(self, "_node_items", []):
            try:
                self.removeItem(node)
                del node
            except Exception:
                pass
        self._node_items.clear()

        # Finally clear the QGraphicsScene itself
        self.clear()
        self.startItem = None
        self.newConnection = None
        self.update()

    def delete_node(self, node_item: GraphItem):
            """Remove a node and its attached edges from the scene and internal state."""
            # 1. Remove connected edges first
            edges_to_remove = []
            # Suppose GraphItem has e.g. node_item.edges (list of GraphEdge)
            for edge in getattr(node_item, "edges", []):
                try:
                    self.removeItem(edge)
                except Exception:
                    pass
                if edge in self._edge_items:
                    self._edge_items.remove(edge)
            # Optionally clear back-references
            if hasattr(node_item, "edges"):
                node_item.edges.clear()
            
            # 2. Remove the node item
            try:
                self.removeItem(node_item)
            except Exception:
                pass
            if node_item in self._node_items:
                self._node_items.remove(node_item)
            
            # 3. Break any references in node_item itself
            # For example, if node_item had pointers to parent/child nodes or edges:
            for attr in ("parent", "children", "lines", "edges"):
                if hasattr(node_item, attr):
                    try:
                        setattr(node_item, attr, None)
                    except:
                        pass

            # 4. Optionally delete it (or let GC reclaim)
            try:
                del node_item
            except:
                pass

            # 5. Update scene and UI
            self.update()

    def remove_edge(self, edge: GraphEdge):
        """Remove an edge and clean up references."""
        try:
            self.removeItem(edge)
        except Exception:
            pass

        if edge in self._edge_items:
            self._edge_items.remove(edge)

        # Clean references from start and end nodes
        if edge.start and hasattr(edge.start, "edges"):
            if edge in edge.start.edges:
                edge.start.edges.remove(edge)

        if edge.end and hasattr(edge.end, "edges"):
            if edge in edge.end.edges:
                edge.end.edges.remove(edge)

        try:
            del edge
        except:
            pass

    def __del__(self):
        print("GraphScene is being deleted")
        """Destructor to ensure cleanup when the scene is deleted."""
        try:
            self.clear_scene_and_references()
        except Exception as e:
            print(f"GraphScene cleanup error during deletion: {e}")
