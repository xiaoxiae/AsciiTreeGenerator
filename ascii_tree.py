# code maintainability
from typing import Callable, List, Tuple, Set

# tree generation
from random import random, randint, uniform
from math import pi, sin, cos

# tree export
from datetime import datetime


class Point:
    """A class for working with points."""

    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    def move(self, d: float, alpha: float):
        """Return a coordinate moved by a given distance d at an angle alpha."""
        return Point(self.x + d * cos(alpha), self.y + d * sin(alpha))

    def __add__(self, other):
        """Defines the addition of points as addition of their components."""
        return Point(self.x + other.x, self.y + other.y)

    def __str__(self) -> str:
        """Defines the string representation of a point as [x; y]."""
        return f"[{self.x}; {self.y}]"

    __repr__ = __str__

    def __hash__(self):
        """Defines the hash of a point as a hash of an (x, y) tuple."""
        return hash(tuple(self.x, self.y))

    def __eq__(self, other):
        """Defines the equality of two points as the equality of their components."""
        return self.x == other.x and self.y == other.y

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


class Node:
    """A class for holding information about a tree branch (i. e. a node)."""

    def __init__(
        self, position=Point(), thickness: float = 1.0, orientation: float = pi
    ):
        # information about the state of the node
        self.position = position
        self.thickness = thickness
        self.orientation = orientation

        # information about the children of the node
        self.children: List[Node] = []


class AsciiTree:
    """A class for generating realistic-looking ASCII trees. 

    PARAMETERS DESCRIPTION:
    =======================

    number_of_children (float -> int)
    - input : current node thickness
    - output: number of children

    children_orientation_offsets (int, float -> (float,...))
    - input : number of children, current thickness
    - output: offsets of the directions of the branches

    child_thickness (int, float -> float)
    - input : number of children, current thickness
    - output: thickness of a child of the node

    child_distance (float -> float)
    - input : current thickness
    - output: distance to the child

    silhouette_points_distance (float -> (float, float))
    - input : current thickness
    - output: distances to the left and right silhouette points

    CONSTANTS DESCRIPTION:
    ======================
    minimum_node_thickness (float): the minimum thickness a branch can have
    size ((float, float)): size of the resulted export image
    """

    def __init__(
        self,
        number_of_children: Callable[[float], int],
        children_orientation_offsets: Callable[[int, float], tuple],
        child_thickness: Callable[[int, float], float],
        child_distance: Callable[[float], float],
        silhouette_points_distance: Callable[[float], Tuple[float, float]],
        minimum_node_thickness: float,
        size: Tuple[int, int],
    ):
        """Initializes an AsciiTree object."""
        self.number_of_children = number_of_children
        self.children_orientation_offsets = children_orientation_offsets
        self.child_thickness = child_thickness
        self.child_distance = child_distance
        self.silhouette_points_distance = silhouette_points_distance

        self.minimum_node_thickness = minimum_node_thickness
        self.size = size

    def generate(self) -> None:
        """Generate an ASCII tree with the given functions/restrictions."""
        # generate the branches
        self.root = Node()
        self._generate_branches(self.root)

        # generate the silhouette from the branches
        self.silhouette: List[Point] = []
        self._generate_silhouette(self.root, self.silhouette)

        self.picture: List[List[str]] = [
            [" "] * self.size[1] for _ in range(self.size[0])
        ]
        self._generate_picture(self.picture)

    def _generate_branches(self, branch: Node) -> None:
        """Recursively generate the branches of the tree."""
        # recursion end condition (when branches get too thin)
        if branch.thickness < self.minimum_node_thickness:
            return

        # number of children and the offsets of their orientations
        count = self.number_of_children(branch.thickness)
        offsets = self.children_orientation_offsets(count, branch.thickness)

        for offset in offsets:
            # create the new child of the current node
            thickness = self.child_thickness(count, branch.thickness)
            distance = self.child_distance(branch.thickness)

            new_branch = Node(
                branch.position.move(distance, branch.orientation + offset),
                thickness,
                branch.orientation + offset,
            )

            # append it to the neighbours of the node and recursively generate more!
            branch.children.append(new_branch)
            self._generate_branches(new_branch)

    def _generate_silhouette(self, branch: Node, silhouette: List[Point]) -> None:
        """Generates a polygon representing the silhouette of the tree."""
        d1, d2 = self.silhouette_points_distance(branch.thickness)

        # firstly, add the point to the left to the polygon
        silhouette.append(branch.position.move(d1, branch.orientation + pi / 2))

        # secondly, add the rest of the points in all of its child branches
        for child in branch.children:
            self._generate_silhouette(child, silhouette)

        # lastly, add the point to the left to the polygon
        silhouette.append(branch.position.move(d2, branch.orientation - pi / 2))

    def _generate_picture(self, picture) -> None:
        """Generates a 2D array representing the silhouette of the tree."""
        # variables for centering the tree within the given size
        x_min = min(self.silhouette, key=lambda p: p.x).x
        y_min = min(self.silhouette, key=lambda p: p.y).y
        x_range = max(self.silhouette, key=lambda p: p.x).x - x_min
        y_range = max(self.silhouette, key=lambda p: p.y).y - y_min

        for x in range(len(self.picture)):
            for y in range(len(self.picture[x])):
                # scale the picture x and y to the tree coordinates
                adjusted_x = (x / self.size[0]) * x_range + x_min
                adjusted_y = (y / self.size[1]) * y_range + y_min

                # set points in the outline of the tree to '*'
                if Point(adjusted_x, adjusted_y).is_within_polygon(self.silhouette):
                    picture[x][y] = "*"

    def export(self, file_name=None, print_to_console=True):
        """Export the file (while also possibly console-printing it in the process)."""
        if file_name is None:
            # default filename to the current date
            file_name = datetime.now().strftime("trees/tree-%m-%d-%Y_%H-%M-%S.txt")

        with open(file_name, "w") as f:
            for row in self.picture:
                for char in row:
                    if print_to_console:
                        print(char, end="")
                    f.write(char)
                if print_to_console:
                    print()
                f.write("\n")
