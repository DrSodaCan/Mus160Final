from pyo import *

# Initialize the Pyo server
def reverb_test():
    s = Server().boot()
    track = "C:/Users/Atlas/Music/converted_audio.wav"

    snd = SfPlayer(track, speed=1, loop=True)
    rev = Freeverb(snd, size=0.8, damp=0.7, bal=0.5).out()

    # Start the server and run the script
    s.start()
    s.gui(locals())

if __name__ == "__main__":
    reverb_test()


