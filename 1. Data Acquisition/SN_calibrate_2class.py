"""
23/12/27:增加總實驗次數在標題列
23/12/23:調整ssvep頻率為4.3 6 7.6 10
24/01/25: 大量調整
"""
import matplotlib
import matplotlib.pyplot as plt

import time
import random
from pylsl import StreamInfo, StreamOutlet
from PIL import Image
from pynput import keyboard

# for SSVEP
import pygame
import numpy as np

# for sound
import platform
print(platform.system())
if platform.system() == 'Windows':
    import winsound
else:
    import subprocess
from matplotlib.animation import FuncAnimation


def play_start_sound(cue):
    if platform.system() == 'Windows':
        # dict = ['LH', 'RH', 'F', 'BH']
        sound = "./sound/cue_" + cue + ".wav"
        winsound.PlaySound(sound, winsound.SND_FILENAME)
        sound = "./sound/button04a.wav"
        winsound.PlaySound(sound, winsound.SND_FILENAME)
    else:
        sound = "./sound/cue_" + cue + ".wav"
        subprocess.run(["afplay", sound])
        sound = "./sound/button04a.wav"
        subprocess.run(["afplay", sound])


def play_finish_sound():
    if platform.system() == 'Windows':
        sound = "./sound/button02a.wav"
        winsound.PlaySound(sound, winsound.SND_FILENAME)
    else:
        sound = "./sound/button02a.wav"
        subprocess.run(["afplay", sound])


def SSVEP(perform_time, FREQ=6, marker=999):
    class Button():

        def __init__(self, name, color, rect, time, target_f):
            self.name = name
            self.color = color
            self.rect = rect
            self.target_f = target_f
            self.delay = 1000 / target_f
            self.time = time + self.delay
            self.show = False
            self.show_portion = 0.5
            self.time_buffer = []
            self.maxBuffer = 16

        def draw(self, screen):
            if self.show:
                pygame.draw.rect(screen, self.color, self.rect)
                pygame.draw.rect(screen, (0, 0, 0), self.rect, 5)

        def update(self, current_time):
            if current_time >= self.time:
                if self.show:
                    # show
                    self.time = current_time + self.delay * self.show_portion
                else:
                    # no-show
                    self.time = current_time + self.delay * (1 - self.show_portion)
                self.show = not self.show
                if self.show:
                    self.time_buffer.append(current_time)
                    if (len(self.time_buffer) > self.maxBuffer):
                        dif = np.diff(self.time_buffer)
                        actual_f = 1000 / np.mean(dif)
                        if actual_f - self.target_f > 0.05:
                            self.delay += 0.5
                        elif actual_f - self.target_f < 0.05:
                            self.delay -= 0.5
                        self.time_buffer.clear()

        # print the average time interval per blink of the button
        def observe(self):
            if (len(self.time_buffer) > 1):
                dif = np.diff(self.time_buffer)
                actual_f = 1000 / np.mean(dif)
                print(
                    f" {self.name} | Sample: {len(self.time_buffer):2d} | Actual Frequency: {actual_f:.5f} Hz | Delay: {self.delay:.5f} ms    \r",
                    end="\b")

    if FREQ == 0:
        mark = "idle"
        marker.push_sample([mark])
        time.sleep(perform_time)

    else:
        pygame.init()

        # UI Settings
        screen = pygame.display.set_mode((600, 600), display=1)
        current_time = pygame.time.get_ticks()
        button = Button(
            name='ssvep',
            color=(0, 0, 0),
            rect=(100, 100, 400, 400),
            time=current_time,
            target_f=FREQ,  # target frequency
        )

        start_time = time.time()
        cur_time = time.time()

        if marker != 999:
            mark = "SSVEP_" + str(FREQ)
            marker.push_sample([mark])

        while (cur_time - start_time <= perform_time):
            # clock.tick(fps)

            current_time = pygame.time.get_ticks()
            button.update(current_time)

            # --- draws ---
            screen.fill((255, 255, 255))
            button.draw(screen)
            button.observe()  # Uncomment to observe actual frequency of button
            pygame.display.update()
            cur_time = time.time()

        pygame.quit()

# Global variable to control pause state
pause = False
bad_trial = []
bad_trial_label = []

# Function to toggle pause state
def on_press(key):
    global pause
    if key == keyboard.KeyCode.from_char('p'):
        pause = not pause
        try:
            bad_trial.append(trial + 1)
            bad_trial_label.append(cur_label)
            print(f"Pause: {pause} with Bad trial {trial + 1}th: {cur_label}")
        except:
            print(f"Pause: {pause}")
    elif key == keyboard.KeyCode.from_char('b'):
        try:
            bad_trial.append(trial + 1)
            bad_trial_label.append(cur_label)
            print(f"Bad trial: {trial + 1}th: {cur_label}")
        except:
            print(f"bad label is not exist")


# Start listening for key press
listener = keyboard.Listener(on_press=on_press)
listener.start()

# initial parameter
random.seed(187964418554)
trials_per_class = 30
initial_time = 2

perform_time = 3.2
eog_perform_time = 10
wait_time = 2
pause_every = 30
pause_duration = 10

'''#trials_per_class = 5 # for debug
perform_time = 1 # for debug
eog_perform_time = 0.1 # for debug
wait_time = 0.1 # for debug
pause_duration = 1 # for debug
#pause_every = 10 # for debug'''

fontsize = 10
MI_labels = ['RH']
trial_labels = ['RH', 'SSVEP', 'idle']
warm_trial_labels = ['RH','SSVEP', 'idle']
rest_cue = ['SN_yawn','SN_body_stretch']

total_trial_num = trials_per_class * len(trial_labels)

# 產生實驗順序
labels_arr = []
for j in range(int(trials_per_class * len(trial_labels) / pause_every)):
    run_arr_temp = []
    for i in range(int(pause_every / len(trial_labels))):
        for label in trial_labels:
            run_arr_temp.append(label)
    random.shuffle(run_arr_temp)
    print(f"單組實驗順序為：{run_arr_temp}")
    labels_arr = np.append(labels_arr, run_arr_temp)
#def flatten(l):
#    return [item for sublist in l for item in sublist]
#labels_arr = flatten(labels_arr)
print(f"實際實驗順序為：{labels_arr}")

# load image
RH_img = Image.open("./icon/fist_R.png")

matplotlib.rcParams.update({'font.size': fontsize})

info = StreamInfo(name='MotorImag-Markers', type='Markers', channel_count=1,
                  nominal_srate=0, channel_format='string',
                  source_id='t8u43t98u')
outlet = StreamOutlet(info)

hFigure, ax = plt.subplots()
plt.axis('off')
# ax.set_yticklabels([''])
# ax.set_xticklabels([''])
t = plt.text(5, 5, '', ha='center', va='center', fontsize=20)
plt.xlim(xmin=-0.5, xmax=10.5)
plt.ylim(ymin=-0.5, ymax=10.5)
imgs = {}
imgs["RH"] = ax.imshow(RH_img, alpha=0.1, extent=(3.5, 6.5, 3.5, 6.5))

# fullscreen
# manager = plt.get_current_fig_manager()
# manager.window.showMaximized()

plt.ion()
plt.draw()
plt.show()

# manager = plt.get_current_fig_manager()
# manager.full_screen_toggle()
hFigure.canvas.draw()
hFigure.canvas.flush_events()

print("Press [Enter] to begin.")
x = input()
exp_start_time = time.time()

try:
    outlet.push_sample(['SESSION-begin'])

    ax.set_title(f"EOG open", loc="left", fontsize=10, fontname='monospace')
    print(f"EOG open")
    # initial state
    start_time = time.time()
    outlet.push_sample(['EOG-open trial'])

    for label in MI_labels:
        imgs[label].set_alpha(0)
    t.set_text("+")
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()

    play_start_sound('EOG-OPEN')
    # time.sleep(initial_time)
    end_time = time.time()
    print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

    start_time = time.time()
    outlet.push_sample(['EOG-open begin'])
    time.sleep(eog_perform_time)
    outlet.push_sample(['EOG-open end'])
    end_time = time.time()
    print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

    # break state
    start_time = time.time()
    t.set_text(f'+')
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()
    play_finish_sound()
    # time.sleep(wait_time)
    end_time = time.time()
    print(f"break state 實際執行時間為: {end_time - start_time} 秒")

    ax.set_title(f"EOG-CLOSE", loc="left", fontsize=10, fontname='monospace')
    print(f"EOG close")
    # initial state
    start_time = time.time()
    outlet.push_sample(['EOG-close trial'])
    t.set_text("+")
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()

    play_start_sound('EOG-CLOSE')
    # time.sleep(initial_time)
    end_time = time.time()
    print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

    start_time = time.time()
    outlet.push_sample(['EOG-close begin'])
    time.sleep(eog_perform_time)
    outlet.push_sample(['EOG-close end'])
    end_time = time.time()
    print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

    # break state
    start_time = time.time()
    t.set_text(f'+')
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()
    play_finish_sound()
    # time.sleep(wait_time)
    end_time = time.time()
    print(f"break state 實際執行時間為: {end_time - start_time} 秒")


    outlet.push_sample(['Warm-up-begin'])
    # Warm-up trial
    for trial, cur_label in enumerate(warm_trial_labels):
        #break #test
        if not plt.fignum_exists(hFigure.number):
            break
        ax.set_title(f"Trial: warmup {trial + 1}", loc="left", fontsize=10, fontname='monospace')
        print(f"Warm-up Trial {trial + 1} | {cur_label}")
        # initial state
        start_time = time.time()
        outlet.push_sample(['Warm-up trial-begin'])
        t.set_text("+")
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()

        play_start_sound("SN_" + str(cur_label))
        # time.sleep(initial_time)
        end_time = time.time()
        print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

        # imaging state
        if cur_label == 'SSVEP':
            start_time = time.time()
            mark = 'Warm-up trial-' + cur_label
            outlet.push_sample([mark])
            SSVEP(perform_time)
            outlet.push_sample(['Warm-up trial-end'])
        elif cur_label == 'idle':
            start_time = time.time()
            mark = 'Warm-up trial-' + cur_label
            outlet.push_sample([mark])
            time.sleep(perform_time)
            outlet.push_sample(['Warm-up trial-end'])
        else:
            t.set_text("")
            for label in MI_labels:
                imgs[label].set_alpha(1 if label == cur_label else 0)
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            start_time = time.time()
            mark = 'Warm-up' + cur_label
            outlet.push_sample([mark])
            time.sleep(perform_time)
            outlet.push_sample(['Warm-up trial-end'])
            for label in MI_labels:
                imgs[label].set_alpha(0)
        end_time = time.time()
        print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

        # break state
        start_time = time.time()
        t.set_text(f'+')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        play_finish_sound()
        # time.sleep(wait_time)
        end_time = time.time()
        print(f"break state 實際執行時間為: {end_time - start_time} 秒")

    outlet.push_sample(['Warm-up-end'])
    for sec in range(5, 0, -1):
        t.set_text(f'Calibration Start\n\n{sec}')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        time.sleep(1)

    # Calibration trial
    outlet.push_sample(['calib-begin'])
    for trial, cur_label in enumerate(labels_arr):
        while pause:
            t.set_text("-pause-")
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            time.sleep(2)

        if not plt.fignum_exists(hFigure.number):
            break

        ax.set_title(f"Trial: {trial + 1} / {total_trial_num}", loc="left", fontsize=10, fontname='monospace')
        print(f"Trial {trial + 1} | {cur_label} / {total_trial_num}")

        # initial state

        outlet.push_sample(['trial-begin'])
        t.set_text("+")
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        start_time = time.time()
        play_start_sound("SN_" + str(cur_label))
        # time.sleep(initial_time)
        end_time = time.time()
        print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

        # imaging state
        if cur_label == 'SSVEP':
            start_time = time.time()
            # mark = cur_label + "_" + str(SSVEP_list[SSVEP_IDX])
            # outlet.push_sample([mark])
            SSVEP(perform_time, 6, marker=outlet)
            outlet.push_sample(['trial-end'])
        elif cur_label == 'idle':
            start_time = time.time()
            outlet.push_sample([cur_label])
            time.sleep(perform_time)
            outlet.push_sample(['trial-end'])
        else: #mi
            t.set_text("")
            for label in MI_labels:
                imgs[label].set_alpha(1 if label == cur_label else 0)
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            start_time = time.time()
            outlet.push_sample([cur_label])
            time.sleep(perform_time)
            outlet.push_sample(['trial-end'])
            for label in MI_labels:
                imgs[label].set_alpha(0)
        end_time = time.time()
        print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

        # break state
        if (trial + 1) % pause_every == 0 and (trial + 1) != len(labels_arr):#打哈欠、伸懶腰
            play_finish_sound()
            time.sleep(1)
            t.set_text(f'please follow the instruction')
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            play_start_sound(rest_cue[0])
            rest_cue = [rest_cue[-1]]

            print("Input a space to continue.")
            while 1:
                time.sleep(1)
                x = input()
                if x == ' ':
                    break
            t.set_text('-ready to continue-')
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            play_finish_sound()
            time.sleep(1.5)
        else:
            start_time = time.time()#trial間的兩三秒休息
            t.set_text(f'+')
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            play_finish_sound()
            # time.sleep(wait_time)
            end_time = time.time()
            print(f"break state 實際執行時間為: {end_time - start_time} 秒")

    trial = 0
    outlet.push_sample(['bad-trial-compensate'])
    # compensate bad trial
    while len(bad_trial_label)!=0:
        cur_label = bad_trial_label[0]
        bad_trial_label = np.delete(bad_trial_label, 0)

        while pause:
            t.set_text("-pause-")
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            time.sleep(0.1)

        if not plt.fignum_exists(hFigure.number):
            break

        ax.set_title(f"Trial: {trial + 1} / {total_trial_num}", loc="left", fontsize=10, fontname='monospace')
        print(f"Trial {trial + 1} | {cur_label} / {total_trial_num}")

        # initial state

        outlet.push_sample(['trial-begin'])
        t.set_text("+")
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        start_time = time.time()
        play_start_sound("SN_" + str(cur_label))
        # time.sleep(initial_time)
        end_time = time.time()
        print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

        # imaging state
        if cur_label == 'SSVEP':
            start_time = time.time()
            SSVEP(perform_time, 6, marker=outlet)
            outlet.push_sample(['trial-end'])
        elif cur_label == 'idle':
            start_time = time.time()
            outlet.push_sample([cur_label])
            time.sleep(perform_time)
            outlet.push_sample(['trial-end'])
        else:
            t.set_text("")
            for label in MI_labels:
                imgs[label].set_alpha(0.8 if label == cur_label else 0)
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            start_time = time.time()
            outlet.push_sample([cur_label])
            time.sleep(perform_time)
            outlet.push_sample(['trial-end'])
            for label in MI_labels:
                imgs[label].set_alpha(0)
        end_time = time.time()
        print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

        # break state
        start_time = time.time()
        t.set_text(f'+')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        play_finish_sound()
        # time.sleep(wait_time)
        end_time = time.time()
        print(f"break state 實際執行時間為: {end_time - start_time} 秒")
        trial += 1


    for s in range(5, 0, -1):
        t.set_text(f'Calibration End\n\n{s}')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        if s == 0:
            play_finish_sound()
        time.sleep(1)
    t.set_text('')
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()


except Exception as e:
    print(e)

outlet.push_sample(['calib-end'])
print(f"Bad trial: {bad_trial}")

exp_end_time = time.time()
print(f"實驗總執行時間為: {exp_end_time - exp_start_time} 秒")