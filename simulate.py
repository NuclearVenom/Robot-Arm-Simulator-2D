import sys
import math
import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSlider, QFrame, QGroupBox, QSizePolicy, QStackedWidget,
    QPushButton, QDialog, QScrollArea, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics,
    QPainterPath, QPalette, QLinearGradient
)


# ══════════════════════════════════════════════
#  Design tokens
# ══════════════════════════════════════════════
CLR_BG          = QColor("#FFFFFF")
CLR_PANEL       = QColor("#F8F9FA")
CLR_BORDER      = QColor("#E2E6EA")
CLR_GRID_MINOR  = QColor("#F0F2F5")
CLR_GRID_MAJOR  = QColor("#D8DDE3")
CLR_AXIS        = QColor("#9AA3AD")
CLR_AXIS_LABEL  = QColor("#6C757D")
CLR_WORKSPACE   = QColor("#EBF3FB")
CLR_WORKSPACE_B = QColor("#C8DFEF")

CLR_SEG1        = QColor("#187CFF")   # upper arm
CLR_SEG2        = QColor("#4198F5")   # forearm
CLR_SEG3        = QColor("#65B5FC")   # wrist link
CLR_SEG4        = QColor("#A0D4FF")   # finger link (4-DOF)
CLR_J_BASE      = QColor("#202124")
CLR_J_ELBOW     = QColor("#1A73E8")
CLR_J_WRIST     = QColor("#4A9EF5")
CLR_J_FINGER    = QColor("#88C8FF")   # 4th joint
CLR_END         = QColor("#34A853")
CLR_END_OUT     = QColor("#1E7E3E")
CLR_TARGET      = QColor("#EA4335")
CLR_TARGET_FILL = QColor(234, 67, 53, 40)

CLR_TEXT_PRIM   = QColor("#202124")
CLR_TEXT_SEC    = QColor("#5F6368")
CLR_TEXT_VAL    = QColor("#1A73E8")
CLR_OK          = QColor("#34A853")
CLR_WARN        = QColor("#FBBC04")
CLR_ERR         = QColor("#EA4335")
CLR_MOV         = QColor("#1A73E8")

# 3-position toggle colours: left=2-DOF  mid=3-DOF  right=4-DOF
CLR_PILL_0      = QColor("#65A0FF")   # 2-DOF
CLR_PILL_1      = QColor("#167BFF")   # 3-DOF
CLR_PILL_2      = QColor("#0A4FD6")   # 4-DOF
CLR_KNOB        = QColor("#FFFFFF")

FONT            = "Segoe UI"
MAJOR_EVERY     = 5
MORPH_SPEED     = 0.05   # fixed morph step per tick


# ══════════════════════════════════════════════
#  Easing
# ══════════════════════════════════════════════
def ease_in_out(t: float) -> float:
    """Cubic ease-in-out, t ∈ [0, 1]."""
    return t * t * (3.0 - 2.0 * t)

def lerp_color(a: QColor, b: QColor, t: float) -> QColor:
    return QColor(
        int(a.red()   + t * (b.red()   - a.red())),
        int(a.green() + t * (b.green() - a.green())),
        int(a.blue()  + t * (b.blue()  - a.blue())),
    )


# ══════════════════════════════════════════════
#  3-position sliding pill toggle widget
# ══════════════════════════════════════════════
class TriToggle(QWidget):
    """
    Segmented-control style 3-position toggle.
    Positions: 0 = 2-DOF (left), 1 = 3-DOF (centre), 2 = 4-DOF (right).
    Visual: white capsule with blue outline; dark pill slides to active segment.
    Emits toggled(int) when clicked.
    """

    LABELS = ["2-DOF", "3-DOF", "4-DOF"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pos     = 0       # logical 0/1/2
        self._anim_t  = 0.0    # 0.0 = left, 1.0 = centre, 2.0 = right
        self._timer   = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._animate)
        # 3 x 72 px segments = 216 px wide, 36 px tall
        self.setFixedSize(216, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.toggled = None   # callable(int)

    # ── state ──────────────────────────────────
    @property
    def position(self) -> int:
        return self._pos

    def set_position(self, pos: int, animate: bool = True):
        self._pos = max(0, min(2, pos))
        if animate:
            self._timer.start()
        else:
            self._anim_t = float(self._pos)
            self.update()

    # ── animation ──────────────────────────────
    def _animate(self):
        target = float(self._pos)
        diff   = target - self._anim_t
        if abs(diff) < 0.02:
            self._anim_t = target
            self._timer.stop()
        else:
            self._anim_t += diff * 0.18
        self.update()

    # ── events ─────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            w = self.width()
            new_pos = max(0, min(2, int(event.x() * 3 / w)))
            prev    = self._pos
            self._pos = new_pos
            self._timer.start()          # always animate to confirm click
            if new_pos != prev and self.toggled:
                self.toggled(new_pos)

    # ── painting ───────────────────────────────
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)

        w, h = self.width(), self.height()
        t    = self._anim_t          # animated position: 0.0 / 1.0 / 2.0

        seg_w   = w / 3.0            # width of one segment
        pad     = 3                  # inset of active pill from segment edges
        r_outer = h / 2.0            # outer capsule corner radius

        # Active pill colour: interpolates along the blue gradient
        # 0 (2-DOF) → deep blue #187CFF
        # 1 (3-DOF) → medium blue #4198F5
        # 2 (4-DOF) → light blue #65B5FC
        if t <= 1.0:
            pill_clr = lerp_color(CLR_SEG1, CLR_SEG2, ease_in_out(t))
        else:
            pill_clr = lerp_color(CLR_SEG2, CLR_SEG3, ease_in_out(t - 1.0))

        # ── 1. Outer capsule: light-blue tint background + colour-matched border ──
        p.setPen(QPen(pill_clr, 1.5))
        p.setBrush(QBrush(QColor("#EBF3FB")))
        p.drawRoundedRect(QRectF(0.75, 0.75, w - 1.5, h - 1.5), r_outer, r_outer)

        # ── 2. Sliding coloured active pill ──
        pill_w = seg_w - pad * 2
        pill_h = h - pad * 2
        pill_x = t * seg_w + pad
        pill_y = float(pad)
        r_pill = pill_h / 2.0

        # Drop-shadow
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 22)))
        p.drawRoundedRect(QRectF(pill_x + 1, pill_y + 1.5, pill_w, pill_h),
                          r_pill, r_pill)

        # Pill body
        p.setBrush(QBrush(pill_clr))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(pill_x, pill_y, pill_w, pill_h), r_pill, r_pill)

        # ── 3. Labels — all three always visible ──
        font = QFont(FONT, 8, QFont.DemiBold)
        p.setFont(font)

        pill_centre = t + 0.5
        for i in range(3):
            lbl_rect = QRectF(i * seg_w, 0, seg_w, h)

            # White on the active pill, dark blue on the background
            dist  = abs((i + 0.5) - pill_centre)
            blend = max(0.0, min(1.0, 1.0 - dist / 0.75))

            rv = int(255 * blend +  24 * (1 - blend))
            gv = int(255 * blend +  90 * (1 - blend))
            bv = int(255 * blend + 168 * (1 - blend))
            p.setPen(QColor(rv, gv, bv))
            p.drawText(lbl_rect, Qt.AlignCenter, self.LABELS[i])

        p.end()



# ══════════════════════════════════════════════
#  Canvas
# ══════════════════════════════════════════════
class ArmCanvas(QWidget):
    """
    Unified canvas for 2-DOF, 3-DOF and 4-DOF modes.

    mode ∈ {0, 1, 2}  →  2-DOF / 3-DOF / 4-DOF

    morph_t  ∈ [0, 1]:  0 = wrist link invisible  (2-DOF look)
                         1 = wrist link fully visible
    morph_t2 ∈ [0, 1]:  0 = finger link invisible (2/3-DOF look)
                         1 = finger link fully visible (4-DOF look)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 600)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

        # ── Arm geometry (pixels) ──────────────
        self.L1 = 120
        self.L2 =  90
        self.L3 =  70   # wrist link
        self.L4 =  55   # finger link  (4-DOF only)

        # ── Mode & morph ───────────────────────
        self.mode     = 0       # 0=2DOF  1=3DOF  2=4DOF
        self.morph_t  = 0.0    # 2↔3 (wrist segment)
        self.morph_t2 = 0.0    # 3↔4 (finger segment)
        self._morphing  = False

        # ── Joint angles (rad) ─────────────────
        self.theta1 = math.pi / 4
        self.theta2 = math.pi / 3
        self.theta3 = math.pi / 6
        self.theta4 = math.pi / 8   # finger; ignored in 2/3-DOF

        # ── Target angles ──────────────────────
        self.target_theta1 = self.theta1
        self.target_theta2 = self.theta2
        self.target_theta3 = self.theta3
        self.target_theta4 = self.theta4

        # ── Target position ────────────────────
        self.target_x: float | None = None
        self.target_y: float | None = None

        # ── Hover ──────────────────────────────
        self.hover_x: float | None = None
        self.hover_y: float | None = None

        # ── Animation ─────────────────────────
        self.speed     = 0.20
        self.moving    = False
        self.TOLERANCE = 0.005

        # ── Callbacks ─────────────────────────
        self.on_status_change   = None
        self.on_angles_change   = None
        self.on_position_change = None
        self.on_target_change   = None
        self.on_morph_done      = None   # called when morph finishes

    # ── Coordinate helpers ────────────────────
    def _origin(self) -> QPointF:
        return QPointF(self.width() / 2, self.height() / 2)

    def _scale(self) -> float:
        return 20.0

    def arm_to_canvas(self, ax: float, ay: float) -> QPointF:
        o = self._origin()
        return QPointF(o.x() + ax, o.y() - ay)

    def canvas_to_arm(self, cx: float, cy: float) -> tuple[float, float]:
        o = self._origin()
        return cx - o.x(), o.y() - cy

    def arm_to_cartesian(self, ax: float, ay: float) -> tuple[float, float]:
        return ax / self._scale(), ay / self._scale()

    # ── Effective link lengths (morph-aware) ──
    def _L3_eff(self) -> float:
        return self.L3 * ease_in_out(self.morph_t)

    def _L4_eff(self) -> float:
        return self.L4 * ease_in_out(self.morph_t2)

    # ── Forward kinematics ────────────────────
    def forward_kinematics(self, t1, t2, t3, t4,
                            l3_override=None, l4_override=None) -> tuple:
        """
        Returns (ex, ey, wx, wy, fx, fy, gx, gy).
        ex/ey = elbow, wx/wy = wrist, fx/fy = finger joint, gx/gy = end-effector.
        """
        L3 = l3_override if l3_override is not None else self._L3_eff()
        L4 = l4_override if l4_override is not None else self._L4_eff()
        a12   = t1 + t2
        a123  = t1 + t2 + t3
        a1234 = t1 + t2 + t3 + t4
        ex = self.L1 * math.cos(t1)
        ey = self.L1 * math.sin(t1)
        wx = ex + self.L2 * math.cos(a12)
        wy = ey + self.L2 * math.sin(a12)
        fx = wx + L3 * math.cos(a123)
        fy = wy + L3 * math.sin(a123)
        gx = fx + L4 * math.cos(a1234)
        gy = fy + L4 * math.sin(a1234)
        return ex, ey, wx, wy, fx, fy, gx, gy

    # ── Inverse kinematics ───────────────────
    def _ik_2dof(self, px, py):
        """Closed-form 2-DOF IK. Returns (t1, t2) or None."""
        r2 = px * px + py * py
        r  = math.sqrt(r2)
        if r > self.L1 + self.L2 + 1e-6:
            return None
        if r < abs(self.L1 - self.L2) - 1e-6:
            return None
        try:
            cos2 = (r2 - self.L1**2 - self.L2**2) / (2.0 * self.L1 * self.L2)
            cos2 = max(-1.0, min(1.0, cos2))
            t2   = math.acos(cos2)
            alpha = math.atan2(py, px)
            beta  = math.atan2(self.L2 * math.sin(t2),
                               self.L1 + self.L2 * math.cos(t2))
            t1 = alpha - beta
            return t1, t2
        except (ValueError, ZeroDivisionError):
            return None

    def _ik_3dof(self, px, py):
        """
        φ-sweep 3-DOF IK using the current effective L3.
        Returns (t1, t2, t3) or None.
        """
        L3        = self._L3_eff()
        PHI_STEPS = 360
        best      = None
        best_cost = math.inf
        for i in range(PHI_STEPS):
            phi = -math.pi + 2.0 * math.pi * i / PHI_STEPS
            wx  = px - L3 * math.cos(phi)
            wy  = py - L3 * math.sin(phi)
            r2  = wx * wx + wy * wy
            r   = math.sqrt(r2)
            if r > self.L1 + self.L2 + 1e-6:
                continue
            if r < abs(self.L1 - self.L2) - 1e-6:
                continue
            try:
                cos2  = (r2 - self.L1**2 - self.L2**2) / (2.0 * self.L1 * self.L2)
                cos2  = max(-1.0, min(1.0, cos2))
                alpha = math.atan2(wy, wx)
                for sign in (+1.0, -1.0):
                    t2   = sign * math.acos(cos2)
                    beta = math.atan2(self.L2 * math.sin(t2),
                                      self.L1 + self.L2 * math.cos(t2))
                    t1   = alpha - beta
                    t3   = phi - t1 - t2
                    *_, fx, fy, _, _ = self.forward_kinematics(
                        t1, t2, t3, 0.0, l3_override=L3, l4_override=0.0)
                    if math.hypot(fx - px, fy - py) > 1.5:
                        continue
                    cost = (abs(t1 - self.theta1) +
                            abs(t2 - self.theta2) +
                            abs(t3 - self.theta3))
                    if cost < best_cost:
                        best_cost = cost
                        best      = (t1, t2, t3)
            except (ValueError, ZeroDivisionError):
                continue
        return best

    def _ik_4dof(self, px, py):
        """
        Double φ-sweep 4-DOF IK using the current effective L3 and L4.
        Outer sweep: psi = total orientation (t1+t2+t3+t4).
        Inner analytic: given psi, the finger-joint wrist centre is found,
        then phi = t1+t2+t3 is swept for the 3-DOF sub-problem.
        Returns (t1, t2, t3, t4) or None.
        """
        L3 = self._L3_eff()
        L4 = self._L4_eff()
        PSI_STEPS = 180
        PHI_STEPS = 180
        best      = None
        best_cost = math.inf
        for i in range(PSI_STEPS):
            psi = -math.pi + 2.0 * math.pi * i / PSI_STEPS
            # finger joint position (back-project from end-effector)
            fx = px - L4 * math.cos(psi)
            fy = py - L4 * math.sin(psi)
            for j in range(PHI_STEPS):
                phi = -math.pi + 2.0 * math.pi * j / PHI_STEPS
                wx  = fx - L3 * math.cos(phi)
                wy  = fy - L3 * math.sin(phi)
                r2  = wx * wx + wy * wy
                r   = math.sqrt(r2)
                if r > self.L1 + self.L2 + 1e-6:
                    continue
                if r < abs(self.L1 - self.L2) - 1e-6:
                    continue
                try:
                    cos2  = (r2 - self.L1**2 - self.L2**2) / (2.0 * self.L1 * self.L2)
                    cos2  = max(-1.0, min(1.0, cos2))
                    alpha = math.atan2(wy, wx)
                    for sign in (+1.0, -1.0):
                        t2   = sign * math.acos(cos2)
                        beta = math.atan2(self.L2 * math.sin(t2),
                                          self.L1 + self.L2 * math.cos(t2))
                        t1   = alpha - beta
                        t3   = phi - t1 - t2
                        t4   = psi - t1 - t2 - t3
                        # verify
                        *_, gx, gy = self.forward_kinematics(
                            t1, t2, t3, t4, l3_override=L3, l4_override=L4)
                        if math.hypot(gx - px, gy - py) > 1.5:
                            continue
                        cost = (abs(t1 - self.theta1) +
                                abs(t2 - self.theta2) +
                                abs(t3 - self.theta3) +
                                abs(t4 - self.theta4))
                        if cost < best_cost:
                            best_cost = cost
                            best      = (t1, t2, t3, t4)
                except (ValueError, ZeroDivisionError):
                    continue
        return best

    # ── Mode switching ────────────────────────
    def switch_mode(self, new_mode: int):
        """Begin morph to mode 0/1/2. Called by toggle."""
        new_mode = max(0, min(2, new_mode))
        # No-op if already in the requested mode and fully settled
        if new_mode == self.mode and not self._morphing:
            return
        self.mode      = new_mode
        self._morphing  = True
        self.moving     = False
        self.target_x   = None
        self.target_y   = None

    # ── Stepping (called by timer) ────────────
    def step(self):
        # 1. Advance morphs
        if self._morphing:
            # morph_t  → 0 for mode 0, 1 for modes 1 & 2
            tgt_t  = 0.0 if self.mode == 0 else 1.0
            # morph_t2 → 0 for modes 0 & 1, 1 for mode 2
            tgt_t2 = 1.0 if self.mode == 2 else 0.0

            d1  = tgt_t  - self.morph_t
            d2  = tgt_t2 - self.morph_t2
            done1 = abs(d1)  < MORPH_SPEED
            done2 = abs(d2)  < MORPH_SPEED

            self.morph_t  = tgt_t  if done1 else self.morph_t  + math.copysign(MORPH_SPEED, d1)
            self.morph_t2 = tgt_t2 if done2 else self.morph_t2 + math.copysign(MORPH_SPEED, d2)

            if done1 and done2:
                self._morphing = False
                if self.on_morph_done:
                    self.on_morph_done(self.mode)

        # 2. Advance arm motion
        if self.moving:
            d1 = self.target_theta1 - self.theta1
            d2 = self.target_theta2 - self.theta2
            d3 = self.target_theta3 - self.theta3
            d4 = self.target_theta4 - self.theta4
            tol = self.TOLERANCE
            if abs(d1) < tol and abs(d2) < tol and abs(d3) < tol and abs(d4) < tol:
                self.theta1 = self.target_theta1
                self.theta2 = self.target_theta2
                self.theta3 = self.target_theta3
                self.theta4 = self.target_theta4
                self.moving = False
                self._emit_status("Target reached", "ok")
            else:
                self.theta1 += d1 * self.speed
                self.theta2 += d2 * self.speed
                self.theta3 += d3 * self.speed
                self.theta4 += d4 * self.speed

        # 3. Fire callbacks
        *_, gx, gy = self.forward_kinematics(
            self.theta1, self.theta2, self.theta3, self.theta4)
        if self.on_angles_change:
            self.on_angles_change(
                math.degrees(self.theta1), math.degrees(self.theta2),
                math.degrees(self.theta3), math.degrees(self.theta4),
                self.morph_t, self.morph_t2)
        if self.on_position_change:
            cx, cy = self.arm_to_cartesian(gx, gy)
            self.on_position_change(cx, cy)

    # ── Target setting ────────────────────────
    def set_target(self, canvas_x: float, canvas_y: float):
        if self._morphing:
            return

        ax, ay    = self.canvas_to_arm(canvas_x, canvas_y)
        L3eff     = self._L3_eff()
        L4eff     = self._L4_eff()
        max_reach = self.L1 + self.L2 + L3eff + L4eff

        if math.hypot(ax, ay) > max_reach + 1e-6:
            self._emit_status("Target outside workspace", "error")
            return

        if self.mode == 0:
            result = self._ik_2dof(ax, ay)
            if result:
                t1, t2 = result
                t3 = self.theta3
                t4 = self.theta4
            else:
                self._emit_status("Unreachable position", "error")
                return
        elif self.mode == 1:
            result = self._ik_3dof(ax, ay)
            if result:
                t1, t2, t3 = result
                t4 = self.theta4
            else:
                self._emit_status("Unreachable position", "error")
                return
        else:  # mode == 2
            result = self._ik_4dof(ax, ay)
            if result:
                t1, t2, t3, t4 = result
            else:
                self._emit_status("Unreachable position", "error")
                return

        self.target_x, self.target_y = ax, ay
        self.target_theta1 = t1
        self.target_theta2 = t2
        self.target_theta3 = t3
        self.target_theta4 = t4
        self.moving = True
        self._emit_status("Moving to target", "moving")
        if self.on_target_change:
            cx, cy = self.arm_to_cartesian(ax, ay)
            self.on_target_change(cx, cy)

    def _emit_status(self, msg: str, kind: str):
        if self.on_status_change:
            self.on_status_change(msg, kind)

    # ── Qt events ─────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_target(event.x(), event.y())
            self.update()

    def mouseMoveEvent(self, event):
        ax, ay = self.canvas_to_arm(event.x(), event.y())
        self.hover_x, self.hover_y = self.arm_to_cartesian(ax, ay)
        self.update()

    def leaveEvent(self, event):
        self.hover_x = self.hover_y = None
        self.update()

    # ══════════════════════════════════════════
    #  Painting
    # ══════════════════════════════════════════
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        self._draw_background(p)
        self._draw_workspace(p)
        self._draw_grid(p)
        self._draw_axes(p)
        self._draw_arm(p)
        self._draw_target(p)
        self._draw_hover_info(p)
        p.end()

    def _draw_background(self, p):
        p.fillRect(self.rect(), CLR_BG)

    def _draw_workspace(self, p):
        o     = self._origin()
        L3eff = self._L3_eff()
        L4eff = self._L4_eff()
        R     = self.L1 + self.L2 + L3eff + L4eff
        p.setBrush(QBrush(CLR_WORKSPACE))
        p.setPen(QPen(CLR_WORKSPACE_B, 1.0, Qt.DashLine))
        p.drawEllipse(QPointF(o.x(), o.y()), R, R)

    def _draw_grid(self, p):
        w, h = self.width(), self.height()
        o    = self._origin()
        s    = self._scale()
        x_min = int(-o.x() / s) - 1
        x_max = int((w - o.x()) / s) + 1
        y_min = int(-(h - o.y()) / s) - 1
        y_max = int(o.y() / s) + 1

        for ix in range(x_min, x_max + 1):
            cx    = o.x() + ix * s
            major = (ix % MAJOR_EVERY == 0)
            p.setPen(QPen(CLR_GRID_MAJOR if major else CLR_GRID_MINOR,
                          1.0 if major else 0.5))
            p.drawLine(int(cx), 0, int(cx), h)

        for iy in range(y_min, y_max + 1):
            cy    = o.y() - iy * s
            major = (iy % MAJOR_EVERY == 0)
            p.setPen(QPen(CLR_GRID_MAJOR if major else CLR_GRID_MINOR,
                          1.0 if major else 0.5))
            p.drawLine(0, int(cy), w, int(cy))

    def _draw_axes(self, p):
        w, h = self.width(), self.height()
        o    = self._origin()
        s    = self._scale()

        p.setPen(QPen(CLR_AXIS, 1.5))
        p.drawLine(0, int(o.y()), w, int(o.y()))
        p.drawLine(int(o.x()), 0, int(o.x()), h)

        asz = 7
        p.setBrush(QBrush(CLR_AXIS))
        p.setPen(Qt.NoPen)
        p.drawPolygon(QPointF(w - 2, o.y()),
                      QPointF(w - 2 - asz, o.y() - asz / 2),
                      QPointF(w - 2 - asz, o.y() + asz / 2))
        p.drawPolygon(QPointF(o.x(), 2),
                      QPointF(o.x() - asz / 2, 2 + asz),
                      QPointF(o.x() + asz / 2, 2 + asz))

        font = QFont(FONT, 7)
        p.setFont(font)
        p.setPen(QPen(CLR_AXIS_LABEL))

        x_min = int(-o.x() / s) - 1
        x_max = int((w - o.x()) / s) + 1
        y_min = int(-(h - o.y()) / s) - 1
        y_max = int(o.y() / s) + 1

        for ix in range(x_min, x_max + 1):
            if ix == 0 or ix % MAJOR_EVERY:
                continue
            cx = o.x() + ix * s
            p.drawText(QRectF(cx - 20, o.y() + 4, 40, 12), Qt.AlignHCenter, str(ix))

        for iy in range(y_min, y_max + 1):
            if iy == 0 or iy % MAJOR_EVERY:
                continue
            cy = o.y() - iy * s
            p.drawText(QRectF(o.x() + 4, cy - 6, 24, 12), Qt.AlignLeft, str(iy))

        p.drawText(QRectF(o.x() + 4, o.y() + 4, 14, 12), Qt.AlignLeft, "0")

        lf = QFont(FONT, 8, QFont.Medium)
        lf.setItalic(True)
        p.setFont(lf)
        p.setPen(QPen(CLR_TEXT_SEC))
        p.drawText(int(w - 18), int(o.y()) - 10, "x")
        p.drawText(int(o.x()) + 8, 14, "y")

    def _draw_arm(self, p):
        ex, ey, wx, wy, fx, fy, gx, gy = self.forward_kinematics(
            self.theta1, self.theta2, self.theta3, self.theta4)
        L3eff = self._L3_eff()
        L4eff = self._L4_eff()

        base   = self._origin()
        elbow  = self.arm_to_canvas(ex, ey)
        wrist  = self.arm_to_canvas(wx, wy)
        finger = self.arm_to_canvas(fx, fy)
        end    = self.arm_to_canvas(gx, gy)

        # ── Shadows ──
        shd = QPen(QColor(0, 0, 0, 14), 10, Qt.SolidLine, Qt.RoundCap)
        p.setPen(shd)
        for a, b in [(base, elbow), (elbow, wrist)]:
            p.drawLine(QPointF(a.x() + 2, a.y() + 2),
                       QPointF(b.x() + 2, b.y() + 2))
        if L3eff > 0.5:
            p.drawLine(QPointF(wrist.x() + 2, wrist.y() + 2),
                       QPointF(finger.x() + 2, finger.y() + 2))
        if L4eff > 0.5:
            p.drawLine(QPointF(finger.x() + 2, finger.y() + 2),
                       QPointF(end.x() + 2, end.y() + 2))

        # ── Segment 1 — upper arm ──
        p.setPen(QPen(CLR_SEG1, 7, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(base, elbow)

        # ── Segment 2 — forearm ──
        p.setPen(QPen(CLR_SEG2, 6, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(elbow, wrist)

        # ── Segment 3 — wrist link (fades with morph_t) ──
        if L3eff > 0.5:
            alpha3 = int(255 * min(1.0, L3eff / self.L3))
            seg3_c = QColor(CLR_SEG3.red(), CLR_SEG3.green(), CLR_SEG3.blue(), alpha3)
            w3 = max(1, int(5 * L3eff / self.L3))
            p.setPen(QPen(seg3_c, w3, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(wrist, finger)

        # ── Segment 4 — finger link (fades with morph_t2) ──
        if L4eff > 0.5:
            alpha4 = int(255 * min(1.0, L4eff / self.L4))
            seg4_c = QColor(CLR_SEG4.red(), CLR_SEG4.green(), CLR_SEG4.blue(), alpha4)
            w4 = max(1, int(4 * L4eff / self.L4))
            p.setPen(QPen(seg4_c, w4, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(finger, end)

        # ── Draw joints ──
        def joint(c: QPointF, r_out: float, r_in: float,
                  fill: QColor, ring: QColor, alpha: int = 255):
            fill_a = QColor(fill.red(), fill.green(), fill.blue(), alpha)
            ring_a = QColor(ring.red(), ring.green(), ring.blue(), alpha)
            p.setPen(QPen(ring_a, 1.5))
            p.setBrush(QBrush(fill_a))
            p.drawEllipse(c, r_out, r_out)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(ring_a))
            p.drawEllipse(c, r_in, r_in)

        joint(base,  9, 4,   CLR_J_BASE,  QColor("#5F6368"))
        joint(elbow, 7, 3,   CLR_J_ELBOW, QColor("#0D47A1"))

        # Wrist joint fades in with morph_t
        w_alpha = int(255 * ease_in_out(self.morph_t))
        if w_alpha > 5:
            joint(wrist, 6, 2.5, CLR_J_WRIST, QColor("#1565C0"), w_alpha)

        # Finger joint fades in with morph_t2
        f_alpha = int(255 * ease_in_out(self.morph_t2))
        if f_alpha > 5:
            joint(finger, 5, 2, CLR_J_FINGER, QColor("#2E7BB5"), f_alpha)

        # End effector — always shown
        joint(end, 8, 3.5, CLR_END, CLR_END_OUT)

    def _draw_target(self, p):
        if self.target_x is None:
            return
        tc = self.arm_to_canvas(self.target_x, self.target_y)
        p.setBrush(QBrush(CLR_TARGET_FILL))
        p.setPen(QPen(CLR_TARGET, 2.0, Qt.DashLine))
        p.drawEllipse(tc, 10, 10)
        p.setPen(QPen(CLR_TARGET, 1.5))
        p.drawLine(QPointF(tc.x() - 16, tc.y()), QPointF(tc.x() + 16, tc.y()))
        p.drawLine(QPointF(tc.x(), tc.y() - 16), QPointF(tc.x(), tc.y() + 16))

    def _draw_hover_info(self, p):
        if self.hover_x is None:
            return
        font = QFont(FONT, 8)
        p.setFont(font)
        txt  = f"({self.hover_x:.1f}, {self.hover_y:.1f})"
        fm   = QFontMetrics(font)
        tw   = fm.horizontalAdvance(txt)
        rx, ry, pad = 12, self.height() - 28, 5
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 210)))
        p.drawRoundedRect(QRectF(rx - pad, ry - 11, tw + pad * 2, 18), 4, 4)
        p.setPen(QPen(CLR_TEXT_SEC))
        p.drawText(rx, ry + 2, txt)


# ══════════════════════════════════════════════
#  Sidebar helpers
# ══════════════════════════════════════════════
def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Plain)
    line.setStyleSheet("color: #E2E6EA;")
    return line


class MetricRow(QWidget):
    def __init__(self, label: str, initial: str = "—", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"color: {CLR_TEXT_SEC.name()}; font-size: 12px;")
        self._val = QLabel(initial)
        self._val.setStyleSheet(
            f"color: {CLR_TEXT_VAL.name()}; font-size: 12px; font-weight: 600;")
        self._val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(self._lbl)
        layout.addStretch()
        layout.addWidget(self._val)

    def set_value(self, text: str):
        self._val.setText(text)

    def set_faded(self, faded: bool):
        val_color = "rgba(26,115,232,100)" if faded else "rgba(26,115,232,255)"
        lbl_color = "rgba(95,99,104,100)"  if faded else "rgba(95,99,104,255)"
        self._val.setStyleSheet(
            f"color: {val_color}; font-size: 12px; font-weight: 600;")
        self._lbl.setStyleSheet(
            f"color: {lbl_color}; font-size: 12px;")


class SectionBox(QGroupBox):
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet(f"""
            QGroupBox {{
                font-family: '{FONT}'; font-size: 11px; font-weight: 600;
                color: {CLR_TEXT_SEC.name()};
                border: 1px solid {CLR_BORDER.name()};
                border-radius: 8px;
                margin-top: 8px;
                padding: 6px 8px 8px 8px;
                background: {CLR_PANEL.name()};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 6px; color: {CLR_TEXT_SEC.name()};
            }}
        """)
        self._inner = QVBoxLayout(self)
        self._inner.setContentsMargins(8, 16, 8, 8)
        self._inner.setSpacing(6)

    def add_widget(self, w: QWidget):
        self._inner.addWidget(w)


# ══════════════════════════════════════════════
#  Link length slider widget
# ══════════════════════════════════════════════
LINK_MIN_U = 2
LINK_MAX_U = 12

class LinkSlider(QWidget):
    """
    A labelled slider row for one link length.
    Enabled/disabled state managed through stylesheet swapping only.
    """

    def __init__(self, label: str, initial_px: float,
                 color: QColor, enabled: bool = True, parent=None):
        super().__init__(parent)
        self._scale    = 20.0
        self._color    = color
        self._enabled  = enabled
        self.on_change = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(3)

        top = QWidget()
        tl  = QHBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(4)

        self._lbl = QLabel(label)
        self._val_lbl = QLabel(f"{initial_px / self._scale:.0f} u")
        self._val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        tl.addWidget(self._lbl)
        tl.addStretch()
        tl.addWidget(self._val_lbl)
        root.addWidget(top)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(LINK_MIN_U, LINK_MAX_U)
        self._slider.setValue(int(round(initial_px / self._scale)))
        self._slider.valueChanged.connect(self._on_slider)
        root.addWidget(self._slider)

        hint = QLabel(f"Range  {LINK_MIN_U} – {LINK_MAX_U} u")
        hint.setStyleSheet(f"font-size: 9px; color: {CLR_TEXT_SEC.name()};")
        root.addWidget(hint)

        self._apply_style(enabled)

    def set_enabled(self, val: bool):
        self._enabled = val
        self._apply_style(val)

    def value_px(self) -> float:
        return self._slider.value() * self._scale

    def set_value_px(self, px: float):
        self._slider.blockSignals(True)
        self._slider.setValue(int(round(px / self._scale)))
        self._slider.blockSignals(False)
        self._val_lbl.setText(f"{int(round(px / self._scale))} u")

    def _on_slider(self, units: int):
        if not self._enabled:
            return
        px = units * self._scale
        self._val_lbl.setText(f"{units} u")
        if self.on_change:
            self.on_change(px)

    def _apply_style(self, enabled: bool):
        if enabled:
            lbl_color  = f"rgba({CLR_TEXT_SEC.red()},{CLR_TEXT_SEC.green()},{CLR_TEXT_SEC.blue()},255)"
            val_color  = f"rgba({self._color.red()},{self._color.green()},{self._color.blue()},255)"
            groove_bg  = CLR_BORDER.name()
            fill_color = self._color.name()
            handle_bg  = self._color.name()
            handle_bdr = "white"
        else:
            lbl_color  = f"rgba({CLR_TEXT_SEC.red()},{CLR_TEXT_SEC.green()},{CLR_TEXT_SEC.blue()},100)"
            val_color  = f"rgba({CLR_TEXT_SEC.red()},{CLR_TEXT_SEC.green()},{CLR_TEXT_SEC.blue()},100)"
            groove_bg  = CLR_GRID_MAJOR.name()
            fill_color = CLR_GRID_MAJOR.name()
            handle_bg  = CLR_BORDER.name()
            handle_bdr = CLR_GRID_MAJOR.name()

        self._lbl.setStyleSheet(f"font-size: 12px; color: {lbl_color};")
        self._val_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {val_color};")
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {groove_bg};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 14px; height: 14px; margin: -5px 0;
                background: {handle_bg};
                border-radius: 7px;
                border: 2px solid {handle_bdr};
            }}
            QSlider::sub-page:horizontal {{
                background: {fill_color};
                border-radius: 2px;
            }}
        """)


# ══════════════════════════════════════════════
#  Main window
# ══════════════════════════════════════════════
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Arm Simulator  —  2-DOF / 3-DOF / 4-DOF")
        self.resize(1180, 780)
        self._build_ui()
        self._apply_global_style()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)   # ~30 fps

    # ── Build UI ──────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # Canvas
        self.canvas = ArmCanvas()
        self.canvas.on_status_change   = self._on_status
        self.canvas.on_angles_change   = self._on_angles
        self.canvas.on_position_change = self._on_position
        self.canvas.on_target_change   = self._on_target
        self.canvas.on_morph_done      = self._on_morph_done
        rl.addWidget(self.canvas, stretch=1)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet(f"background: {CLR_PANEL.name()};")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(14, 18, 14, 18)
        sl.setSpacing(8)
        rl.addWidget(sidebar)

        # ── Title ──
        title = QLabel("Robot Arm Simulator")
        title.setStyleSheet(f"""
            font-family: '{FONT}'; font-size: 24px;
            font-weight: 700; color: {CLR_TEXT_PRIM.name()};
        """)
        sl.addWidget(title)

        subtitle = QLabel('Developed by <a href="https://github.com/NuclearVenom" '
                            'style="color:#1E7E3E; font-weight:bold;">'
                            'Ranasurya Ghosh</a>')
        subtitle.setStyleSheet(f"font-family: '{FONT}'; font-size: 17px; color: {CLR_TEXT_SEC.name()};")
        subtitle.setOpenExternalLinks(True)
        sl.addWidget(subtitle)
        sl.addWidget(_divider())

        # ── DOF Toggle ──
        dof_box = SectionBox("Degrees of Freedom")

        # Label row
        toggle_row = QWidget()
        tr_layout  = QHBoxLayout(toggle_row)
        tr_layout.setContentsMargins(0, 0, 0, 0)

        self._dof_label = QLabel("2-DOF")
        self._dof_label.setStyleSheet(
            f"font-family: '{FONT}'; font-size: 13px; font-weight: 700; "
            f"color: {CLR_TEXT_PRIM.name()};")

        self._toggle = TriToggle()
        self._toggle.toggled = self._on_toggle

        # Toggle is the only widget in this row (label removed per user request)
        tr_layout.addStretch()
        tr_layout.addWidget(self._toggle)
        tr_layout.addStretch()
        dof_box.add_widget(toggle_row)

        self._dof_desc = QLabel(
            "Two revolute joints.\nExact solution, no redundancy.")
        self._dof_desc.setWordWrap(True)
        self._dof_desc.setStyleSheet(
            f"font-family: '{FONT}'; font-size: 10px; color: {CLR_TEXT_SEC.name()};")
        dof_box.add_widget(self._dof_desc)
        sl.addWidget(dof_box)

        # ── Status ──
        status_box = SectionBox("Status")
        self._status_lbl = QLabel("Ready — click on the plane")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setStyleSheet(
            f"font-family: '{FONT}'; font-size: 12px; font-weight: 500; "
            f"color: {CLR_OK.name()};")
        status_box.add_widget(self._status_lbl)
        sl.addWidget(status_box)

        # ── Speed ──
        speed_box = SectionBox("Speed")
        sw = QWidget()
        swl = QHBoxLayout(sw)
        swl.setContentsMargins(0, 0, 0, 0)
        lbl_s = QLabel("Animation Speed")
        lbl_s.setStyleSheet(f"font-size: 12px; color: {CLR_TEXT_SEC.name()};")
        self._speed_val = QLabel("20 %")
        self._speed_val.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {CLR_TEXT_VAL.name()};")
        swl.addWidget(lbl_s); swl.addStretch(); swl.addWidget(self._speed_val)
        speed_box.add_widget(sw)
        self._spd_slider = QSlider(Qt.Horizontal)
        self._spd_slider.setRange(1, 20)
        self._spd_slider.setValue(20)
        self._spd_slider.setStyleSheet(self._slider_style())
        self._spd_slider.valueChanged.connect(self._on_speed_change)
        speed_box.add_widget(self._spd_slider)
        sl.addWidget(speed_box)

        # ── Joint Angles ──
        angles_box = SectionBox("Joint Angles")
        self._r_t1    = MetricRow("Shoulder  θ₁")
        self._r_t2    = MetricRow("Elbow     θ₂")
        self._r_t3    = MetricRow("Wrist     θ₃")
        self._r_t4    = MetricRow("Finger    θ₄")
        self._r_reach = MetricRow("Dist. from base")
        for r in (self._r_t1, self._r_t2, self._r_t3, self._r_t4, self._r_reach):
            angles_box.add_widget(r)
        sl.addWidget(angles_box)

        # ── End Effector ──
        pos_box = SectionBox("End Effector")
        self._r_ex = MetricRow("X")
        self._r_ey = MetricRow("Y")
        pos_box.add_widget(self._r_ex)
        pos_box.add_widget(self._r_ey)
        sl.addWidget(pos_box)

        # ── Target ──
        tgt_box = SectionBox("Target")
        self._r_tx = MetricRow("X")
        self._r_ty = MetricRow("Y")
        tgt_box.add_widget(self._r_tx)
        tgt_box.add_widget(self._r_ty)
        sl.addWidget(tgt_box)

        # ── Link Lengths ──
        arm_box = SectionBox("Link Lengths")

        self._sl_l1 = LinkSlider("Upper arm  L₁", self.canvas.L1, CLR_SEG1, enabled=True)
        self._sl_l2 = LinkSlider("Forearm    L₂", self.canvas.L2, CLR_SEG2, enabled=True)
        self._sl_l3 = LinkSlider("Wrist link L₃", self.canvas.L3, CLR_SEG3, enabled=False)
        self._sl_l4 = LinkSlider("Finger lnk L₄", self.canvas.L4, CLR_SEG4, enabled=False)

        self._sl_l1.on_change = self._on_l1_change
        self._sl_l2.on_change = self._on_l2_change
        self._sl_l3.on_change = self._on_l3_change
        self._sl_l4.on_change = self._on_l4_change

        self._r_ws = MetricRow(
            "Max reach",
            f"{(self.canvas.L1 + self.canvas.L2) / self.canvas._scale():.0f} u")

        for w in (self._sl_l1, self._sl_l2, self._sl_l3, self._sl_l4, self._r_ws):
            arm_box.add_widget(w)
        sl.addWidget(arm_box)

        # # ── Instructions ──
        # instr_box = SectionBox("Instructions")
        # self._instr_lbl = QLabel(
        #     "Click on the plane to set a target.\n\n"
        #     "Use the toggle to switch between\n"
        #     "2-DOF, 3-DOF and 4-DOF mode.\n"
        #     "The arm morphs between configurations."
        # )
        # self._instr_lbl.setWordWrap(True)
        # self._instr_lbl.setStyleSheet(
        #     f"font-family: '{FONT}'; font-size: 11px; color: {CLR_TEXT_SEC.name()};")
        # instr_box.add_widget(self._instr_lbl)
        # sl.addWidget(instr_box)

        # ── Action Buttons ──
        btn_row = QWidget()
        btn_row_l = QHBoxLayout(btn_row)
        btn_row_l.setContentsMargins(0, 0, 0, 0)
        btn_row_l.setSpacing(8)

        self._btn_reset = QPushButton("↺  Reset Arm")
        self._btn_reset.setCursor(Qt.PointingHandCursor)
        self._btn_reset.clicked.connect(self._on_reset)
        self._btn_reset.setStyleSheet(f"""
            QPushButton {{
                font-family: '{FONT}'; font-size: 12px; font-weight: 600;
                color: {CLR_TEXT_PRIM.name()};
                background: #FFFFFF;
                border: 1.5px solid {CLR_BORDER.name()};
                border-radius: 7px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{
                background: #F0F4FF;
                border-color: {CLR_SEG1.name()};
                color: {CLR_SEG1.name()};
            }}
            QPushButton:pressed {{ background: #E0EAFF; }}
        """)

        self._btn_calc = QPushButton("Show Calculation")
        self._btn_calc.setCursor(Qt.PointingHandCursor)
        self._btn_calc.clicked.connect(self._on_show_calculation)
        self._btn_calc.setStyleSheet(f"""
            QPushButton {{
                font-family: '{FONT}'; font-size: 12px; font-weight: 600;
                color: #FFFFFF;
                background: {CLR_SEG1.name()};
                border: 1.5px solid {CLR_SEG1.name()};
                border-radius: 7px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{ background: #0A5FD6; border-color: #0A5FD6; }}
            QPushButton:pressed {{ background: #0A50C0; }}
            QPushButton:disabled {{
                background: {CLR_BORDER.name()};
                border-color: {CLR_BORDER.name()};
                color: {CLR_TEXT_SEC.name()};
            }}
        """)

        btn_row_l.addWidget(self._btn_reset)
        btn_row_l.addWidget(self._btn_calc)
        sl.addWidget(btn_row)

        sl.addStretch()

        # ── Apply initial 2-DOF state ──
        self._r_t3.set_faded(True)
        self._r_t4.set_faded(True)
        self._sl_l3.set_enabled(False)
        self._sl_l4.set_enabled(False)

        # Seed values
        self._on_angles(
            math.degrees(self.canvas.theta1), math.degrees(self.canvas.theta2),
            math.degrees(self.canvas.theta3), math.degrees(self.canvas.theta4),
            0.0, 0.0)
        *_, gx, gy = self.canvas.forward_kinematics(
            self.canvas.theta1, self.canvas.theta2,
            self.canvas.theta3, self.canvas.theta4)
        cx, cy = self.canvas.arm_to_cartesian(gx, gy)
        self._on_position(cx, cy)

    # ── Reset handler ─────────────────────────
    def _on_reset(self):
        """Animate all joints back to 0°."""
        self.canvas.target_theta1 = 0.0
        self.canvas.target_theta2 = 0.0
        self.canvas.target_theta3 = 0.0
        self.canvas.target_theta4 = 0.0
        self.canvas.target_x = None
        self.canvas.target_y = None
        self.canvas.moving = True
        self._r_tx.set_value("—")
        self._r_ty.set_value("—")
        self._on_status("Resetting to zero…", "moving")

    # ── Show Calculation handler ───────────────
    def _on_show_calculation(self):
        if self.canvas.target_x is None:
            QMessageBox.information(
                self, "No Target",
                "Please click on the plane first to set a target position.")
            return
        text = self._build_calculation_text()
        dlg = CalculationDialog(text, self)
        dlg.exec_()

    def _build_calculation_text(self) -> str:
        c     = self.canvas
        mode  = ["2-DOF", "3-DOF", "4-DOF"][c.mode]
        px, py = c.target_x, c.target_y
        L1, L2 = c.L1, c.L2
        L3    = c._L3_eff()
        L4    = c._L4_eff()
        scale = c._scale()

        L1u, L2u, L3u, L4u = L1/scale, L2/scale, L3/scale, L4/scale
        pxu, pyu = px/scale, py/scale
        t1, t2, t3, t4 = (c.target_theta1, c.target_theta2,
                           c.target_theta3, c.target_theta4)

        lines = []
        SEP  = "═" * 62
        sep2 = "─" * 62

        lines.append(SEP)
        lines.append("  PLANAR INVERSE KINEMATICS — STEP-BY-STEP DERIVATION")
        lines.append(f"  Mode: {mode}  |  Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(SEP)
        lines.append("")

        # ── Section 1 ──
        lines.append("1. GIVEN / KNOWN QUANTITIES")
        lines.append(sep2)
        lines.append(f"   Link lengths:")
        lines.append(f"     L₁ = {L1u:.4f} u   (upper arm)")
        lines.append(f"     L₂ = {L2u:.4f} u   (forearm)")
        if c.mode >= 1:
            lines.append(f"     L₃ = {L3u:.4f} u   (wrist link)")
        if c.mode == 2:
            lines.append(f"     L₄ = {L4u:.4f} u   (finger link)")
        lines.append("")
        lines.append(f"   Target end-effector position:")
        lines.append(f"     Pₓ = {pxu:.4f} u")
        lines.append(f"     Pᵧ = {pyu:.4f} u")
        lines.append("")

        # ── Section 2 ──
        if c.mode == 0:
            r2  = px*px + py*py
            r   = math.sqrt(r2)
            r2u = r2/scale**2; ru = r/scale
            cn  = r2 - L1**2 - L2**2
            cd  = 2.0*L1*L2
            cv  = cn/cd
            cc  = max(-1.0, min(1.0, cv))
            alpha = math.atan2(py, px)
            beta  = math.atan2(L2*math.sin(t2), L1+L2*math.cos(t2))

            lines.append("2. GEOMETRIC APPROACH — 2-DOF PLANAR ARM")
            lines.append(sep2)
            lines.append("   Two revolute joints solved with the Law of Cosines.")
            lines.append("")
            lines.append("   Step 2.1 — Distance from base to target:")
            lines.append(f"     r² = Pₓ² + Pᵧ² = ({pxu:.4f})² + ({pyu:.4f})² = {r2u:.4f} u²")
            lines.append(f"     r  = √{r2u:.4f} = {ru:.4f} u")
            lines.append("")
            lines.append("   Step 2.2 — Reachability check:")
            lines.append(f"     |L₁-L₂| = {abs(L1u-L2u):.4f} ≤ r ≤ {L1u+L2u:.4f} = L₁+L₂  →  ✓ REACHABLE")
            lines.append("")
            lines.append("   Step 2.3 — Elbow angle θ₂ (Law of Cosines):")
            lines.append("       cos(θ₂) = (r² − L₁² − L₂²) / (2·L₁·L₂)")
            lines.append(f"              = ({r2u:.4f} − {L1u**2:.4f} − {L2u**2:.4f}) / (2·{L1u:.4f}·{L2u:.4f})")
            lines.append(f"              = {cn/scale**2:.4f} / {cd/scale**2:.4f} = {cv:.6f}")
            lines.append(f"     θ₂ = arccos({cc:.6f}) = {math.degrees(t2):+.4f}°")
            lines.append("")
            lines.append("   Step 2.4 — Shoulder angle θ₁:")
            lines.append("       α = atan2(Pᵧ, Pₓ);   β = atan2(L₂·sinθ₂, L₁+L₂·cosθ₂);   θ₁ = α − β")
            lines.append(f"     α = {math.degrees(alpha):+.4f}°")
            lines.append(f"     β = atan2({L2u*math.sin(t2):.4f}, {L1u+L2u*math.cos(t2):.4f}) = {math.degrees(beta):+.4f}°")
            lines.append(f"     θ₁ = {math.degrees(alpha):+.4f}° − ({math.degrees(beta):+.4f}°) = {math.degrees(t1):+.4f}°")
            lines.append("")

        elif c.mode == 1:
            phi = t1+t2+t3
            wx  = px - L3*math.cos(phi)
            wy  = py - L3*math.sin(phi)
            r2  = wx*wx+wy*wy; r = math.sqrt(r2)
            wxu = wx/scale; wyu = wy/scale
            r2u = r2/scale**2; ru = r/scale
            cn  = r2 - L1**2 - L2**2; cd = 2.0*L1*L2; cv = cn/cd
            alpha = math.atan2(wy, wx)
            beta  = math.atan2(L2*math.sin(t2), L1+L2*math.cos(t2))

            lines.append("2. φ-SWEEP APPROACH — 3-DOF PLANAR ARM")
            lines.append(sep2)
            lines.append("   Redundant arm: orientation φ = θ₁+θ₂+θ₃ is swept over [−π,π].")
            lines.append("   For each φ, the wrist centre W is computed and a 2-DOF sub-IK is solved.")
            lines.append("   The solution minimising joint displacement from the current pose is kept.")
            lines.append("")
            lines.append("   Step 2.1 — Best φ (via minimum-displacement sweep):")
            lines.append(f"     φ = θ₁+θ₂+θ₃ = {math.degrees(t1):+.4f}° + {math.degrees(t2):+.4f}° + {math.degrees(t3):+.4f}° = {math.degrees(phi):+.4f}°")
            lines.append("")
            lines.append("   Step 2.2 — Wrist centre W:")
            lines.append(f"     Wₓ = Pₓ − L₃·cos φ = {pxu:.4f} − {L3u:.4f}·cos({math.degrees(phi):.4f}°) = {wxu:.4f} u")
            lines.append(f"     Wᵧ = Pᵧ − L₃·sin φ = {pyu:.4f} − {L3u:.4f}·sin({math.degrees(phi):.4f}°) = {wyu:.4f} u")
            lines.append("")
            lines.append(f"   Step 2.3 — Distance to wrist: r = √({wxu:.4f}² + {wyu:.4f}²) = {ru:.4f} u")
            lines.append("")
            lines.append("   Step 2.4 — Elbow angle θ₂ (Law of Cosines on sub-arm):")
            lines.append(f"     cos(θ₂) = ({r2u:.4f} − {L1u**2:.4f} − {L2u**2:.4f}) / (2·{L1u:.4f}·{L2u:.4f}) = {cv:.6f}")
            lines.append(f"     θ₂ = arccos({max(-1.0,min(1.0,cv)):.6f}) = {math.degrees(t2):+.4f}°")
            lines.append("")
            lines.append("   Step 2.5 — Shoulder angle θ₁:")
            lines.append(f"     α = atan2({wyu:.4f},{wxu:.4f}) = {math.degrees(alpha):+.4f}°")
            lines.append(f"     β = atan2({L2u*math.sin(t2):.4f},{L1u+L2u*math.cos(t2):.4f}) = {math.degrees(beta):+.4f}°")
            lines.append(f"     θ₁ = α − β = {math.degrees(t1):+.4f}°")
            lines.append("")
            lines.append("   Step 2.6 — Wrist angle θ₃:")
            lines.append(f"     θ₃ = φ − θ₁ − θ₂ = {math.degrees(phi):+.4f}° − {math.degrees(t1):+.4f}° − {math.degrees(t2):+.4f}° = {math.degrees(t3):+.4f}°")
            lines.append("")

        else:  # 4-DOF
            psi = t1+t2+t3+t4
            phi = t1+t2+t3
            fx2  = px - L4*math.cos(psi)
            fy2  = py - L4*math.sin(psi)
            wx2  = fx2 - L3*math.cos(phi)
            wy2  = fy2 - L3*math.sin(phi)
            fx2u = fx2/scale; fy2u = fy2/scale
            wx2u = wx2/scale; wy2u = wy2/scale
            r2   = wx2*wx2+wy2*wy2; r = math.sqrt(r2)
            r2u  = r2/scale**2; ru = r/scale
            cn   = r2 - L1**2 - L2**2; cd = 2.0*L1*L2; cv = cn/cd
            alpha = math.atan2(wy2, wx2)
            beta  = math.atan2(L2*math.sin(t2), L1+L2*math.cos(t2))

            lines.append("2. DOUBLE φ-SWEEP APPROACH — 4-DOF PLANAR ARM")
            lines.append(sep2)
            lines.append("   Twice-redundant arm. Two orientation parameters are swept:")
            lines.append("     ψ = θ₁+θ₂+θ₃+θ₄  (total end-effector orientation)")
            lines.append("     φ = θ₁+θ₂+θ₃       (finger-joint sub-orientation)")
            lines.append("   For each (ψ, φ) pair the 2-DOF shoulder/elbow sub-IK is solved.")
            lines.append("   The configuration minimising total joint displacement is selected.")
            lines.append("")
            lines.append("   Step 2.1 — Best (ψ, φ) selected by joint-displacement minimisation:")
            lines.append(f"     ψ = {math.degrees(psi):+.4f}°   φ = {math.degrees(phi):+.4f}°")
            lines.append("")
            lines.append("   Step 2.2 — Finger joint position (back-project end-effector by L₄):")
            lines.append(f"     Fₓ = Pₓ − L₄·cos ψ = {pxu:.4f} − {L4u:.4f}·cos({math.degrees(psi):.4f}°) = {fx2u:.4f} u")
            lines.append(f"     Fᵧ = Pᵧ − L₄·sin ψ = {pyu:.4f} − {L4u:.4f}·sin({math.degrees(psi):.4f}°) = {fy2u:.4f} u")
            lines.append("")
            lines.append("   Step 2.3 — Wrist centre (back-project finger joint by L₃):")
            lines.append(f"     Wₓ = Fₓ − L₃·cos φ = {fx2u:.4f} − {L3u:.4f}·cos({math.degrees(phi):.4f}°) = {wx2u:.4f} u")
            lines.append(f"     Wᵧ = Fᵧ − L₃·sin φ = {fy2u:.4f} − {L3u:.4f}·sin({math.degrees(phi):.4f}°) = {wy2u:.4f} u")
            lines.append("")
            lines.append(f"   Step 2.4 — Distance to wrist: r = √({wx2u:.4f}² + {wy2u:.4f}²) = {ru:.4f} u")
            lines.append("")
            lines.append("   Step 2.5 — Elbow angle θ₂ (Law of Cosines):")
            lines.append(f"     cos(θ₂) = ({r2u:.4f} − {L1u**2:.4f} − {L2u**2:.4f}) / (2·{L1u:.4f}·{L2u:.4f}) = {cv:.6f}")
            lines.append(f"     θ₂ = arccos({max(-1.0,min(1.0,cv)):.6f}) = {math.degrees(t2):+.4f}°")
            lines.append("")
            lines.append("   Step 2.6 — Shoulder angle θ₁:")
            lines.append(f"     α = atan2({wy2u:.4f},{wx2u:.4f}) = {math.degrees(alpha):+.4f}°")
            lines.append(f"     β = atan2({L2u*math.sin(t2):.4f},{L1u+L2u*math.cos(t2):.4f}) = {math.degrees(beta):+.4f}°")
            lines.append(f"     θ₁ = α − β = {math.degrees(t1):+.4f}°")
            lines.append("")
            lines.append("   Step 2.7 — Wrist angle θ₃:")
            lines.append(f"     θ₃ = φ − θ₁ − θ₂ = {math.degrees(phi):+.4f}° − {math.degrees(t1):+.4f}° − {math.degrees(t2):+.4f}° = {math.degrees(t3):+.4f}°")
            lines.append("")
            lines.append("   Step 2.8 — Finger angle θ₄:")
            lines.append(f"     θ₄ = ψ − θ₁ − θ₂ − θ₃ = {math.degrees(psi):+.4f}° − {math.degrees(t1):+.4f}° − {math.degrees(t2):+.4f}° − {math.degrees(t3):+.4f}° = {math.degrees(t4):+.4f}°")
            lines.append("")

        # ── Section 3: FK Verification ──
        lines.append("3. VERIFICATION — FORWARD KINEMATICS CHECK")
        lines.append(sep2)
        a12   = t1+t2; a123 = t1+t2+t3; a1234 = t1+t2+t3+t4
        ex_v  = L1*math.cos(t1);  ey_v = L1*math.sin(t1)
        wx_v  = ex_v+L2*math.cos(a12); wy_v = ey_v+L2*math.sin(a12)
        fx_v  = wx_v+L3*math.cos(a123); fy_v = wy_v+L3*math.sin(a123)
        gx_v  = fx_v+L4*math.cos(a1234); gy_v = fy_v+L4*math.sin(a1234)
        # end-effector is g in 4dof, f in 3dof, w in 2dof
        if c.mode == 2:
            ex_end, ey_end = gx_v, gy_v
        elif c.mode == 1:
            ex_end, ey_end = fx_v, fy_v
        else:
            ex_end, ey_end = wx_v, wy_v

        lines.append(f"   Eₓ = L₁·cos θ₁ = {L1u:.4f}·cos({math.degrees(t1):.4f}°) = {ex_v/scale:.4f} u")
        lines.append(f"   Eᵧ = L₁·sin θ₁ = {L1u:.4f}·sin({math.degrees(t1):.4f}°) = {ey_v/scale:.4f} u")
        lines.append(f"   Wₓ = Eₓ+L₂·cos(θ₁+θ₂) = {ex_v/scale:.4f}+{L2u:.4f}·cos({math.degrees(a12):.4f}°) = {wx_v/scale:.4f} u")
        lines.append(f"   Wᵧ = Eᵧ+L₂·sin(θ₁+θ₂) = {ey_v/scale:.4f}+{L2u:.4f}·sin({math.degrees(a12):.4f}°) = {wy_v/scale:.4f} u")
        if c.mode >= 1:
            lines.append(f"   Fₓ = Wₓ+L₃·cos(θ₁+θ₂+θ₃) = {wx_v/scale:.4f}+{L3u:.4f}·cos({math.degrees(a123):.4f}°) = {fx_v/scale:.4f} u")
            lines.append(f"   Fᵧ = Wᵧ+L₃·sin(θ₁+θ₂+θ₃) = {wy_v/scale:.4f}+{L3u:.4f}·sin({math.degrees(a123):.4f}°) = {fy_v/scale:.4f} u")
        if c.mode == 2:
            lines.append(f"   Gₓ = Fₓ+L₄·cos(θ₁+θ₂+θ₃+θ₄) = {fx_v/scale:.4f}+{L4u:.4f}·cos({math.degrees(a1234):.4f}°) = {gx_v/scale:.4f} u")
            lines.append(f"   Gᵧ = Fᵧ+L₄·sin(θ₁+θ₂+θ₃+θ₄) = {fy_v/scale:.4f}+{L4u:.4f}·sin({math.degrees(a1234):.4f}°) = {gy_v/scale:.4f} u")
        err = math.hypot(ex_end - px, ey_end - py) / scale
        lines.append("")
        lines.append(f"   Target:         ({pxu:.4f}, {pyu:.4f}) u")
        lines.append(f"   FK result:      ({ex_end/scale:.4f}, {ey_end/scale:.4f}) u")
        lines.append(f"   Residual error: {err:.6f} u  {'✓ SOLVED' if err < 0.02 else '⚠ CHECK'}")
        lines.append("")

        # ── Section 4: Summary ──
        lines.append("4. RESULT SUMMARY")
        lines.append(sep2)
        lines.append(f"   θ₁ (Shoulder) = {math.degrees(t1):+.4f}°  =  {t1:+.6f} rad")
        lines.append(f"   θ₂ (Elbow)    = {math.degrees(t2):+.4f}°  =  {t2:+.6f} rad")
        if c.mode >= 1:
            lines.append(f"   θ₃ (Wrist)    = {math.degrees(t3):+.4f}°  =  {t3:+.6f} rad")
        if c.mode == 2:
            lines.append(f"   θ₄ (Finger)   = {math.degrees(t4):+.4f}°  =  {t4:+.6f} rad")
        lines.append("")
        methods = ["Closed-form geometric", "φ-sweep (360 orientations)", "Double φψ-sweep (180×180)"]
        lines.append(f"   Method: {methods[c.mode]}")
        lines.append("")
        lines.append(SEP)
        lines.append("  Robot Arm Simulator  —  Planar Inverse Kinematics")
        lines.append(SEP)

        return "\n".join(lines)

    # ── Toggle handler ────────────────────────
    def _on_toggle(self, mode: int):
        self.canvas.switch_mode(mode)
        self._update_dof_ui(mode, morphing=True)
        self._on_status("Morphing…", "moving")

    def _on_morph_done(self, mode: int):
        self._update_dof_ui(mode, morphing=False)
        self._on_status("Ready — click on the plane", "ok")

    def _update_dof_ui(self, mode: int, morphing: bool = False):
        labels = ["2-DOF", "3-DOF", "4-DOF"]
        descs  = [
            "Two revolute joints.\nExact solution, no redundancy.",
            "Three revolute joints.\nKinematically redundant — φ-sweep IK.",
            "Four revolute joints.\nTwice redundant — double φψ-sweep IK.",
        ]
        self._dof_desc.setText(descs[mode])

        # Update max reach
        s  = self.canvas._scale()
        L3 = self.canvas.L3 if mode >= 1 else 0.0
        L4 = self.canvas.L4 if mode == 2 else 0.0
        self._r_ws.set_value(
            f"{(self.canvas.L1 + self.canvas.L2 + L3 + L4) / s:.0f} u")

        # Fade joint rows
        self._r_t3.set_faded(mode < 1)
        self._r_t4.set_faded(mode < 2)

        # Enable / disable link sliders
        self._sl_l3.set_enabled(mode >= 1)
        self._sl_l4.set_enabled(mode == 2)

    # ── Callbacks ─────────────────────────────
    def _on_status(self, msg: str, kind: str):
        colours = {"ok": CLR_OK, "moving": CLR_MOV,
                   "warn": CLR_WARN, "error": CLR_ERR}
        c = colours.get(kind, CLR_OK)
        self._status_lbl.setStyleSheet(
            f"font-family: '{FONT}'; font-size: 12px; "
            f"font-weight: 500; color: {c.name()};")
        self._status_lbl.setText(msg)

    def _on_angles(self, t1, t2, t3, t4, morph_t, morph_t2):
        self._r_t1.set_value(f"{t1:+.1f}°")
        self._r_t2.set_value(f"{t2:+.1f}°")
        self._r_t3.set_value(f"{t3:+.1f}°")
        self._r_t4.set_value(f"{t4:+.1f}°")
        *_, gx, gy = self.canvas.forward_kinematics(
            math.radians(t1), math.radians(t2),
            math.radians(t3), math.radians(t4))
        dist = math.hypot(gx, gy) / self.canvas._scale()
        self._r_reach.set_value(f"{dist:.2f} u")

    def _on_position(self, x: float, y: float):
        self._r_ex.set_value(f"{x:.2f}")
        self._r_ey.set_value(f"{y:.2f}")

    def _on_target(self, x: float, y: float):
        self._r_tx.set_value(f"{x:.2f}")
        self._r_ty.set_value(f"{y:.2f}")

    def _on_speed_change(self, val: int):
        self.canvas.speed = val / 100.0
        self._speed_val.setText(f"{val} %")

    # ── Link length callbacks ──────────────────
    def _on_l1_change(self, px: float):
        self.canvas.L1 = px
        self._refresh_after_link_change()

    def _on_l2_change(self, px: float):
        self.canvas.L2 = px
        self._refresh_after_link_change()

    def _on_l3_change(self, px: float):
        self.canvas.L3 = px
        self._refresh_after_link_change()

    def _on_l4_change(self, px: float):
        self.canvas.L4 = px
        self._refresh_after_link_change()

    def _refresh_after_link_change(self):
        self.canvas.target_x = None
        self.canvas.target_y = None
        self.canvas.moving   = False
        self._r_tx.set_value("—")
        self._r_ty.set_value("—")
        m  = self.canvas.mode
        s  = self.canvas._scale()
        L3 = self.canvas.L3 if m >= 1 else 0.0
        L4 = self.canvas.L4 if m == 2 else 0.0
        self._r_ws.set_value(
            f"{(self.canvas.L1 + self.canvas.L2 + L3 + L4) / s:.0f} u")
        self.canvas.update()

    # ── Timer ─────────────────────────────────
    def _tick(self):
        self.canvas.step()
        self.canvas.update()

    # ── Styles ────────────────────────────────
    def _apply_global_style(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background: {CLR_BG.name()};
                font-family: '{FONT}';
            }}
            QLabel {{ background: transparent; }}
        """)

    @staticmethod
    def _slider_style() -> str:
        return f"""
            QSlider::groove:horizontal {{
                height: 4px; background: {CLR_BORDER.name()}; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                width: 14px; height: 14px; margin: -5px 0;
                background: {CLR_SEG1.name()};
                border-radius: 7px; border: 2px solid white;
            }}
            QSlider::sub-page:horizontal {{
                background: {CLR_SEG1.name()}; border-radius: 2px;
            }}
        """


# ══════════════════════════════════════════════
#  Calculation floating window
# ══════════════════════════════════════════════
class CalculationDialog(QDialog):
    """Floating window showing step-by-step IK calculation."""

    def __init__(self, text: str, parent=None):
        super().__init__(parent, Qt.Window)
        self._text = text
        self.setWindowTitle("Download Calculation")
        self.setMinimumSize(700, 560)
        self.resize(760, 640)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ──
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background: {CLR_SEG1.name()};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 16, 0)
        hl.setSpacing(10)

        title_lbl = QLabel("Inverse Kinematics Calculation — Step by Step")
        title_lbl.setStyleSheet(
            f"font-family: 'Segoe UI'; font-size: 14px; font-weight: 700;"
            f" color: #FFFFFF; background: transparent;")
        hl.addWidget(title_lbl)
        hl.addStretch()
        root.addWidget(header)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: #FAFBFC; }"
            "QScrollBar:vertical { width: 10px; background: #F0F2F5; }"
            "QScrollBar::handle:vertical { background: #C8CACE; border-radius: 5px; min-height: 30px; }"
        )
        self._text_lbl = QLabel(self._text)
        self._text_lbl.setTextFormat(Qt.PlainText)
        self._text_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._text_lbl.setWordWrap(False)
        self._text_lbl.setMargin(24)
        self._text_lbl.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace;"
            " font-size: 12px; color: #1C2333; background: transparent;"
            " line-height: 1.6;"
        )
        scroll.setWidget(self._text_lbl)
        root.addWidget(scroll, stretch=1)

        # ── Bottom bar ──
        bar = QWidget()
        bar.setFixedHeight(58)
        bar.setStyleSheet(
            f"background: {CLR_PANEL.name()};"
            f" border-top: 1px solid {CLR_BORDER.name()};"
        )
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(16, 0, 16, 0)
        bl.setSpacing(10)

        note = QLabel("Textbook-style derivation — angles in degrees (°) and radians (rad).")
        note.setStyleSheet(
            f"font-size: 10px; color: {CLR_TEXT_SEC.name()}; background: transparent;")
        bl.addWidget(note)
        bl.addStretch()

        btn_copy = QPushButton("Copy to clipboard")
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.clicked.connect(self._copy)
        btn_copy.setStyleSheet(self._btn_style(accent=False))

        btn_dl = QPushButton("Download text file")
        btn_dl.setCursor(Qt.PointingHandCursor)
        btn_dl.clicked.connect(self._download)
        btn_dl.setStyleSheet(self._btn_style(accent=True))

        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(self._btn_style(accent=False))

        bl.addWidget(btn_copy)
        bl.addWidget(btn_dl)
        bl.addWidget(btn_close)
        root.addWidget(bar)

    def _btn_style(self, accent: bool) -> str:
        if accent:
            return (
                f"QPushButton {{ font-family: 'Segoe UI'; font-size: 12px; font-weight: 600;"
                f" color: #FFFFFF; background: {CLR_SEG1.name()};"
                f" border: none; border-radius: 7px; padding: 7px 18px; }}"
                f" QPushButton:hover {{ background: #0A5FD6; }}"
                f" QPushButton:pressed {{ background: #0A50C0; }}"
            )
        else:
            return (
                f"QPushButton {{ font-family: 'Segoe UI'; font-size: 12px; font-weight: 600;"
                f" color: {CLR_TEXT_PRIM.name()}; background: #FFFFFF;"
                f" border: 1.5px solid {CLR_BORDER.name()}; border-radius: 7px; padding: 7px 18px; }}"
                f" QPushButton:hover {{ background: #F0F4FF; border-color: {CLR_SEG1.name()}; color: {CLR_SEG1.name()}; }}"
                f" QPushButton:pressed {{ background: #E0EAFF; }}"
            )

    def _copy(self):
        QApplication.clipboard().setText(self._text)
        QMessageBox.information(self, "Copied", "Calculation copied to clipboard.")

    def _download(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"IK_Calculation_{ts}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Calculation", default_name,
            "Text Files (*.txt);;All Files (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._text)
            QMessageBox.information(self, "Saved", f"Saved to:\n{path}")


# ══════════════════════════════════════════════
#  Entry point
# ══════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window,     QColor(CLR_BG))
    palette.setColor(QPalette.WindowText, QColor(CLR_TEXT_PRIM))
    app.setPalette(palette)
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
