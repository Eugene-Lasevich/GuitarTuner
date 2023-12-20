import tkinter as tk
import os
import numpy as np
import scipy.fftpack
import sounddevice as sd
import time
import keyboard  # For key processing
from settings import *
import copy

HANN_WINDOW = np.hanning(WINDOW_SIZE)

def find_closest_note(pitch, standard_tuning_freqs):
    note_distances = {note: abs(pitch - freq) for note, freq in standard_tuning_freqs.items()}
    closest_note = min(note_distances, key=note_distances.get)
    closest_pitch = standard_tuning_freqs[closest_note]
    return closest_note, closest_pitch

def find_closest_note_1(pitch):
    i = int(np.round(np.log2(pitch / CONCERT_PITCH) * 12))
    closest_note = ALL_NOTES[i % 12] + str(4 + (i + 9) // 12)
    closest_pitch = CONCERT_PITCH * 2 ** (i / 12)
    return closest_note, closest_pitch

def process_input_data(indata, window_samples):
    window_samples = np.concatenate((window_samples, indata[:, 0]))
    window_samples = window_samples[len(indata[:, 0]):]
    return window_samples

def calculate_signal_power(samples):
    return (np.linalg.norm(samples, ord=2, axis=0) ** 2) / len(samples)

def calculate_magnitude_spectrum(samples, window):
    hann_samples = samples * window
    return abs(scipy.fftpack.fft(hann_samples)[:len(hann_samples) // 2])

def suppress_main_hum(magnitude_spec, delta_freq):
    for i in range(int(62 / delta_freq)):
        magnitude_spec[i] = 0
    return magnitude_spec

def calculate_avg_energy_per_frequency(magnitude_spec, octave_bands, delta_freq, white_noise_thresh):
    for j in range(len(octave_bands) - 1):
        ind_start = int(octave_bands[j] / delta_freq)
        ind_end = int(octave_bands[j + 1] / delta_freq)
        ind_end = ind_end if len(magnitude_spec) > ind_end else len(magnitude_spec)
        avg_energy_per_freq = (
                (np.linalg.norm(magnitude_spec[ind_start:ind_end], ord=2, axis=0) ** 2) / (ind_end - ind_start))
        avg_energy_per_freq = avg_energy_per_freq ** 0.5
        for i in range(ind_start, ind_end):
            magnitude_spec[i] = magnitude_spec[i] if magnitude_spec[i] > white_noise_thresh * avg_energy_per_freq else 0
    return magnitude_spec

def interpolate_spectrum(magnitude_spec, num_hps):
    return np.interp(np.arange(0, len(magnitude_spec), 1 / num_hps), np.arange(0, len(magnitude_spec)),
                     magnitude_spec) / np.linalg.norm(magnitude_spec, ord=2, axis=0)

def calculate_hps(mag_spec_ipol, num_hps):
    hps_spec = copy.deepcopy(mag_spec_ipol)
    for i in range(num_hps):
        tmp_hps_spec = np.multiply(hps_spec[:int(np.ceil(len(mag_spec_ipol) / (i + 1)))], mag_spec_ipol[::(i + 1)])
        if not any(tmp_hps_spec):
            break
        hps_spec = tmp_hps_spec
    return hps_spec

def find_max_frequency(hps_spec, sample_freq, window_size, num_hps):
    max_ind = np.argmax(hps_spec)
    return max_ind * (sample_freq / window_size) / num_hps

def update_note_buffer(closest_note, note_buffer):
    note_buffer.insert(0, closest_note)
    note_buffer.pop()
    return note_buffer
def select_tuning(tuning):
    tunings = {
        "standard": STANDARD_TUNING_FREQUENCIES,
        "open_c": OPEN_C_TUNING_FREQUENCIES,
        "open_d": OPEN_D_TUNING_FREQUENCIES,
        "drop_c": DROP_C_TUNING_FREQUENCIES,
        "drop_d": DROP_D_TUNING_FREQUENCIES
    }
    return tunings.get(tuning, STANDARD_TUNING_FREQUENCIES)

class TunerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HPS Guitar Tuner")
        self.root.geometry("750x200")  # Устанавливаем размер окна
        self.tuning_var = tk.StringVar()
        self.tuning_var.set("standard")
        self.note_buffer = ["1", "2"]
        self.window_samples = [0 for _ in range(WINDOW_SIZE)]

        self.create_widgets()

    def create_widgets(self):
        tuning_menu_label = tk.Label(self.root, text="Select the desired tuning:")
        tuning_menu_label.pack()

        tuning_menu = tk.OptionMenu(self.root, self.tuning_var,
                                    "standard",
                                    "open_c",
                                    "open_d",
                                    "drop_c",
                                    "drop_d",
                                    "tune")
        tuning_menu.pack()

        start_button = tk.Button(self.root, text="Start Tuner", command=self.start_tuner)
        start_button.pack()

        self.result_label = tk.Label(self.root, text="")
        self.result_label.pack()

        # Устанавливаем шрифт размером 32 для метки результата
        self.result_label.config(font=("Helvetica", 32))

    def start_tuner(self):
        global STANDARD_TUNING_FREQUENCIES

        def check_quit():
            if keyboard.is_pressed('q'):
                self.root.destroy()

        try:
            selected_tuning = self.tuning_var.get()
            if selected_tuning == "tune":
                with sd.InputStream(channels=1, callback=self.callback_1, blocksize=WINDOW_STEP, samplerate=SAMPLE_FREQ):
                    # self.root.after(500, check_quit)
                    self.root.mainloop()  # Запускаем главный цикл tkinter
            else:
                STANDARD_TUNING_FREQUENCIES = select_tuning(selected_tuning)
                print("Starting HPS guitar tuner... (Press 'q' to quit)")
                with sd.InputStream(channels=1, callback=self.callback, blocksize=WINDOW_STEP, samplerate=SAMPLE_FREQ):
                    # self.root.after(500, check_quit)
                    self.root.mainloop()  # Запускаем главный цикл tkinter
        except Exception as exc:
            print(str(exc))

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
            return
        if any(indata):
            self.window_samples = process_input_data(indata, self.window_samples)

            # skip if signal power is too low
            signal_power = calculate_signal_power(self.window_samples)
            if signal_power < POWER_THRESH:
                os.system('cls' if os.name == 'nt' else 'clear')
                self.print_closest_note_result_tk("Closest note: ...")
                return

            magnitude_spec = calculate_magnitude_spectrum(self.window_samples, HANN_WINDOW)
            magnitude_spec = suppress_main_hum(magnitude_spec, DELTA_FREQ)
            magnitude_spec = calculate_avg_energy_per_frequency(magnitude_spec, OCTAVE_BANDS, DELTA_FREQ, WHITE_NOISE_THRESH)

            # interpolate spectrum
            mag_spec_ipol = interpolate_spectrum(magnitude_spec, NUM_HPS)
            hps_spec = calculate_hps(mag_spec_ipol, NUM_HPS)

            max_freq = find_max_frequency(hps_spec, SAMPLE_FREQ, WINDOW_SIZE, NUM_HPS)
            closest_note, closest_pitch = find_closest_note(max_freq, STANDARD_TUNING_FREQUENCIES)
            max_freq = round(max_freq, 1)
            closest_pitch = round(closest_pitch, 1)

            self.note_buffer = update_note_buffer(closest_note, self.note_buffer)
            self.print_closest_note_result_tk(f"Closest note: {closest_note} {max_freq}/{closest_pitch}")
        else:
            print('no input')


    def callback_1(self, indata, frames, time, status):
        if status:
            print(status)
            return
        if any(indata):
            self.window_samples = process_input_data(indata, self.window_samples)
            signal_power = calculate_signal_power(self.window_samples)

            if signal_power < POWER_THRESH:
                os.system('cls' if os.name == 'nt' else 'clear')
                self.print_closest_note_result_tk("Closest note: ...")
                return

            magnitude_spec = calculate_magnitude_spectrum(self.window_samples, HANN_WINDOW)
            magnitude_spec = suppress_main_hum(magnitude_spec, DELTA_FREQ)
            magnitude_spec = calculate_avg_energy_per_frequency(magnitude_spec, OCTAVE_BANDS, DELTA_FREQ, WHITE_NOISE_THRESH)

            mag_spec_ipol = interpolate_spectrum(magnitude_spec, NUM_HPS)
            hps_spec = calculate_hps(mag_spec_ipol, NUM_HPS)

            max_freq = find_max_frequency(hps_spec, SAMPLE_FREQ, WINDOW_SIZE, NUM_HPS)

            closest_note, closest_pitch = find_closest_note_1(max_freq)
            max_freq = round(max_freq, 1)
            closest_pitch = round(closest_pitch, 1)

            self.note_buffer = update_note_buffer(closest_note, self.note_buffer)
            self.print_closest_note_result_tk(f"Closest note: {closest_note} {max_freq}/{closest_pitch}")
        else:
            print('no input')


    def print_closest_note_result_tk(self, result_text):
        self.result_label.config(text=result_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = TunerApp(root)
    root.mainloop()