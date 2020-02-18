# code maintainability
from __future__ import annotations
from typing import Callable, List, Tuple, Set
from dataclasses import dataclass, field

# tree generation
from random import choice
from math import pi, sin, cos
from util import *

# tree export
from datetime import datetime


@dataclass
class Point:
    """A class for working with points."""

    x: float
    y: float

    def move(self, d: float, alpha: float) -> Point:
        """Return a coordinate moved by a given distance d at an angle alpha."""
        return Point(self.x + d * cos(alpha), self.y + d * sin(alpha))

    def __add__(self, other) -> Point:
        """Defines the addition of points as addition of their components."""
        return Point(self.x + other.x, self.y + other.y)

    def __str__(self) -> str:
        """Defines the string representation of a point as [x; y]."""
        return f"[{self.x}; {self.y}]"

    __repr__ = __str__

    def __hash__(self) -> int:
        """Defines the hash of a point as a hash of an (x, y) tuple."""
        return hash(tuple(self.x, self.y))

    def is_within_polygon(self, polygon: List) -> bool:
        """Checks if a point is within a polygon by casting a ray and counting how many 
        line segments it hits -- if the number is odd, return True (False otherwise)."""
        inside = False

        for i in range(-1, len(polygon) - 1):
            p1, p2 = polygon[i], polygon[i + 1]

            # check for correct y coordinate range
            if not (p1.y <= self.y < p2.y or p2.y <= self.y < p1.y):
                continue

            # use a linear equation to check whether the point is on the segment
            if (p2.x - p1.x) * (self.y - p1.y) / (p2.y - p1.y) + p1.x < self.x:
                inside = not inside

        # if the number of segments crossed is odd, the point is inside the polygon
        return inside


@dataclass
class Node:
    """A class for holding information about a tree branch (i. e. a node)."""

    position: Point = Point(0, 0)
    thickness: float = 1.0
    orientation: float = pi

    children: List[Node] = field(default_factory=list)


@dataclass
class AsciiTree:
    """A class for generating realistic-looking ASCII trees."""

    number_of_children: Callable[[float], int]
    # - input : current node thickness
    # - output: number of children

    children_orientation_offsets: Callable[[int, float], tuple]
    # - input : number of children, current thickness
    # - output: offsets of the directions of the branches

    child_thickness: Callable[[int, float], float]
    # - input : number of children, current thickness
    # - output: thickness of a child of the node

    child_distance: Callable[[float], float]
    # - input : current thickness
    # - output: distance to the child

    silhouette_points_distance: Callable[[float], Tuple[float, float]]
    # - input : current thickness
    # - output: distances to the left and right silhouette points

    minimum_node_thickness: float
    # - the minimum thickness a branch can have

    substitutions: List[List[Tuple[str, Callable]]]
    # - size of the resulted export image

    size: Tuple[int, int]
    # - size of the resulted export image (height, width)

    composition: List[List[List[str]]] = field(default_factory=list)
    # - the composition layers of the image

    def generate(self) -> None:
        """Generate an ASCII tree with the given functions/restrictions."""
        self.root = Node()
        self.__generate_branches(self.root)

        self.silhouette: List[Point] = []
        self.__generate_silhouette(self.root, self.silhouette)

        self.composition += self.__get_picture()

    def __get_blank_layer(self):
        """Return a blank layer of the appropriate size.."""
        return [[" "] * self.size[1] for _ in range(self.size[0])]

    def __get_blank_mask(self):
        """Return a blank layer of the appropriate size.."""
        return [[False] * self.size[1] for _ in range(self.size[0])]

    def grass(self, max_height, chars) -> None:
        """Generate a grass layer."""
        heights = get_wave(self.size[1], max_height)

        layer = self.__get_blank_layer()
        mask = self.__get_blank_mask()

        for column in range(self.size[1]):
            for row in range(int(heights[column])):
                layer[-row][column] = choice(chars)
                mask[-row][column] = True

        self.composition += [mask, layer]

    def __generate_branches(self, branch: Node) -> None:
        """Recursively generate the branches of the tree."""
        # recursion end condition (when branches get too thin)
        if branch.thickness < self.minimum_node_thickness:
            return

        children_count = self.number_of_children(branch.thickness)
        offsets = self.children_orientation_offsets(children_count, branch.thickness)

        for offset in offsets:
            # create the new child of the current node
            thickness = self.child_thickness(children_count, branch.thickness)
            distance = self.child_distance(branch.thickness)

            new_branch = Node(
                branch.position.move(distance, branch.orientation + offset),
                thickness,
                branch.orientation + offset,
            )

            # append it to the neighbours of the node and recursively generate more!
            branch.children.append(new_branch)
            self.__generate_branches(new_branch)

    def __generate_silhouette(self, branch: Node, silhouette: List[Point]) -> None:
        """Generates a polygon representing the silhouette of the tree."""
        d1, d2 = self.silhouette_points_distance(branch.thickness)

        # firstly, add the point to the left to the polygon
        silhouette.append(branch.position.move(d1, branch.orientation + pi / 2))

        # secondly, add the rest of the points in all of its child branches
        for child in branch.children:
            self.__generate_silhouette(child, silhouette)

        # lastly, add the point to the left to the polygon
        silhouette.append(branch.position.move(d2, branch.orientation - pi / 2))

    def __get_picture(self, debug=True) -> List[list, list]:
        """Generates a 2D array representing the ASCII tree."""

        picture = self.__get_blank_layer()

        # variables for centering the tree within the given size
        x_min = min(self.silhouette, key=lambda p: p.x).x
        y_min = min(self.silhouette, key=lambda p: p.y).y
        x_range = max(self.silhouette, key=lambda p: p.x).x - x_min
        y_range = max(self.silhouette, key=lambda p: p.y).y - y_min

        for x in range(len(picture)):
            for y in range(len(picture[x])):
                # scale the picture x and y to the tree coordinates
                adjusted_x = (x / self.size[0]) * x_range + x_min
                adjusted_y = (y / self.size[1]) * y_range + y_min

                # set points in the outline of the tree to '*'
                if Point(adjusted_x, adjusted_y).is_within_polygon(self.silhouette):
                    picture[x][y] = "*"

        mask = [[c != " " for c in picture[i]] for i in range(len(picture))]

        # go through each substitution phase
        for phase in self.substitutions:
            filtered_picture = self.__get_blank_layer()

            # for each point
            for x in range(len(picture)):
                for y in range(len(picture[x])):
                    # compare the neighbourhood with the substitutions
                    neighbours = self.__get_neighbourhood(x, y, picture)

                    for pattern, substitution in phase:
                        # check chars one by one
                        for c1, c2 in zip(pattern, neighbours):
                            if c1 != "a" and c1 != c2:
                                break
                        else:
                            filtered_picture[x][y] = substitution()
                            break
                    else:
                        filtered_picture[x][y] = picture[x][y]

            picture = filtered_picture

        return [mask, filtered_picture]

    def __get_neighbourhood(self, x: int, y: int, picture: List[List[str]]) -> str:
        """Return a string of the 9 chars positioned -1, 0, 1 points relative to both
        x and y. Add ' ' if the coordinates are out of bounds."""
        neighbours = ""

        for i in range(-1, 2):
            for j in range(-1, 2):
                if 0 <= x + i < len(picture) and 0 <= y + j < len(picture[0]):
                    neighbours += picture[x + i][y + j]
                else:
                    neighbours += " "

        return None if len(neighbours) != 9 else neighbours

    def __print(self, f: file, string: str, print_to_console: bool):
        """Print a string to the given file (and possibly to the console). Note that the
        new line needs to be included in the string itself."""
        f.write(string)

        if print_to_console:
            print(string, end="")

    def export(self, file_name: str = None, print_to_console: bool = True):
        """Export the file (while also possibly console-printing it in the process)."""
        # default filename to the current date
        if file_name is None:
            file_name = datetime.now().strftime("trees/%Y-%m-%d_%H-%M-%S.txt")

        with open(file_name, "w") as f:
            for row in range(self.size[0]):
                for column in range(self.size[1]):
                    for layer in range(len(self.composition)):
                        char = self.composition[layer][row][column]

                        if char is True:
                            self.__print(
                                f,
                                self.composition[layer + 1][row][column],
                                print_to_console,
                            )
                            break
                        elif type(char) != bool and char != " ":
                            self.__print(f, char, print_to_console)
                            break
                    else:
                        self.__print(f, " ", print_to_console)

                self.__print(f, "\n", print_to_console)
