"""A tiny software 3D engine: quad meshes, perspective camera, flat shading.

It exists so explainer scenes can show *real* 3D objects (rotating, cut away,
animated) without any GPU/OpenGL/browser dependency: numpy does the geometry
and Pillow rasterises the shaded polygons at 2x supersampling.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=np.float64)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float64)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=np.float64)


def _align_z(axis: str) -> np.ndarray:
    """Rotation taking local +Z onto the requested world axis."""
    if axis == "z":
        return np.eye(3)
    if axis == "y":
        return rot_x(-math.pi / 2)  # z -> y
    if axis == "x":
        return rot_y(math.pi / 2)  # z -> x
    raise ValueError(axis)


@dataclass
class Mesh:
    v: np.ndarray                      # (N, 3)
    f: np.ndarray                      # (M, 4) int, triangles repeat last index
    c: np.ndarray                      # (M, 3) float 0..255
    alpha: float = 1.0
    double: bool = True
    prio: float = 0.0                  # depth bias: larger = drawn later (in front)
    emissive: float = 0.0              # 0 = lit, 1 = unlit/self-illuminated
    outline: bool = True

    def copy(self) -> "Mesh":
        return Mesh(self.v.copy(), self.f.copy(), self.c.copy(), self.alpha,
                    self.double, self.prio, self.emissive, self.outline)

    def tf(self, R=None, t=(0, 0, 0), s=1.0) -> "Mesh":
        v = self.v * s
        if R is not None:
            v = v @ np.asarray(R).T
        v = v + np.asarray(t, dtype=np.float64)
        return Mesh(v, self.f, self.c, self.alpha, self.double, self.prio, self.emissive, self.outline)

    def colored(self, color, **kw) -> "Mesh":
        m = self.copy()
        m.c = np.tile(np.asarray(color, dtype=np.float64), (len(m.f), 1))
        for k, val in kw.items():
            setattr(m, k, val)
        return m


def merge(meshes: list[Mesh]) -> Mesh:
    vs, fs, cs, off = [], [], [], 0
    for m in meshes:
        vs.append(m.v)
        fs.append(m.f + off)
        cs.append(m.c)
        off += len(m.v)
    base = meshes[0]
    return Mesh(np.vstack(vs), np.vstack(fs), np.vstack(cs), base.alpha, base.double,
                base.prio, base.emissive, base.outline)


def _quad_faces(rings: list[np.ndarray], closed: bool) -> list[list[int]]:
    faces = []
    n = len(rings[0])
    for a in range(len(rings) - 1):
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            faces.append([a * n + i, a * n + j, (a + 1) * n + j, (a + 1) * n + i])
    return faces


def revolve(profile, seg: int = 36, arc=(0.0, 2 * math.pi), axis: str = "y",
            color=(150, 170, 205), cap_cut: bool = True, shade_jitter: float = 0.0) -> Mesh:
    """Surface of revolution around local Z from ``profile`` = [(radius, z), ...].

    A cylinder, cone, disc, hollow shell, nozzle... are all just profiles.
    ``arc`` limits the sweep (cutaway). Cut faces are added for partial arcs.
    """
    a0, a1 = arc
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    steps = seg if full else max(2, int(seg * (a1 - a0) / (2 * math.pi)))
    angles = np.linspace(a0, a1, steps, endpoint=not full)
    pts, ring_idx = [], []
    for (r, z) in profile:
        ring = np.stack([r * np.cos(angles), r * np.sin(angles), np.full_like(angles, z)], axis=1)
        pts.append(ring)
    verts = np.vstack(pts)
    faces = _quad_faces(pts, closed=full)
    n = len(angles)
    if not full and cap_cut and len(profile) >= 3:
        # Planar cut faces: fan over the profile polygon at both arc ends.
        for end in (0, n - 1):
            base = [k * n + end for k in range(len(profile))]
            for k in range(1, len(base) - 1):
                faces.append([base[0], base[k], base[k + 1], base[k + 1]])
    f = np.array(faces, dtype=np.int64)
    c = np.tile(np.asarray(color, dtype=np.float64), (len(f), 1))
    if shade_jitter:
        c = c * (1 + shade_jitter * (np.arange(len(f)) % 2 - 0.5))[:, None]
    m = Mesh(verts, f, c)
    R = _align_z(axis)
    return m.tf(R) if axis != "z" else m


def cylinder(r, length, seg=36, axis="y", color=(150, 170, 205), z0=0.0, caps=True, arc=(0, 2 * math.pi)):
    prof = [(0, z0), (r, z0), (r, z0 + length), (0, z0 + length)] if caps else [(r, z0), (r, z0 + length)]
    return revolve(prof, seg=seg, arc=arc, axis=axis, color=color)


def shell(r_out, r_in, length, seg=48, axis="y", color=(150, 170, 205), z0=0.0, arc=(0, 2 * math.pi)):
    prof = [(r_out, z0), (r_out, z0 + length), (r_in, z0 + length), (r_in, z0), (r_out, z0)]
    return revolve(prof, seg=seg, arc=arc, axis=axis, color=color)


def cone(r0, r1, length, seg=36, axis="y", color=(150, 170, 205), z0=0.0, caps=True):
    prof = [(0, z0), (r0, z0), (r1, z0 + length), (0, z0 + length)] if caps else [(r0, z0), (r1, z0 + length)]
    return revolve(prof, seg=seg, axis=axis, color=color)


def sphere(r, seg=20, color=(150, 170, 205), hemi: bool = False):
    n = max(6, seg // 2)
    lim = math.pi / 2 if hemi else math.pi
    prof = [(r * math.sin(a), r * -math.cos(a)) for a in np.linspace(0, lim, n)]
    return revolve(prof, seg=seg, axis="z", color=color)


def box(sx, sy, sz, color=(150, 170, 205), center=True) -> Mesh:
    x, y, z = sx / 2, sy / 2, sz / 2
    v = np.array([[-x, -y, -z], [x, -y, -z], [x, y, -z], [-x, y, -z],
                  [-x, -y, z], [x, -y, z], [x, y, z], [-x, y, z]], dtype=np.float64)
    if not center:
        v = v + np.array([x, y, z])
    f = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4], [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4]])
    c = np.tile(np.asarray(color, dtype=np.float64), (6, 1))
    return Mesh(v, f, c)


def slab_between(p0, p1, w, d, color=(150, 170, 205)) -> Mesh:
    """Rectangular bar from p0 to p1 with cross-section w x d (connecting rods...)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    ax = p1 - p0
    L = np.linalg.norm(ax)
    if L < 1e-9:
        return box(w, w, d, color)
    m = box(w, L, d, color)
    yaxis = ax / L
    ref = np.array([0.0, 0.0, 1.0]) if abs(yaxis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    xaxis = np.cross(yaxis, ref)
    xaxis /= np.linalg.norm(xaxis)
    zaxis = np.cross(xaxis, yaxis)
    R = np.stack([xaxis, yaxis, zaxis], axis=1)
    return m.tf(R, (p0 + p1) / 2)


def blade(span, chord, thick, twist=0.7, color=(190, 205, 230), slices=4) -> Mesh:
    """Twisted airfoil-ish blade extending along +X from origin (local)."""
    rings = []
    for k in range(slices + 1):
        u = k / slices
        a = twist * (u - 0.5)
        ch = chord * (1.0 - 0.35 * u)
        pts = []
        for (cx, cz) in [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]:
            y, z = cx * ch, cz * thick
            yr = y * math.cos(a) - z * math.sin(a)
            zr = y * math.sin(a) + z * math.cos(a)
            pts.append([u * span, yr, zr])
        rings.append(np.array(pts))
    verts = np.vstack(rings)
    faces = _quad_faces(rings, closed=True)
    faces.append([0, 1, 2, 3])
    last = slices * 4
    faces.append([last, last + 1, last + 2, last + 3])
    f = np.array(faces)
    return Mesh(verts, f, np.tile(np.asarray(color, float), (len(f), 1)))


def gear(r_in, r_out, teeth, thick, color=(170, 185, 215), axis="z") -> Mesh:
    n = teeth * 4
    ang = np.linspace(0, 2 * math.pi, n, endpoint=False)
    radii = []
    for i in range(n):
        phase = i % 4
        radii.append(r_out if phase in (1, 2) else r_in * 1.06)
    outer = np.array([[radii[i] * math.cos(ang[i]), radii[i] * math.sin(ang[i])] for i in range(n)])
    z0, z1 = -thick / 2, thick / 2
    verts = [(0, 0, z0), (0, 0, z1)]
    for p in outer:
        verts.append((p[0], p[1], z0))
    for p in outer:
        verts.append((p[0], p[1], z1))
    verts = np.array(verts, dtype=np.float64)
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([2 + i, 2 + j, 2 + n + j, 2 + n + i])
        faces.append([0, 2 + i, 2 + j, 2 + j])
        faces.append([1, 2 + n + i, 2 + n + j, 2 + n + j])
    f = np.array(faces)
    m = Mesh(verts, f, np.tile(np.asarray(color, float), (len(f), 1)))
    return m.tf(_align_z(axis)) if axis != "z" else m


@dataclass
class Camera:
    yaw: float = 0.4
    pitch: float = 0.25
    dist: float = 12.0
    fov_px: float = 1500.0
    target: tuple = (0.0, 0.0, 0.0)
    center_px: tuple = (540.0, 500.0)
    roll: float = 0.0

    def view(self):
        return rot_x(self.pitch) @ rot_y(self.yaw)

    def project(self, pts) -> np.ndarray:
        """World points (N,3) -> screen (N,3) [x, y, depth]."""
        P = np.atleast_2d(np.asarray(pts, dtype=np.float64)) - np.asarray(self.target)
        Vv = P @ self.view().T
        z = self.dist - Vv[:, 2]            # +z toward camera in view space
        s = self.fov_px / np.maximum(z, 0.1)
        x = self.center_px[0] + Vv[:, 0] * s
        y = self.center_px[1] - Vv[:, 1] * s
        return np.stack([x, y, z], axis=1)


LIGHT = np.array([-0.45, 0.75, 0.55])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def render(meshes: list[Mesh], cam: Camera, size: tuple[int, int], ss: int = 2,
           outline_dark: float = 0.8) -> Image.Image:
    """Painter's-algorithm render of ``meshes`` to an RGBA image of ``size``."""
    w, h = size
    img = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img, "RGBA")
    Rv = cam.view()
    items = []
    for mi, m in enumerate(meshes):
        if m.f.size == 0:
            continue
        P = m.v - np.asarray(cam.target)
        Vv = P @ Rv.T
        z = cam.dist - Vv[:, 2]
        sc = cam.fov_px / np.maximum(z, 0.1)
        sx = (cam.center_px[0] + Vv[:, 0] * sc) * ss
        sy = (cam.center_px[1] - Vv[:, 1] * sc) * ss
        F = m.f
        a, b, c_, d = (Vv[F[:, 0]], Vv[F[:, 1]], Vv[F[:, 2]], Vv[F[:, 3]])
        n = np.cross(c_ - a, d - b)
        ln = np.linalg.norm(n, axis=1)
        ln[ln < 1e-12] = 1e-12
        n = n / ln[:, None]
        centroid = (a + b + c_ + d) / 4
        facing = np.sum(n * (np.array([0, 0, cam.dist]) - centroid), axis=1)
        if not m.double:
            keep = facing > 0
        else:
            keep = np.ones(len(F), dtype=bool)
        flip = facing < 0
        n = np.where(flip[:, None], -n, n)
        # light is defined in view space so highlights stay stable while orbiting
        diff = np.clip(n @ LIGHT, 0, 1)
        rim = np.clip(1 - np.abs(n[:, 2]), 0, 1) ** 2 * 0.18
        lit = 0.36 + 0.78 * diff + rim
        lit = lit * (1 - m.emissive) + m.emissive * 1.15
        depth = z[F].mean(axis=1) - m.prio
        cols = np.clip(m.c * lit[:, None], 0, 255)
        for i in np.nonzero(keep)[0]:
            items.append((depth[i], mi, i, F[i], cols[i], m, sx, sy))
    items.sort(key=lambda it: -it[0])
    for depth, mi, i, face, col, m, sx, sy in items:
        poly = [(sx[k], sy[k]) for k in face]
        fill = (int(col[0]), int(col[1]), int(col[2]), int(255 * m.alpha))
        if m.outline and m.alpha >= 0.99:
            oc = (int(col[0] * outline_dark), int(col[1] * outline_dark), int(col[2] * outline_dark), 255)
            draw.polygon(poly, fill=fill, outline=oc)
        else:
            draw.polygon(poly, fill=fill)
    if ss != 1:
        img = img.resize((w, h), Image.LANCZOS)
    return img
