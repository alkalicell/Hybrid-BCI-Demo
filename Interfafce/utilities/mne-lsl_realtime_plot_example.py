import time
from matplotlib import pyplot as plt
from mne_lsl.stream import StreamLSL as Stream
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

host_id = 'openbcigui'
used_eeg = "obci_eeg1"
stream = Stream(name=used_eeg,stype = 'EEG',source_id = host_id,  bufsize=2)  # 5 seconds of buffer
stream.connect(acquisition_delay=0.001)
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
    rt_raw.apply_function(lambda x: x * 1e-6)

    for k, data_channel in enumerate(rt_raw.get_data()):
        ax[k].cla()
        ax[k].plot(range(0, int(sfreq)*plot_time), data_channel)
        ax[k].set_ylim(-100*1e-6, 100*1e-6)

    figure.canvas.draw()
    figure.canvas.flush_events()
    #time.sleep(0.01)
