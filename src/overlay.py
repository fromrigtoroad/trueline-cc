from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import QPointF
import numpy as np

from settings import (
    OVERLAY_WIDTH, OVERLAY_HEIGHT, OVERLAY_X, OVERLAY_Y, OVERLAY_OPACITY,
    TRACE_WINDOW, COLOR_LIVE_THROTTLE, COLOR_REF_THROTTLE,
    COLOR_LIVE_BRAKE, COLOR_REF_BRAKE, COLOR_BACKGROUND, POLL_INTERVAL_MS,
)
from live_reader import LiveReader
from ibt_parser import ReferenceLap

# Display modes
MODE_BARS    = "bars"
MODE_TRACE   = "trace"
MODE_FULL    = "full"


class OverlayWindow(QWidget):
    def __init__(self, live: LiveReader, reference: ReferenceLap | None = None):
        super().__init__()
        self.live = live
        self.reference = reference
        self.mode = MODE_TRACE
        self._drag_pos = None
        self._live_sample = None

        self._setup_window()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(POLL_INTERVAL_MS)

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(OVERLAY_OPACITY)
        self.resize(OVERLAY_WIDTH, OVERLAY_HEIGHT)
        self.move(OVERLAY_X, OVERLAY_Y)

    def set_reference(self, ref: ReferenceLap):
        self.reference = ref

    def set_mode(self, mode: str):
        self.mode = mode
        self.update()

    def _tick(self):
        self._live_sample = self.live.sample()
        self.update()

    # ── Dragging ──────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Painting ──────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        p.setBrush(QBrush(QColor(*COLOR_BACKGROUND)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 8, 8)

        connected = self.live.is_connected()
        sample = self._live_sample

        if not connected or sample is None:
            self._draw_status(p, "Waiting for iRacing...")
            return

        if not sample.get('on_track'):
            self._draw_status(p, "Not on track")
            return

        if self.mode == MODE_BARS:
            self._draw_bars(p, sample)
        elif self.mode == MODE_TRACE:
            self._draw_trace(p, sample)
        elif self.mode == MODE_FULL:
            self._draw_full(p, sample)

    def _draw_status(self, p: QPainter, msg: str):
        p.setPen(QColor(180, 180, 180))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, msg)

    # ── Mode: Bars ─────────────────────────────────────────────────────────────

    def _draw_bars(self, p: QPainter, sample: dict):
        w, h = self.width(), self.height()
        pad = 12
        bar_h = (h - pad * 3) // 2
        bar_w = w - pad * 2

        live_t = sample['throttle']
        live_b = sample['brake']
        ref_t = ref_b = None

        if self.reference:
            ref_t, ref_b = self.reference.sample_at(sample['lap_dist_pct'])

        # Throttle row
        ty = pad
        self._draw_bar_row(p, pad, ty, bar_w, bar_h, live_t, ref_t,
                           COLOR_LIVE_THROTTLE, COLOR_REF_THROTTLE, "T")

        # Brake row
        by = pad * 2 + bar_h
        self._draw_bar_row(p, pad, by, bar_w, bar_h, live_b, ref_b,
                           COLOR_LIVE_BRAKE, COLOR_REF_BRAKE, "B")

    def _draw_bar_row(self, p, x, y, w, h, live_val, ref_val, live_color, ref_color, label):
        # Background track
        p.setBrush(QBrush(QColor(40, 40, 40)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(x, y, w, h)

        half = h // 2

        # Reference bar (top half)
        if ref_val is not None:
            p.setBrush(QBrush(QColor(*ref_color)))
            p.drawRect(x, y, int(w * ref_val), half - 1)

        # Live bar (bottom half)
        p.setBrush(QBrush(QColor(*live_color)))
        p.drawRect(x, y + half, int(w * live_val), half)

        # Label
        p.setPen(QColor(200, 200, 200))
        p.drawText(x - 14, y, 14, h, Qt.AlignmentFlag.AlignCenter, label)

    # ── Mode: Scrolling trace ──────────────────────────────────────────────────

    def _draw_trace(self, p: QPainter, sample: dict):
        w, h = self.width(), self.height()
        pad = 10
        center_pct = sample['lap_dist_pct']

        half_w = TRACE_WINDOW

        # Row heights
        row_h = (h - pad * 3) // 2
        t_top = pad
        b_top = pad * 2 + row_h

        live_t = sample['throttle']
        live_b = sample['brake']

        if self.reference:
            dist, ref_t, ref_b = self.reference.slice(center_pct, half_w)
            self._draw_trace_row(p, pad, t_top, w - pad * 2, row_h,
                                  center_pct, half_w, dist, ref_t,
                                  live_t, COLOR_LIVE_THROTTLE, COLOR_REF_THROTTLE, "T")
            self._draw_trace_row(p, pad, b_top, w - pad * 2, row_h,
                                  center_pct, half_w, dist, ref_b,
                                  live_b, COLOR_LIVE_BRAKE, COLOR_REF_BRAKE, "B")
        else:
            self._draw_status(p, "No reference loaded")

        # Center cursor line
        cx = pad + (w - pad * 2) // 2
        p.setPen(QPen(QColor(255, 255, 255, 180), 1))
        p.drawLine(cx, t_top, cx, b_top + row_h)

    def _draw_trace_row(self, p, x, y, w, h, center, half_w,
                         ref_dist, ref_vals, live_val,
                         live_color, ref_color, label):
        p.setBrush(QBrush(QColor(40, 40, 40)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(x, y, w, h)

        def dist_to_x(d):
            return x + int((d - (center - half_w)) / (2 * half_w) * w)

        # Reference trace (filled polygon)
        if len(ref_dist) > 1:
            pts = []
            pts.append(QPointF(dist_to_x(ref_dist[0]), y + h))
            for d, v in zip(ref_dist, ref_vals):
                pts.append(QPointF(dist_to_x(d), y + h - v * h))
            pts.append(QPointF(dist_to_x(ref_dist[-1]), y + h))
            color = QColor(*ref_color)
            p.setBrush(QBrush(color))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(QPolygonF(pts))

        # Live value: vertical line at center
        cx = x + w // 2
        live_y = int(y + h - live_val * h)
        p.setPen(QPen(QColor(*live_color), 2))
        p.drawLine(cx, y + h, cx, live_y)

        p.setPen(QColor(200, 200, 200))
        p.drawText(x - 14, y, 14, h, Qt.AlignmentFlag.AlignCenter, label)

    # ── Mode: Full lap ─────────────────────────────────────────────────────────

    def _draw_full(self, p: QPainter, sample: dict):
        if not self.reference:
            self._draw_status(p, "No reference loaded")
            return

        w, h = self.width(), self.height()
        pad = 10
        row_h = (h - pad * 3) // 2
        t_top = pad
        b_top = pad * 2 + row_h

        dist = self.reference.dist

        self._draw_full_row(p, pad, t_top, w - pad * 2, row_h,
                             dist, self.reference.throttle, sample['throttle'],
                             sample['lap_dist_pct'],
                             COLOR_LIVE_THROTTLE, COLOR_REF_THROTTLE, "T")
        self._draw_full_row(p, pad, b_top, w - pad * 2, row_h,
                             dist, self.reference.brake, sample['brake'],
                             sample['lap_dist_pct'],
                             COLOR_LIVE_BRAKE, COLOR_REF_BRAKE, "B")

    def _draw_full_row(self, p, x, y, w, h, dist, ref_vals, live_val, pct,
                        live_color, ref_color, label):
        p.setBrush(QBrush(QColor(40, 40, 40)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(x, y, w, h)

        if len(dist) > 1:
            pts = [QPointF(x + dist[0] * w, y + h)]
            for d, v in zip(dist, ref_vals):
                pts.append(QPointF(x + d * w, y + h - v * h))
            pts.append(QPointF(x + dist[-1] * w, y + h))
            p.setBrush(QBrush(QColor(*ref_color)))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(QPolygonF(pts))

        # Cursor
        cx = x + int(pct * w)
        p.setPen(QPen(QColor(255, 255, 255, 200), 1))
        p.drawLine(cx, y, cx, y + h)

        p.setPen(QColor(200, 200, 200))
        p.drawText(x - 14, y, 14, h, Qt.AlignmentFlag.AlignCenter, label)
