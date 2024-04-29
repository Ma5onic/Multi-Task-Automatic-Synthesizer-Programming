import numpy as np
from scipy.io import wavfile
import os
import librosa
import matplotlib.pyplot as plt
import librosa.display
import dawdreamer as dd
import itertools


def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles

#folder where diva data is stored
data_folder = "Serum Presets"

#get list of fxp files
fxp_files = getListOfFiles(data_folder)


if __name__ == "__main__":
    #load data of diva parameters and get one data point
    data = np.load("serum_params.npy", allow_pickle=True)
    preset_names = np.load("serum_preset_name.npy", allow_pickle=True)


    #path to plugin
    plugin_path = "Serum.vst"

    SAMPLING_RATE = 44100

    #create renderman engine with plugin loaded
    engine = dd.RenderEngine(SAMPLING_RATE, 512)
    engine.set_bpm(120)
    synth = engine.make_plugin_processor("Serum", plugin_path)
    engine.load_graph([(synth, [])])

    #initialize list of asp data
    asp_data = list()
    #generate audio for 10 presets
    for i,d_point in enumerate(data):

        #change preset
        for j in range(len(d_point)):
            synth.set_parameter(j,d_point[j])

        #Check RMS
        synth.clear_midi()
        synth.add_midi_note(60,255,0.25,3)
        
        engine.render(5)
        audio = engine.get_audio()
        #combine to mono
        audio = audio[0] + audio[1]
        rms = np.sqrt(np.mean(audio**2)) 

        if rms > 0.01:

            #perform hpss
            D = librosa.stft(audio)
            H,P = librosa.decompose.hpss(D, margin=3.0)
            R = D - (H+P)
            d_mag = np.mean(np.abs(D))
            h_mag = np.mean(np.abs(H))
            p_mag = np.mean(np.abs(P))
            r_mag = np.mean(np.abs(R))
            add_mag = np.mean(np.abs(H+P+R))

            h_per = round(h_mag/d_mag,2)*100
            p_per = round(p_mag/d_mag,2)*100
            r_per = round(r_mag/d_mag,2)*100
            add_per = round(add_mag/d_mag,2)*100

            # print(h_per)
            # print(p_per)
            # print(r_per)
            # print(add_per)

            l_value = 20

            if h_per > 20:
                l_value = 40

            if h_per > 40:
                l_value = 60
            
            if h_per > 60:
                l_value = 80

            if h_per > 80:
                l_value = 100

            # Define notes and velocities to generate
            notes = [12 + 12*i for i in range(6)]  # C notes from C2 to C7
            velocities = [32, 64, 127]  # Three velocity levels

            mel_specs = []
            for note, velocity in itertools.product(notes, velocities):
                # Play new note
                synth.clear_midi()
                synth.add_midi_note(note, velocity, 0.25, 3)

                engine.render(5)
                audio = engine.get_audio()
                audio = audio[0] + audio[1]  # Combine to mono

                # Create and normalize mel spectrogram
                mel_spec = librosa.feature.melspectrogram(y=audio, sr=SAMPLING_RATE)
                mel_spec = librosa.power_to_db(mel_spec, ref=np.max)
                # mel_spec = mel_spec - np.min(mel_spec)
                # mel_spec = mel_spec / np.max(mel_spec)

                mel_specs.append(mel_spec)
                # fig, ax = plt.subplots(nrows=1, ncols=1, sharex=True)
                # img = librosa.display.specshow(mel_spec, y_axis='mel', x_axis='time', ax=ax)
                # ax.set(title='Mel-frequency power spectrogram')
                # ax.label_outer()
                # fig.colorbar(img, ax=ax, format = "%+2.f dB")
                # wavfile.write('audio ' + str(i) + '.' + str(note) + '.wav', SAMPLING_RATE, audio.transpose())
                # plt.show()
        
            asp_data.append([mel_specs,d_point,l_value,preset_names[i]])

    np.save("asp_data_serum", np.array(asp_data))
    print(np.array(asp_data))
    print("Done!!")
