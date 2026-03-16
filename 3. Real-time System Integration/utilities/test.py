import time
from matplotlib import pyplot as plt
from mne_lsl.stream import StreamLSL as Stream
from mne_lsl.player import PlayerLSL as Player
from pathlib import Path

import mne
from pynput import keyboard

# Global variable to control pause state
pause = False

# Function to toggle pause state
def on_press(key):
    global pause
    if key == keyboard.KeyCode.from_char('p'):
        pause = not pause

# Bind space key to toggle_pause function
listener = keyboard.Listener(on_press=on_press)
listener.start()


SAMPLELSL_PATH = Path("/Users/alkalisk/Downloads/test_mock_lsl.fif")

player = Player(SAMPLELSL_PATH)
player.start()
stream = Stream(bufsize=3)
raw = mne.io.read_raw(SAMPLELSL_PATH)
player_length = len(raw)/125
mode = 'rp'
print('starting replay...')

stream.connect(acquisition_delay=0.001)
first_time = time.time()
info = stream.info
sfreq = info['sfreq']

plot_time = 2

plt.ion()
figure, ax = plt.subplots(4, 1, sharex=True, constrained_layout=True)

start_time = time.time()
while 1:
    # 至少每X秒計算一次
    #cur_time = time.time()
    #if cur_time - start_time < 2:
    #    continue
    #start_time = time.time()

    while pause:
        time.sleep(0.1)

    data = stream.get_data(plot_time)[0]
    rt_raw = mne.io.RawArray(data, info)
    #rt_raw.apply_function(lambda x: x * 1e-6)

    for k, data_channel in enumerate(rt_raw.get_data()):
        ax[k].cla()
        ax[k].plot(range(0, int(sfreq)*plot_time), data_channel)
        ax[k].set_ylim(-50, 50)
    cur_time = time.time()
    print(f"===plotting {cur_time - first_time}===")
    figure.canvas.draw()
    figure.canvas.flush_events()
    #time.sleep(0.5)

