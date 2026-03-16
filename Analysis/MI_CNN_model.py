import numpy as np

import mne
from mne import Epochs, pick_types
from mne.decoding import CSP
import pyxdf
from mnelab.io import read_raw

from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedShuffleSplit, cross_val_score

from keras.models import Sequential
from keras.layers import Conv2D, Conv3D, MaxPooling3D, Flatten, Dense, Activation, Dropout
from keras.regularizers import l2
import tensorflow as tf
from datetime import datetime
import pickle

fname = "/content/drive/MyDrive/BCI/Recordings/1214/sub-tsun_ses-1214_task-Default_run-001_eeg.xdf"

used_eeg = 'obci_eeg1'
#1 mean unfilter, 2 use filter by OPENBCI GUI, 3 is aux

streams, header = pyxdf.load_xdf(fname)
for i in streams:
    if i['info']['name'][0] == used_eeg:
        eeg_id = i['info']['stream_id']
    print(i['info']['name'][0])
    print('stream_id: ' + str(i['info']['stream_id']))
    print('---')
print('use eeg id is ' + str(eeg_id))


raw_ori = read_raw(fname, stream_ids=[eeg_id], fs_new=125)
raw_ori.set_channel_types({used_eeg + '_0':'eeg', used_eeg + '_1':'eeg',
                           used_eeg + '_2':'eeg', used_eeg + '_3':'eeg',
                           used_eeg + '_4':'eeg', used_eeg + '_5':'eeg',
                           used_eeg + '_6':'eeg', used_eeg + '_7':'eeg',
                           used_eeg + '_8':'eeg', used_eeg + '_9':'eeg',
                           used_eeg + '_10':'eeg',used_eeg + '_11':'eeg',
                           used_eeg + '_12':'eeg',used_eeg + '_13':'eeg',
                           used_eeg + '_14':'eeg',used_eeg + '_15':'eeg'
                          })
#for data after 1207
raw_ori.rename_channels({used_eeg + '_0':'O1',  used_eeg + '_1':'O2',
                         used_eeg + '_2':'PO3', used_eeg + '_3':'PO4',
                         used_eeg + '_4':'P3',  used_eeg + '_5':'P4',
                         used_eeg + '_6':'C3',  used_eeg + '_7':'C4',
                         used_eeg + '_8':'F3',  used_eeg + '_9':'F4',
                         used_eeg + '_10':'T3', used_eeg + '_11':'T4',
                         used_eeg + '_12':'Cz', used_eeg + '_13':'Pz',
                         used_eeg + '_14':'CP1',used_eeg + '_15':'CP2'
                         })
raw_ori.reorder_channels(['O1','O2','PO3','PO4','P3','Pz','P4','CP1',
                          'CP2','T3','C3','Cz','C4','T4','F3','F4'])

raw_ori.set_montage('standard_1020')
raw = raw_ori.copy()
raw.apply_function(lambda x: x * 1e-6 /10)
#raw_filter = raw.copy().filter(l_freq=1, h_freq=50)
raw.filter(l_freq=2, h_freq=50)

events,all_events_id=mne.events_from_annotations(raw,event_id='auto')

train_event_dict = {'BH': all_events_id['BH'],
                    'F': all_events_id['F'],
                    'LH': all_events_id['LH'],
                    'RH': all_events_id['RH'],
                    'SSVEP': all_events_id['SSVEP']}

repeat_num = 20
shift = 4

aug_events = events.copy()
trial_event = [1,8,9,10,12]
num = len(aug_events)

for i in range(num):
  if aug_events[i][2] in trial_event:
    for j in range(1,repeat_num+1):
      aug_events = np.row_stack([aug_events,[events[i][0]+shift*j,events[i][1],events[i][2]]])

picks = pick_types(raw.info, eeg=True, stim=False, eog=False, exclude="bads")

reject_criteria = dict(
    eeg=0.0002 # 150 µV
)

CSP_epochs = mne.Epochs(
    raw,
    events,
    event_id = train_event_dict,
    tmin = 0,
    tmax = 3,
    picks = picks,
    baseline = None,
    reject = reject_criteria,
    preload = True
)


train_epochs = mne.Epochs(
    raw,
    aug_events,
    event_id = train_event_dict,
    tmin = 0,
    tmax = 3,
    picks = picks,
    baseline = None,
    reject = reject_criteria,
    preload = True
)

event_name = ["LH", "RH", "F", "BH","SSVEP"]
t_min = 0.2
t_max = 2.2
CSP_m = 8

# set binary class combination
binary_class_dict = {}
id = 0
for i, name in enumerate(event_name):
  for j in range(i+1,len(event_name)):
    binary_class_dict[id] = (event_name[i], event_name[j])
    id += 1
del id
'''
example output
binary_class_dict =  {0: ('LH', 'RH'),
                      1: ('LH', 'F'),
                      2: ('LH', 'T'),
                      3: ('RH', 'F'),
                      4: ('RH', 'T'),
                      5: ('F', 'T')}
'''

band_default = (6, 30)  # Hz
band_dict = {}
for binary_class in binary_class_dict.values():
  band_dict[binary_class] = band_default    # set as default first, will adjust value in part1

def csp_svm(class1, class2, Bl, Bh, random_state):
  scores = []
  epochs_filtered = CSP_epochs.copy()[class1,class2].crop(tmin=t_min, tmax=t_max).filter(Bl, Bh, method='iir',verbose = False)
  epochs_data = epochs_filtered.copy().get_data(copy = True)
  labels = CSP_epochs[class1, class2].events[:, -1]
  cv = StratifiedShuffleSplit(30, test_size=0.25,random_state=random_state)

  # Assemble a classifier
  svm = SVC()
  csp = CSP(n_components=CSP_m, reg=None, log=True, norm_trace=False)

  # Use scikit-learn Pipeline with cross_val_score function
  clf = Pipeline([("CSP", csp), ("SVC", svm)])
  scores = cross_val_score(clf, epochs_data, labels, cv=cv, n_jobs=-1)

  # Printing the results
  accuracy = np.mean(scores)
  print(f"Bl {Bl} | Bh {Bh} | Classification accuracy: {accuracy}")
  return accuracy

def bestBand_selected(class1, class2):
  print(f"Start selecting combination {class1}/{class2}...")
  Bl = band_dict[(class1,class2)][0]
  Bh = band_dict[(class1,class2)][1]
  random_state = 0
  A1 = 0
  A2 = 0
  result = {}

  #adjust Bl
  """
  #Bl try downward
  while A1 >= A2 and Bl >= 0:
    A2 = A1
    if (Bl-2,Bh) not in result:
      result[(Bl-2,Bh)] = csp_svm(class1, class2, Bl-2, Bh, random_state)
    A1 = result[(Bl-2,Bh)]
    if A1 >= A2:
      Bl = Bl - 2
  """
  result[(Bl,Bh)] = csp_svm(class1, class2, Bl, Bh, random_state)
  A1 = result[(Bl,Bh)]
  #Bl try upward
  while A1 >= A2 and Bl <= Bh-6:
    A2 = A1
    if (Bl+2,Bh) not in result:
      result[(Bl+2,Bh)] = csp_svm(class1, class2, Bl+2, Bh, random_state)
    A1 = result[(Bl+2,Bh)]
    if A1 >= A2:
      Bl = Bl + 2
  print(f"--------------------- Final Bl = {Bl} ---------------------")

  #adjust Bh
  #Bh try downward
  A1 = A2
  while A1 >= A2 and Bh >= Bl+6:
    A2 = A1
    if (Bl,Bh-2) not in result:
      result[(Bl,Bh-2)] = csp_svm(class1, class2, Bl, Bh-2, random_state)
    A1 = result[(Bl,Bh-2)]
    if A1 >= A2:
      Bh = Bh - 2
  #Bl try upward
  A1 = A2
  while A1 >= A2 and Bh <= 38:
    A2 = A1
    if (Bl,Bh+2) not in result:
      result[(Bl,Bh+2)] = csp_svm(class1, class2, Bl, Bh+2, random_state)
    A1 = result[(Bl,Bh+2)]
    if A1 >= A2:
      Bh = Bh + 2
  print(f"--------------------- Final Bh = {Bh} ---------------------")
  print(f"Combination {class1}/{class2} Finished| {Bl} - {Bh} \n")
  return (Bl, Bh)

for i,binary_class in binary_class_dict.items():
  class1, class2 = binary_class
  band_dict[binary_class] = bestBand_selected(class1, class2)

CSPs = {}
for binary_class in binary_class_dict.values():
  print("====================================================")
  print(binary_class)
  #CSPs[binary_class] = CSP(n_components=CSP_m, reg=None, log=None, transform_into = 'average_power', norm_trace=False)
  CSPs[binary_class] = CSP(n_components=CSP_m, reg=None, log=None, transform_into = 'csp_space', norm_trace=False)
  class1, class2 = binary_class
  Bl, Bh = band_dict[binary_class]
  epochs_filtered = CSP_epochs.copy()[class1,class2].crop(tmin=t_min, tmax=t_max).filter(Bl, Bh, method='iir',verbose = False)
  epochs_data = epochs_filtered.copy().get_data()
  labels = CSP_epochs[class1, class2].events[:, -1]
  CSPs[binary_class].fit(epochs_data, labels)
  print(CSPs[binary_class])
  print("====================================================")


data_of_combination = {}
sfreq=125
sample_per_sec = int(sfreq)
sample_per_step = int(sample_per_sec/2)
sample_per_step

#這邊有大修正 by tsun
for binary_class in binary_class_dict.values():
  class1, class2 = binary_class
  Bl, Bh = band_dict[binary_class]
  epochs_fil = train_epochs.copy().crop(tmin=t_min, tmax=t_max).filter(Bl, Bh, method='iir', verbose = False)
  data_fil = epochs_fil.get_data(copy = True)

  #原本的算法
  data_csp = CSPs[(class1, class2)].transform(data_fil)
  #可能是照paper的寫法:
  #data_csp = np.zeros(data_fil.shape)
  #for idx, single_trail in enumerate(data_fil):
  #  data_csp[idx] = np.dot(CSPs[(class1, class2)].filters_[:].T,single_trail)

  section1 = np.log(np.var(data_csp[:,:,:sample_per_sec], axis = 2, keepdims=True))
  section2 = np.log(np.var(data_csp[:,:,sample_per_step*1:sample_per_step*1+sample_per_sec], axis = 2, keepdims=True))
  section3 = np.log(np.var(data_csp[:,:,sample_per_step*2:sample_per_step*2+sample_per_sec], axis = 2, keepdims=True))
  data_of_combination[binary_class] = np.concatenate((section1, section2, section3), axis=2)

  merged_arrays = []

for binary_class in data_of_combination:
    array = data_of_combination[binary_class]
    merged_arrays.append(array)

data_merged = np.concatenate(merged_arrays, axis=1)

X_shape = data_merged.shape
X_train = data_merged.reshape((X_shape[0],X_shape[1],X_shape[2],1,1))
y_unlabel = train_epochs.events[:, -1]
X_train.shape

y = np.zeros(shape=y_unlabel.shape)
for idx in range(len(y_unlabel)):
  if y_unlabel[idx] == 1:
    y[idx] = int(y_unlabel[idx]-1)
  elif y_unlabel[idx] == 12:
    y[idx] = int(y_unlabel[idx]-8)
  else:
    y[idx] = int(y_unlabel[idx]-7)
y_train = y.astype(int)

# input shape
input_shape = (80, 3, 1, 1)

# 建構 CNN 模型
def create_cnn_model():
    model = Sequential()
    model.add(Conv3D(16, (9, 5, 1), input_shape=input_shape, activation='relu', padding='same', kernel_regularizer=l2(0.0001)))
    #model.add(Conv3D(16, (9, 5, 16), activation='relu', padding='same', kernel_regularizer=l2(0.0001)))
    model.add(MaxPooling3D(pool_size=(2, 2, 1), strides=(2, 2, 1)))
    #model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Activation('relu'))
    #model.add(Dropout(0.5))
    model.add(Dense(5, activation='softmax'))
    return model

# 使用舊版的 SGD 優化器，避免問題
optimizer = tf.keras.optimizers.legacy.SGD(learning_rate=0.01, momentum=0.1836)

callback = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy',
                                            patience=5, start_from_epoch=50,
                                            restore_best_weights=True)
model = create_cnn_model()
model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])

model.fit(X_train, y_train,
          epochs= 150, batch_size= 40,
          shuffle=True, validation_split=0.1,)
#          callbacks=[callback])

current_time = datetime.now()

model.save('my_model_'+str(current_time)+'.h5')

with open('variables.pickle', 'wb') as f:
    pickle.dump(binary_class_dict, f)
    pickle.dump(band_dict, f)
    pickle.dump(CSPs, f)
