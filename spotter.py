#!/usr/bin/python3

import os
import sys
import json
import vosk
import pyaudio
import collections
from time import sleep
from cffi import FFI as _FFI

class RingBuffer(object):
    """Ring buffer to hold audio from PortAudio"""
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        """Adds data to the end of buffer"""
        self._buf.extend(data)

    def get(self):
        """Retrieves data from the beginning of buffer and clears it"""
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp

class VoskTest:
    def __init__(self):
        self._ignore_stderr()

        def audio_callback(in_data, frame_count, time_info, status):
            self.ring_buffer.extend(in_data)
            play_data = chr(0) * len(in_data)
            return play_data, pyaudio.paContinue

        vosk.SetLogLevel(-1)
        
        sample_rate = 16000

        self.recognizer = vosk.KaldiRecognizer(vosk.Model(VOSK_MODEL), sample_rate)
        self.ring_buffer = RingBuffer()

        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(
                input=True, output=False,
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                frames_per_buffer=2048,
                stream_callback=audio_callback)


    def start(self):
        print("Starting...")
        while True:
            data = self.ring_buffer.get()
            if self.recognizer.AcceptWaveform(data):               
                r = self.recognizer.Result()
                result = json.loads(r)["text"].lower().strip()

                if KEYWORD.lower() in result:
                    print("Keyword detected")

            sleep(0.1)    

    @staticmethod
    def _ignore_stderr():
        """
        Try to forward PortAudio messages from stderr to /dev/null.
        """
        ffi = _FFI()
        ffi.cdef("""
            /* from stdio.h */
            extern FILE* fopen(const char* path, const char* mode);
            extern int fclose(FILE* fp);
            extern FILE* stderr;  /* GNU C library */
            extern FILE* __stderrp;  /* Mac OS X */
            """)
        stdio = ffi.dlopen(None)
        devnull = stdio.fopen(os.devnull.encode(), b'w')
        try:
            stdio.stderr = devnull
        except KeyError:
            try:
                stdio.__stderrp = devnull
            except KeyError:
                stdio.fclose(devnull)


KEYWORD = "Computer"
#VOSK_MODEL = "vosk-model-small-de-0.15"
VOSK_MODEL = "vosk-model-small-en-us-0.15"

v = VoskTest()
try:
    v.start()
except KeyboardInterrupt:
    pass 

sys.exit()
