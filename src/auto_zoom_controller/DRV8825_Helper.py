
class Direction:
    forward = 'forward'
    backward = 'backward'


class Stepper:
    """
    # 1.8 degree: nema23, nema14
    # softward Control :
    # 'fullstep': A cycle = 200 steps
    # 'halfstep': A cycle = 200 * 2 steps
    # '1/4step': A cycle = 200 * 4 steps
    # '1/8step': A cycle = 200 * 8 steps
    # '1/16step': A cycle = 200 * 16 steps
    # '1/32step': A cycle = 200 * 32 steps
    """
    softward = 'softward'
    hardward = 'hardward'

    fullstep = 'fullstep'
    halfstep = 'halfstep'
    step_1_4 = '1/4step'
    step_1_8 = '1/8step'
    step_1_16 = '1/16step'
    step_1_32 = '1/32step'
