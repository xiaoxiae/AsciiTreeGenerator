from random import randint


def get_wave(length, maximum, iterations=10):
    """Generate an array of given length with the values being from 0 to maximum, with
    the values being brought closer together by averaging."""
    wave = [randint(0, maximum) for _ in range(length)]

    for _ in range(iterations):
        wave = [(wave[i - 2] + wave[i - 1] + wave[i]) / 3 for i in range(len(wave))]

    return wave
