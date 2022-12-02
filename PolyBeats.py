#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 09:25:25 2022

@author: MateP
"""

from tkinter import *
import numpy as np
import pyaudio
import wave
from fractions import Fraction


class AudioFile:
    # play cursor
    i = 0
    color = ['red', 'blue', 'green']
    dIsOn = np.zeros(3, dtype=int)

    def __init__(self, file, variables):
        """ Init audio stream """
        self.stream = None

        self.freqVar = variables[0]
        self.freqM1, self.freqM2, self.freqM3 = variables[1:4]
        self.cVar1, self.cVar2, self.cVar3 = variables[4:7]
        self.sineVar = variables[7]
        self.canvas = variables[8]
        self.dots = variables[9]

        ifile = wave.open(file, 'rb')
        self.framerate = ifile.getframerate()
        raw = ifile.readframes(ifile.getnframes())
        if ifile.getsampwidth() == 1:
            self.base_sample = np.frombuffer(raw, dtype=np.int8)/2**15
        elif ifile.getsampwidth() == 2:
            self.base_sample = np.frombuffer(raw, dtype=np.int16)/2**15
        elif ifile.getsampwidth() == 4:
            self.base_sample = np.frombuffer(raw, dtype=np.int32)/2**15
        elif ifile.getsampwidth() == 8:
            self.base_sample = np.frombuffer(raw, dtype=np.int64)/2**15
        else:
            raise NotImplementedError(
                f'{ifile.getsampwidth()*8}-bit .wav file not supported.')
        ifile.close()

        self.base_sample = self.base_sample[350:]
        self.base_sample = np.pad(
            self.base_sample, (0, 31*self.framerate-len(self.base_sample)))

        self.update()

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.framerate,
            output=True,
            frames_per_buffer=440*3,
            stream_callback=self.callback
        )
        # self.pause()

    def repeated(self, sample, i, total):
        # n = len(sample)
        # i = i % n
        tmp = sample[i:]
        while len(tmp) < total:
            tmp = np.concatenate((tmp, sample))
        return tmp[:total]

    def callback(self, in_data, frame_count, time_info, status):
        total = sum(self.checkedVars) if sum(self.checkedVars) > 0 else 1
        data = np.zeros(frame_count)
        for j in range(3):
            offset = self.sample_lens[j]
            M = self.multipliers[j]

            if self.checkedVars[j]:
                start, end = self.i, self.i+frame_count
                end = end - offset*(start//offset)
                start = start % offset

                if self.isSine:
                    x = np.arange(self.i, self.i+frame_count)
                    tmp = np.sin(np.pi*2*M*self.fq/self.framerate*x)
                else:
                    tmp = self.base_sample[:offset]/5
                    tmp = self.repeated(tmp, start, frame_count)
                    if end >= offset:

                        if self.dIsOn[j] == 0:
                            self.canvas.itemconfig(
                                self.dots[j], fill=self.color[j])
                        self.dIsOn[j] = np.maximum(
                            self.framerate/self.fq*.5-(end-offset), 0)

                    else:
                        lit = self.dIsOn[j] > 0
                        self.dIsOn[j] = np.maximum(
                            self.dIsOn[j] - frame_count, 0)
                        if lit and self.dIsOn[j] == 0:
                            self.canvas.itemconfig(self.dots[j], fill='')

                data += tmp/3

        self.i = self.i+frame_count

        return (data.astype(np.float32), pyaudio.paContinue)

    def update(self):
        self.fq = self.freqVar.get()

        try:
            M1 = float(Fraction(self.freqM1.get()))
            if M1 == 0:
                M1 = 1
        except (ValueError, ZeroDivisionError):
            M1 = 1

        try:
            M2 = float(Fraction(self.freqM2.get()))
            if M2 == 0:
                M2 = 1
        except (ValueError, ZeroDivisionError):
            M2 = 1

        try:
            M3 = float(Fraction(self.freqM3.get()))
            if M3 == 0:
                M3 = 1
        except (ValueError, ZeroDivisionError):
            M3 = 1

        self.multipliers = np.array([M1, M2, M3])

        self.sample_lens = (self.framerate / float(self.fq) /
                            self.multipliers).astype(int)
        self.checkedVars = [
            self.cVar1.get(), self.cVar2.get(), self.cVar3.get()]

        self.isSine = self.sineVar.get()

        for j in range(3):
            self.canvas.itemconfig(self.dots[j], fill='')
            self.dIsOn[j] = 0
        # self.i = 0

    def play(self):
        if not self.stream.is_active():
            self.stream.start_stream()

    def pause(self):
        if self.stream.is_active():
            self.stream.stop_stream()

    def close(self):
        self.stream.close()
        self.p.terminate()


def main():
    # new window with a title
    window = Tk()
    window.title('PolyBeats')

    freqVar = DoubleVar(window, 1)
    freqM1 = StringVar(window, 1)
    freqM2 = StringVar(window, 1)
    freqM3 = StringVar(window, 1)

    cVar1 = IntVar(window, 1)
    cVar2 = IntVar(window, 0)
    cVar3 = IntVar(window, 0)

    sineVar = IntVar(window, 0)

    height = 200
    width = 100
    diam = height//3
    pad = 15

    global dot
    global canvas
    canvas = Canvas(window, width=width, height=height)

    dots = []
    dots.append(canvas.create_oval(pad, pad, diam - pad, diam - pad))
    dots.append(canvas.create_oval(pad, diam + pad, diam - pad, 2*diam - pad))
    dots.append(canvas.create_oval(
        pad, 2*diam + pad, diam - pad,  3*diam - pad))

    variables = [freqVar, freqM1, freqM2, freqM3, cVar1,
                 cVar2, cVar3, sineVar, canvas, dots]
    global audio
    # Usage example for pyaudio
    audio = AudioFile("beat.wav", variables)
    # audioSine = AudioSine(freqVar)

    # create the widgets
    freq_label = Label(window, text='Base frequency [Hz]:')
    base_frequency_slider = Scale(
        window, variable=freqVar, orient=HORIZONTAL, length=800,
        resolution=1, from_=1, to=440, command=lambda *args: audio.update())

    freqM1.trace('w', lambda *args: audio.update())
    freqM2.trace('w', lambda *args: audio.update())
    freqM3.trace('w', lambda *args: audio.update())

    multiplier1_label = Label(window, text='Base frequency multiplier')
    multiplier2_label = Label(window, text='Base frequency multiplier')
    multiplier3_label = Label(window, text='Base frequency multiplier')

    multiplier1_entry = Entry(window, width=8, textvariable=freqM1)
    multiplier2_entry = Entry(window, width=8, textvariable=freqM2)
    multiplier3_entry = Entry(window, width=8, textvariable=freqM3)

    multiplier1_check = Checkbutton(window, variable=cVar1,
                                    onvalue=1, offvalue=0,
                                    command=audio.update)
    multiplier2_check = Checkbutton(window, variable=cVar2,
                                    onvalue=1, offvalue=0,
                                    command=audio.update)
    multiplier3_check = Checkbutton(window, variable=cVar3,
                                    onvalue=1, offvalue=0,
                                    command=audio.update)

    # play_button = Button(window, text="Play", command=audio.play)
    # stop_button = Button(window, text="Stop", command=audio.pause)

    sineRadio1 = Radiobutton(
        window, text='Beat', variable=sineVar, value=0, command=audio.update)
    sineRadio2 = Radiobutton(window, text='Sine wave',
                             variable=sineVar, value=1, command=audio.update)

    # using grid layout
    freq_label.grid(row=0, column=0, sticky='w')
    base_frequency_slider.grid(row=0, column=1, columnspan=25)
    multiplier1_label.grid(row=1, column=0, sticky='w')
    multiplier1_entry.grid(row=1, column=1, sticky='w')
    multiplier1_check.grid(row=1, column=2, sticky='w')

    multiplier2_label.grid(row=2, column=0, sticky='w')
    multiplier2_entry.grid(row=2, column=1, sticky='w')
    multiplier2_check.grid(row=2, column=2, sticky='w')

    multiplier3_label.grid(row=3, column=0, sticky='w')
    multiplier3_entry.grid(row=3, column=1, sticky='w')
    multiplier3_check.grid(row=3, column=2, sticky='w')

    # play_button.grid(row=5, column=0, sticky='e')
    # stop_button.grid(row=5, column=1)

    sineRadio1.grid(row=4, column=8, sticky='w')
    sineRadio2.grid(row=4, column=9, sticky='w')

    canvas.grid(row=1, rowspan=3, column=3, sticky='w')

    # start the app
    window.mainloop()
    audio.close()


if __name__ == "__main__":
    main()
