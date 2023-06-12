import numpy as np
from magtogoek.sci_tools import rotate_heading


def test__rotate_heading():
    heading = np.array([-180, -90, 0, 90, 180])
    rotation = 45
    rotated_heading = np.array([-135, -45, 45, 135, -135])
    assert (rotate_heading(heading, rotation) == rotated_heading).all()
