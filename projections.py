import pygame
from pygame.locals import *

from typing import Tuple, Optional, List, TypeVar
from math import sqrt, fsum


T = TypeVar('T')
Vector2 = Tuple[T, T]
Vector2f = Vector2[float]
Vector3 = Tuple[T, T, T]
Vector3f = Vector3[float]
LineSegment3 = Tuple[Vector3[T], Vector3[T]]
LineSegment2 = Tuple[Vector2[T], Vector2[T]]
LineSegment3f = LineSegment3[float]
LineSegment2f = LineSegment2[float]


def mult_vec(v: Vector3f, m: float) -> Vector3f:
    return (v[0] * m, v[1] * m, v[2] * m)


def sum_vec(l: List[Vector3f]) -> Vector3f:
    return tuple(map(fsum, zip(*l))) # type: ignore


def decompose(v: Vector3f, basis: Tuple[Vector3f, Vector3f]) -> Vector2f:
    a = basis[0]
    b = basis[1]

    try:
        n = (v[0] * a[1] - v[1] * a[0])/(b[0] * a[1] - b[1] * a[0])
        m = (v[0] - n * b[0])/(a[0])

        return(n, m)

    except ZeroDivisionError:
        return (0, 0)


def normalize_vec(v: Vector3f) -> Vector3f:
    M = sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)
    return (v[0]/M, v[1]/M, v[2]/M)


class Line:
    def __init__(self, point: Vector3f, dir_vec: Vector3f) -> None:
        self.point = point
        self.dir_vec = normalize_vec(dir_vec)

    def __str__(self) -> str:
        return "{0!s} + t{1!s}".format(self.point, self.dir_vec)

    def scuttle(self, u: float) -> Vector3f:
        return (self.point[0] + u * self.dir_vec[0], self.point[1] + u * self.dir_vec[1], self.point[2] + u * self.dir_vec[2])


class Plane:
    def __init__(self, normal: Vector3f, intercept: float) -> None:
        self.normal = normal
        self.intercept = intercept


    def project_vector(self, point: Vector3f, view: Vector3f) -> Vector3f:
        A = self.normal[0]
        B = self.normal[1]
        C = self.normal[2]
        D = self.intercept

        x = point[0]
        y = point[1]
        z = point[2]

        mx = x - view[0]
        my = y - view[1]
        mz = z - view[2]

        t = -(A * x + B * y + C * z + D)/(A * mx + B * my + C * mz)

        return (x + t * mx, y + t * my, z + t * mz)


    def project_through(self, point: Vector3f) -> Vector3f:
        return self.project_vector(point, sum_vec([point, self.normal]))


    def project_line(self, line: Line) -> Line:
        p1 = self.project_through(line.point)
        p2 = self.project_through(line.scuttle(1))

        m = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])

        return Line(p1, m)


    def get_vectors(self, basis: Vector3f) -> Tuple[Vector3f, Vector3f]:
        A = self.normal[0]
        B = self.normal[1]
        C = self.normal[2]

        q = normalize_vec(self.project_through(basis))

        x = B * q[2] - C * q[1]
        y = C * q[0] - A * q[2]
        z = A * q[1] - B * q[0]

        r = normalize_vec((x, y, z))

        return (q, r)


class KeyboardEventHandler:
    def __init__(self):
        self.key_event_map = {}


    def has_handler(self, key) -> bool:
        return key in self.key_event_map


    def get_handler(self, key):
        handler, kwargs_dict = self.key_event_map[key]
        return (lambda *args, **kwargs: handler(*args, key, **kwargs, **kwargs_dict))


    def add_handler(self, key, handler, kwargs_dict = {}):
        self.key_event_map[key] = (handler, kwargs_dict)


    def add_group_handler(self, group, handler, kwargs_dict = {}):
        for key in group:
            self.add_handler(key, handler, kwargs_dict)


class View:
    def __init__(self, point: Vector3f, plane: Plane, basis: Vector3f = (1, 1, 1)) -> None:
        self.point = point
        self.plane = plane
        self.basis = plane.get_vectors(basis)


    def project_point(self, point: Vector3f) -> Vector2[int]:
        return tuple(map(round, decompose(self.plane.project_vector(point, self.point), self.basis))) # type: ignore


    def project_points(self, points: List[Vector3f]) -> List[Vector2[int]]:
        return list(map(self.project_point, points))


    def move_point(self, v: Vector3f) -> None:
        self.point = sum_vec([self.point, v])


class PrimitiveRenderer():
    def __init__(self, screen) -> None:
        self.screen = screen

    
    def draw_point(self, point: Vector2[int], color: Tuple[int, int, int] = (0, 0, 0), radius: int = 3) -> None:
        pygame.draw.circle(self.screen, color, point, radius)


    def draw_line_segment(self, segment: LineSegment2[int], color: Tuple[int, int, int] = (0, 0, 0), radius: int = 3) -> None:
        draw_point(segment[0], color, radius)
        draw_point(segment[1], color, radius)
        pygame.draw.line(self.screen, color, segment[0], segment[1], radius)


    def draw_polygon(self, polygon: List[LineSegment2[int]], color: Tuple[int, int, int] = (0, 0, 0), radius: int = 3) -> None:
        if not points:
            return

        first = points[0]
        for i in range(0, len(points)):
            if i + 1 < len(points):
                self.draw_line_segment((points[i], point[i + 1]), color, radius)
            else:
                self.draw_line_segment((points[i], first), color, radius)


def adjust_view_point(key, view) -> None:
    if key == pygame.K_LEFT:
        view.move_point((-10, 0, 0))
    elif key == pygame.K_RIGHT:
        view.move_point((10, 0, 0))
    elif key == pygame.K_UP:
        view.move_point((0, 10, 0))
    elif key == pygame.K_DOWN:
        view.move_point((0, -10, 0))
    elif key == pygame.K_q:
        view.move_point((0, 0, 10))
    elif key == pygame.K_e:
        view.move_point((0, 0, -10))


def main() -> None:
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((0, 0), pygame.DOUBLEBUF)

    color = { "white": (255, 255, 255), "black": (0, 0, 0) }

    font = pygame.font.SysFont("arial", 38)

    view = View((0.0, 0.0, 0.0), Plane((2, 2, 1), 0))

    p1 = (100.0, 50.0, 1.0)
    p2 = (100.0, 200.0, 1.0)
    p3 = (250.0, 200.0, 1.0)
    p4 = (250.0, 50.0, 1.0)

    view_control_keys = [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_q, pygame.K_e]

    keyboard_event_handler = KeyboardEventHandler()
    keyboard_event_handler.add_group_handler(view_control_keys, adjust_view_point, {"view": view})


    def draw_line_segment(line_segment: LineSegment2) -> None:
        p1, p2 = line_segment
        pygame.draw.line(screen, color["black"], p1, p2, 3)
        pygame.draw.circle(screen, color["black"], p1, 5)
        pygame.draw.circle(screen, color["black"], p2, 5)


    def draw_polygon(points: List[Vector2[int]]) -> None:
        if not points:
            return

        first = points[0] # type: Tuple[int, int]
        for i in range(0, len(points)):
            if i + 1 < len(points):
                draw_line_segment((points[i], points[i + 1]))
            else:
                draw_line_segment((points[i], first))


    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                exit()
            elif e.type == pygame.KEYDOWN:
                if keyboard_event_handler.has_handler(e.key):
                    keyboard_event_handler.get_handler(e.key)()


            shape = view.project_points([p1, p2, p3, p4])

            screen.fill(color["white"])

            draw_polygon(shape)

            pygame.display.flip()


if __name__ == "__main__":
    main()

