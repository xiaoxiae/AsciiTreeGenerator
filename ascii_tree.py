# code maintainability
from typing import Callable, List, Tuple, Set

# tree generation
from random import random, randint, uniform
from math import pi, sin, cos

# tree export
from datetime import datetime


class Point:
    """A class for working with points."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, d: float, alpha: float):
        """Return a coordinate moved by a given distance d at an angle alpha."""
        return Point(self.x + d * cos(alpha), self.y + d * sin(alpha))

    def __add__(self, other):
        """Defines addition of points as addition of their components."""
        return Point(self.x + other.x, self.y + other.y)

    def __str__(self) -> str:
        """Defines the string representation of a point as [x; y]."""
        return f"[{self.x}; {self.y}]"

    __repr__ = __str__

    def __hash__(self):
        """Defines the hash of a point as a hash of a (x, y) tuple."""
        return hash(tuple(self.x, self.y))

    def __eq__(self, other):
        """Defines the equality of two points as the equality of their components."""
        return self.x == other.x and self.y == other.y

    def is_within_polygon(self, polygon: List) -> bool:
        """Returns True if a point is within a polygon and False otherwise by casting a ray
        and counting how many polygon line segments it hits."""
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


class Branch:
    """A struct for holding information about a tree branch."""

    def __init__(
        self, position=Point(0, 0), thickness: float = 1.0, direction: float = pi
    ):
        self.position = position
        self.thickness = thickness
        self.direction = direction

        self.branches: List[Branch] = []


class AsciiTree:
    """A class for generating realistic-looking ASCII trees."""

    def __init__(
        self,
        branching_factor: Callable[[float], int],
        branching_offsets: Callable[[int, float], tuple],
        thickness_change: Callable[[int, float], float],
        length_from_thickness: Callable[[float], float],
        silhouette_points_distance: Callable[[float], Tuple[float, float]],
        minimum_branch_thickness: float,
        size: Tuple[int, int],
    ):
        """Initializes an AsciiTree object. The meaning of the parameters is as follows:

        Generation-related functions (see parameter annotation for the types):
        - branching_factor:           current thickness                               -> current number of branches
        - branching_offsets:          current number of branches, current thickness   -> branches angle offset
        - thickness_change:           current number of branches, current thickness   -> next thickness
        - length_from_thickness:      current thickness                               -> distance of next branch
        - silhouette_points_distance: current thickness                               -> distances of silhouette points

        Constants (see parameter annotation for the types):
        - minimum_branch_thickness: the minimum thickness a branch can have
        - size: size of the resulted export image"""

        self.branching_factor = branching_factor
        self.branching_offsets = branching_offsets
        self.thickness_change = thickness_change
        self.length_from_thickness = length_from_thickness
        self.silhouette_points_distance = silhouette_points_distance

        self.minimum_branch_thickness = minimum_branch_thickness
        self.size = size

    def generate(self):
        """Generate an Ascii tree with the given functions/restrictions."""
        # generate the branches
        self.root = Branch()
        self._generate_branches(self.root)

        # generate the silhouette from the branches
        self.silhouette: List[Point] = []
        self._generate_silhouette(self.root, self.silhouette)

    def _generate_silhouette(self, branch: Branch, silhouette: List[Point]) -> None:
        """Returns a polygon representing the silhouette of the tree."""
        d1, d2 = self.silhouette_points_distance(branch.thickness)

        # point to the left
        silhouette.append(branch.position.move(d1, branch.direction + pi / 2))

        # the rest of the points under it
        for b in branch.branches:
            self._generate_silhouette(b, silhouette)

        # point on the right
        silhouette.append(branch.position.move(d2, branch.direction - pi / 2))

    def _generate_branches(self, branch: Branch) -> None:
        """Recursively generate the branches of the tree."""
        # recursion end condition (when branches get too thin)
        if branch.thickness < self.minimum_branch_thickness:
            return

        # get the number of children of the branch and their relative offsets
        branches_count = self.branching_factor(branch.thickness)
        offsets = self.branching_offsets(branches_count, branch.thickness)

        print(branch.thickness, branches_count)

        # for each branch number and its offset
        for branch_number, direction_offset in zip(range(branches_count), offsets):
            branch_thickness = self.thickness_change(branches_count, branch.thickness)
            branch_length = self.length_from_thickness(branch.thickness)

            new_branch = Branch(
                branch.position.move(
                    branch_length, branch.direction + direction_offset
                ),
                branch_thickness,
                branch.direction + direction_offset,
            )

            branch.branches.append(new_branch)
            self._generate_branches(new_branch)

    def export(self, file_name=None, print_to_console=True):
        """Export the file (while also possibly console-printing it in the process)."""
        # variables for adjusting the output to file
        x_min = min(self.silhouette, key=lambda p: p.x).x
        y_min = min(self.silhouette, key=lambda p: p.y).y
        x_range = max(self.silhouette, key=lambda p: p.x).x - x_min
        y_range = max(self.silhouette, key=lambda p: p.y).y - y_min

        # an array of the symbols representing the tree
        picture = [[" "] * self.size[1] for _ in range(self.size[0])]

        # default to the current date if the file name is not specified
        if file_name is None:
            file_name = datetime.now().strftime("trees/tree-%m-%d-%Y_%H-%M-%S.txt")

        with open(file_name, "w") as f:
            for x, line in enumerate(picture):
                for y, char in enumerate(line):
                    adjusted_x = (x / self.size[0]) * x_range + x_min
                    adjusted_y = (y / self.size[1]) * y_range + y_min

                    if Point(adjusted_x, adjusted_y).is_within_polygon(self.silhouette):
                        if print_to_console:
                            print("*", end="")
                        f.write("*")
                    else:
                        if print_to_console:
                            print(" ", end="")
                        f.write(" ")
                if print_to_console:
                    print()
                f.write("\n")
