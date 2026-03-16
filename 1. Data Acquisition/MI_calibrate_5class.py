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


def play_cue_sound(cue):
    if platform.system() == 'Windows':
        # dict = ['LH', 'RH', 'F', 'T]
        sound = "./sound/cue_" + cue + ".wav"
        winsound.PlaySound(sound, winsound.SND_FILENAME)

    else:
        sound = "./sound/cue_" + cue + ".wav"
        subprocess.run(["afplay", sound])


def play_beat_sound(play_sound = 'start_sound'):
    SOUND_PATH = {'start_sound': "./sound/button04a.wav",
                    'end_sound': "./sound/button02a.wav"}
    if platform.system() == 'Windows':
        sound = SOUND_PATH[play_sound]
        winsound.PlaySound(sound, winsound.SND_FILENAME)
    else:
        sound = SOUND_PATH[play_sound]
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
        start0 = start = time.time()
        play_beat_sound('start_sound')
        marker.push_sample([mark])
        # This loop will run for 3 seconds
        while time.time() - start0 < perform_time:
            cur = time.time()
            if cur - start > 1:
                play_beat_sound('end_sound')
                start = cur

    else:
        pygame.init()

        # UI Settings
        screen = pygame.display.set_mode((600, 600), display=MONITOR_NUM)
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
        play_beat_sound('start_sound')

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


def MI_move(perform_time, direction):
    mi_direction = {'LH': 'left', 'a_LH': 'left',
                    'RH': 'right', 'a_RH': 'right',
                    'F': 'down', 'a_F': 'down',
                    'T': 'up', 'a_T': 'up'}

    # Display the figure
    start0 = start = time.time()
    play_beat_sound('start_sound')
    # This loop will run for 3 seconds
    while time.time() - start0 < perform_time:
        cur = time.time()
        if cur - start > 1:
            play_beat_sound('end_sound')
            start = cur
        ori_point = imgs[direction].get_extent()
        if mi_direction[direction] == 'left':
            imgs[direction].set_extent([ori_point[0]-0.1,ori_point[1]-0.1,ori_point[2],ori_point[3]])  # left
        elif mi_direction[direction] == 'right':
            imgs[direction].set_extent([ori_point[0]+0.1,ori_point[1]+0.1,ori_point[2],ori_point[3]])
        elif mi_direction[direction] == 'up':
            imgs[direction].set_extent([ori_point[0],ori_point[1],ori_point[2]+0.1,ori_point[3]+0.1])
        elif mi_direction[direction] == 'down':
            imgs[direction].set_extent([ori_point[0],ori_point[1],ori_point[2]-0.1,ori_point[3]-0.1])
        plt.show()
        plt.pause(0.01)

# Global variable to control pause state
pause = False
bad_trial = []
bad_trial_label = []
MONITOR_NUM = 0

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
trials_per_class = 48
initial_time = 2

perform_time = 4
eog_perform_time = 30
wait_time = 2
pause_every = 20
pause_duration = 10


'''trials_per_class = 5 # for debug
#perform_time = 1 # for debug
eog_perform_time = 0.1 # for debug
wait_time = 0.1 # for debug
pause_duration = 1 # for debug
pause_every = 10 # for debug'''

fontsize = 10
MI_labels = ['LH','a_LH', 'RH', 'a_RH', 'F', 'a_F', 'T', 'a_T']
trial_labels = ['LH', 'RH', 'F', 'T', 'SSVEP']
warm_trial_labels = ['a_LH', 'LH',
                     'a_RH', 'RH',
                     'a_F', 'F',
                     'a_T', 'T',
                     'SSVEP']


# markers = {'LH':'left hand',  :'right hand', 'F':'foot', 'T':'tongue'}

total_trial_num = trials_per_class * len(trial_labels)

# 隨機SSVEP頻率 (0表示不顯示有12組,其他四個頻率9組)
SSVEP_list = np.array([0, 6])
SSVEP_list = np.repeat(SSVEP_list, 24)
#SSVEP_list = np.append(SSVEP_list, [0, 0, 0, 0, 0, 0, 0, 0, 0,
#                                    6, 6, 6, 6, 6, 6, 6, 6, 6])
random.shuffle(SSVEP_list)
SSVEP_IDX = 0
if len(SSVEP_list) != trials_per_class:
    print("WARMING: SSVEP length is not match!")

# 產生實驗順序
labels_arr = []
for j in range(int(trials_per_class * len(trial_labels) / pause_every / 2)):
    #前20輪：一實際一想像
    run_arr_temp = []
    run_arr = []
    for i in range(int(pause_every / len(trial_labels)/2)):
        for label in trial_labels:
            run_arr_temp.append(label)
    random.shuffle(run_arr_temp)
    for label in run_arr_temp:
        if label != 'SSVEP': #MI的話要複製a_mi
            run_arr.append("a_" + label)
            run_arr.append(label)
        else:
            run_arr.append(label)
            run_arr.append(label)
    #後20輪：純想像
    run_arr_temp = []
    for i in range(int(pause_every / len(trial_labels))):
        for label in trial_labels:
            run_arr_temp.append(label)
    random.shuffle(run_arr_temp)
    run_arr = np.append(run_arr, run_arr_temp)
    print(f"單組實驗順序為：{run_arr}")

    labels_arr = np.append(labels_arr, run_arr)
#def flatten(l):
#    return [item for sublist in l for item in sublist]
#labels_arr = flatten(labels_arr)
print(f"實際實驗順序為：{labels_arr}")

# load image
LH_img = Image.open("./icon/fist_L.png")
a_LH_img = Image.open("./icon/a_fist_L.png")
RH_img = Image.open("./icon/fist_R.png")
a_RH_img = Image.open("./icon/a_fist_R.png")
T_img = Image.open("./icon/tongue.png")
a_T_img = Image.open("./icon/a_tongue.png")
F_img = Image.open("./icon/foot.png")
a_F_img = Image.open("./icon/a_foot.png")

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
imgs["LH"] = ax.imshow(LH_img, alpha=0.1, extent=(0, 3, 3.75, 6.25))
imgs["a_LH"] = ax.imshow(a_LH_img, alpha=0, extent=(0, 3, 3.75, 6.25))
imgs["RH"] = ax.imshow(RH_img, alpha=0.1, extent=(7, 10, 3.75, 6.25))
imgs["a_RH"] = ax.imshow(a_RH_img, alpha=0, extent=(7, 10, 3.75, 6.25))
imgs["T"] = ax.imshow(T_img, alpha=0.1, extent=(3.75, 6.25, 7, 10))
imgs["a_T"] = ax.imshow(a_T_img, alpha=0, extent=(3.75, 6.25, 7, 10))
imgs["F"] = ax.imshow(F_img, alpha=0.1, extent=(3.75, 6.25, 0, 3))
imgs["a_F"] = ax.imshow(a_F_img, alpha=0, extent=(3.75, 6.25, 0, 3))


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

try:
    outlet.push_sample(['SESSION-begin'])

    ax.set_title(f"EOG open", loc="left", fontsize=10, fontname='monospace')
    print(f"EOG open")
    # initial state
    start_time = time.time()
    outlet.push_sample(['EOG-open trial'])

    for label in MI_labels:
        imgs[label].set_alpha(0)
        imgs[label].set_extent((3, 6.5, 3.5, 6.5))
    t.set_text("+")
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()

    play_cue_sound('EOG-OPEN')
    # time.sleep(initial_time)
    end_time = time.time()
    print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

    play_beat_sound('start_sound')
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
    play_beat_sound('end_sound')
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

    play_cue_sound('EOG-CLOSE')
    # time.sleep(initial_time)
    end_time = time.time()
    print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

    play_beat_sound('start_sound')
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
    play_beat_sound('end_sound')
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

        play_cue_sound(cur_label)
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
        else:
            t.set_text("")
            for label in MI_labels:
                imgs[label].set_alpha(1 if label == cur_label else 0)
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            start_time = time.time()
            mark = 'Warm-up' + cur_label
            outlet.push_sample([mark])

            MI_move(perform_time, cur_label)
            #time.sleep(perform_time)

            outlet.push_sample(['Warm-up trial-end'])
            for label in MI_labels:
                imgs[label].set_alpha(0)
                imgs[label].set_extent((3, 6.5, 3.5, 6.5))
        end_time = time.time()
        print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

        # break state
        start_time = time.time()
        t.set_text(f'+')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        play_beat_sound('end_sound')
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
        play_cue_sound(cur_label)
        # time.sleep(initial_time)
        end_time = time.time()
        print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

        # imaging state
        if cur_label == 'SSVEP':
            start_time = time.time()
            # mark = cur_label + "_" + str(SSVEP_list[SSVEP_IDX])
            # outlet.push_sample([mark])
            print("freq is " + str(SSVEP_list[SSVEP_IDX]) + 'Hz')
            SSVEP(perform_time, SSVEP_list[SSVEP_IDX], marker=outlet)
            SSVEP_IDX += 1
            outlet.push_sample(['trial-end'])
        else:
            t.set_text("")
            for label in MI_labels:
                imgs[label].set_alpha(1 if label == cur_label else 0)
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            start_time = time.time()
            outlet.push_sample([cur_label])
            MI_move(perform_time, cur_label)
            # time.sleep(perform_time)
            outlet.push_sample(['trial-end'])
            for label in MI_labels:
                imgs[label].set_alpha(0)
                imgs[label].set_extent((3, 6.5, 3.5, 6.5))
        end_time = time.time()
        print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

        # break state
        if (trial + 1) % pause_every == 0 and (trial + 1) != len(labels_arr):
            for s in range(0, pause_duration + 1):
                t.set_text(f'Rest {pause_duration} sec\n\nRemain {pause_duration - s} sec')
                hFigure.canvas.draw()
                hFigure.canvas.flush_events()
                if s == 0:
                    play_beat_sound('end_sound')
                time.sleep(1)
            t.set_text('')
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
        else:
            start_time = time.time()
            t.set_text(f'+')
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            play_beat_sound('end_sound')
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
        play_cue_sound(cur_label)
        # time.sleep(initial_time)
        end_time = time.time()
        print(f"initial state 實際執行時間為: {end_time - start_time} 秒")

        # imaging state
        if cur_label == 'SSVEP':
            start_time = time.time()
            # mark = cur_label + "_" + str(SSVEP_list[SSVEP_IDX])
            # outlet.push_sample([mark])
            print("freq is " + str(SSVEP_list[SSVEP_IDX]) + 'Hz')
            SSVEP(perform_time, SSVEP_list[SSVEP_IDX], marker=outlet)
            SSVEP_IDX += 1
            outlet.push_sample(['trial-end'])
        else:
            t.set_text("")
            for label in MI_labels:
                imgs[label].set_alpha(0.8 if label == cur_label else 0)
            hFigure.canvas.draw()
            hFigure.canvas.flush_events()
            start_time = time.time()
            outlet.push_sample([cur_label])
            MI_move(perform_time, cur_label)
            # time.sleep(perform_time)
            outlet.push_sample(['trial-end'])
            for label in MI_labels:
                imgs[label].set_alpha(0)
                imgs[label].set_extent((3, 6.5, 3.5, 6.5))
        end_time = time.time()
        print(f"imaging state 實際執行時間為: {end_time - start_time} 秒")

        # break state
        start_time = time.time()
        t.set_text(f'+')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        play_beat_sound('end_sound')
        # time.sleep(wait_time)
        end_time = time.time()
        print(f"break state 實際執行時間為: {end_time - start_time} 秒")
        trial += 1


    for s in range(5, 0, -1):
        t.set_text(f'Calibration End\n\n{s}')
        hFigure.canvas.draw()
        hFigure.canvas.flush_events()
        if s == 0:
            play_beat_sound('end_sound')
        time.sleep(1)
    t.set_text('')
    hFigure.canvas.draw()
    hFigure.canvas.flush_events()




except Exception as e:
    print(e)

outlet.push_sample(['calib-end'])
print(f"Bad trial: {bad_trial}")