# import the AsciiTree class
from lib import AsciiTree
from sys import exit

# functions for generating the trees
from random import random, randint, uniform, choice
from math import pi


# various tree settings
trees = {
    "oak": (
        lambda t: int(1.7 / t),
        lambda n, __: (0,)
        if n <= 1
        else tuple(pi / 5 - ((pi / 5) * 2 / (n - 1)) * i for i in range(n)),
        lambda _, x: x * uniform(0.55, 0.7),
        lambda x: x * uniform(0.5, 1),
        lambda x: (x / 2 * uniform(0.6, 0.8), x / 2 * uniform(0.6, 0.8)),
        0.1,
    ),
}

t_type = input(f"Select tree kind ({' / '.join(t for t in trees)}): ")

t_size = tuple(
    map(
        lambda x: int(x.strip()),
        input(f"Select output size in the form 'width, height': ").split(","),
    )
)

tree = AsciiTree(*trees[t_type], t_size)
tree.generate()
tree.export()
