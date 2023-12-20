SAMPLE_FREQ = 48000  # sample frequency in Hz
WINDOW_SIZE = 48000  # window size of the DFT in samples
WINDOW_STEP = 12000  # step size of window
NUM_HPS = 5  # max number of harmonic product spectrums
POWER_THRESH = 1e-6  # tuning is activated if the signal power exceeds this threshold
CONCERT_PITCH = 440  # defining a1
WHITE_NOISE_THRESH = 0.2  # everything under WHITE_NOISE_THRESH*avg_energy_per_freq is cut off

WINDOW_T_LEN = WINDOW_SIZE / SAMPLE_FREQ  # length of the window in seconds
SAMPLE_T_LENGTH = 1 / SAMPLE_FREQ  # length between two samples in seconds
DELTA_FREQ = SAMPLE_FREQ / WINDOW_SIZE  # frequency step width of the interpolated DFT
OCTAVE_BANDS = [50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 25600]


ALL_NOTES = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]

# Dictionary of standard tuning frequencies
STANDARD_TUNING_FREQUENCIES = {
    "E2": 82.41,
    "A2": 110.0,
    "D3": 146.83,
    "G3": 196.0,
    "B3": 246.94,
    "E4": 329.63
}

# Dictionary of open C tuning frequencies
OPEN_C_TUNING_FREQUENCIES = {
    "C2": 65.41,
    "G2": 98.0,
    "C3": 130.81,
    "G3": 196.0,
    "C4": 261.63,
    "E4": 329.63
}

# Dictionary of open D tuning frequencies
OPEN_D_TUNING_FREQUENCIES = {
    "D2": 73.42,
    "A2": 110.0,
    "D3": 146.83,
    "F#3": 185.0,
    "A3": 220.0,
    "D4": 293.66
}
# Dictionary of drop C tuning frequencies
DROP_C_TUNING_FREQUENCIES = {
    "C2": 65.41,
    "G2": 98.0,
    "C3": 130.81,
    "G3": 196.0,
    "C4": 261.63,
    "F4": 349.23
}

# Dictionary of drop D tuning frequencies
DROP_D_TUNING_FREQUENCIES = {
    "D2": 73.42,
    "A2": 110.0,
    "D3": 146.83,
    "G3": 196.0,
    "B3": 246.94,
    "E4": 329.63
}