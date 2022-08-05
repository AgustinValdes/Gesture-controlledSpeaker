import board
import busio
import audiomp3
import audioio
import digitalio
import displayio
import time
from analogio import AnalogIn
from analogio import AnalogOut
from digitalio import DigitalInOut
import neopixel
from math import log
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spiimport adafruit_requests as requests
from adafruit_st7735r import ST7735R
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.circle import Circle
from adafruit_display_shapes.triangle import Triangle
from adafruit_display_shapes.roundrect import RoundRect
import terminalio
from adafruit_display_text.label import Label
#set up the screen:
#spi = board.SPI()
tft_cs = board.D5
tft_dc = board.D6
displayio.release_displays()
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

display_bus = displayio.FourWire(spi, command=tft_dc, chip_select=tft_cs, reset=board.D7)
display = ST7735R(display_bus, width=128, height=160, colstart=0, rowstart=0)
scene = displayio.Group(max_size=10)
display.show(scene)
SCREEN_WIDTH = 127
SCREEN_HEIGHT = 159
#Test Buttons Set-Up
switchBack = digitalio.DigitalInOut(board.D8)
switchPlayPause = digitalio.DigitalInOut(board.D9)
switchVup = digitalio.DigitalInOut(board.D10)
switchVdown = digitalio.DigitalInOut(board.D11)
switchSkip = digitalio.DigitalInOut(board.D12)

switchBack.switch_to_input(pull=digitalio.Pull.UP)
switchPlayPause.switch_to_input(pull=digitalio.Pull.UP)
switchVup.switch_to_input(pull=digitalio.Pull.UP)
switchVdown.switch_to_input(pull=digitalio.Pull.UP)
switchSkip.switch_to_input(pull=digitalio.Pull.UP)

#U/D
volume_toggle = digitalio.DigitalInOut(board.D3)
volume_toggle.switch_to_output()

#INC
volume_increment = digitalio.DigitalInOut(board.D4)
volume_increment.switch_to_output()
#CS
volume_store = digitalio.DigitalInOut(board.D2)
volume_store.switch_to_output()

#Volume Control
volume_fill = 20
volume_pos = 15
volume_bar = RoundRect(15, 0, 100, int(SCREEN_HEIGHT/20), 5, fill=0xFFFFFF)
volume_status = RoundRect(volume_pos, 0 , volume_fill, int(SCREEN_HEIGHT/20), 5, fill=0x00FF00)

#Pause/Play/Skip UI
ui_playpause = Circle(64, 130, 15, fill=0xFFFFFF)
ui_back = Circle(32, 130, 15, fill=0x00FF00)
ui_next = Circle(96, 130, 15, fill=0x00FF00)
ui_thumbnail = RoundRect(24,25, 80, 80, 10, fill=0xFFFFFF)
image_next = Triangle(90,120, 90, 140, 107, 130, fill = 0x000000)
image_back = Triangle(39, 120, 39, 140, 22, 130, fill = 0x000000)
#Append Assets
scene.append(volume_bar)
scene.append(ui_playpause)
scene.append(ui_back)
scene.append(ui_next)
scene.append(ui_thumbnail)
scene.append(image_next)
scene.append(image_back)
scene.append(volume_status)
#Speaker and playlist step-up
i = 0
state = 0
play_pause_state = 0 #0 is playing and 1 is paused
speaker = audioio.AudioOut(board.A0)
playlist = ("AllStar.mp3", "CarelessWhisper.mp3", "DejaVu.mp3", "Halo.mp3", "RickAstley.mp3")
open_song = open(playlist[i], "rb")
print(playlist[i])
current_song = audiomp3.MP3Decoder(open_song)
speaker.play(current_song)


#internet stuff
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
requests.set_socket(socket, esp)

from secrets import secrets

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Connecting to AP...")

while not esp.is_connected:
    try:
        esp.connect_AP(secrets["ssid"], secrets["password"])
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
while True:
    if state == 0: #Waiting area
        volume_store.value = 0
        volume_toggle.value = 0
        volume_increment.value = 1
        speaker.play(current_song)
        state = 1
    if state == 1: #Active area
        while speaker.playing or not speaker.playing:
            try:
                r = requests.get("http://608dev.net/sandbox/mostec/speaker?gesture")
                gestureDict = eval(r.text)
                code = gestureDict['gesture']
                print(code)
                if not switchSkip.value == 1 or code == "skip song":
                    if i>4:
                        i = 0
                    elif i<0:
                        i = 4
                    else:
                        i += 1
                    open_song = open(playlist[i], "rb")
                    current_song = audiomp3.MP3Decoder(open_song)
                    speaker.play(current_song)
                    state = 0
                elif not switchBack.value == 1 or code == "back song":
                    if i>4:
                        i = 0
                    elif i<0:
                        i = 4
                    else:
                        i -= 1
                    open_song = open(playlist[i], "rb")
                    current_song = audiomp3.MP3Decoder(open_song)
                    speaker.play(current_song)
                    state = 0






                elif not switchVup.value == 1:
                    print("received")
                    if volume_fill >= 100:
                        volume_fill = 100
                        state = 0
                    else:
                        volume_fill += 4
                        scene.pop(7)
                        scene.append(volume_status)
                        scene[7] = RoundRect(volume_pos, 0 , volume_fill, int(SCREEN_HEIGHT/20), 5, fill=0x00FF00)
                        #Increment
                        volume_store.value = 0
                        volume_toggle.value = 1
                        volume_increment.value = 0
                        #Store it
                        volume_store.value = 1
                        volume_increment.value = 1
                        #temporary reset
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 1

                        #increment
                        volume_store.value = 0
                        volume_toggle.value = 1
                        volume_increment.value = 0
                        #Store it
                        volume_store.value = 1
                        volume_increment.value = 1
                        #temporary reset
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 1
                        #increment
                        volume_store.value = 0
                        volume_toggle.value = 1
                        volume_increment.value = 0
                        #Store it
                        volume_store.value = 1
                        volume_increment.value = 1
                        state = 0
                elif not switchVdown.value == 1 or code == "volume down":
                    if volume_fill <= 10:
                        volume_fill = 10
                        state = 0
                    else:
                        volume_fill -= 4
                        scene.pop(7)
                        scene.append(volume_status)
                        scene[7] = RoundRect(volume_pos, 0 , volume_fill, int(SCREEN_HEIGHT/20), 5, fill=0x00FF00)
                        #Decrement
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 0
                        #Store it
                        volume_store.value = 1
                        volume_increment.value = 1
                        #temporary reset
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 1
                        #Decrement
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 0
                        #Store it
                        volume_store.value = 1
                        volume_increment.value = 1
                        #temporary reset
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 1
                        #Decrement
                        volume_store.value = 0
                        volume_toggle.value = 0
                        volume_increment.value = 0
                        #Store it
                        volume_store.value = 1
                        volume_increment.value = 1
                        state = 0
                elif not switchPlayPause.value == 1 or code == "play/pause":
                    if play_pause_state == 0: #if it was already playing
                        speaker.pause()
                        play_pause_state = 1 #change state to paused
                        state = 1
                        #Go back to active state
                    elif play_pause_state == 1: #if it was already paused
                        speaker.resume()
                        play_pause_state = 0 #change state to playing
                        #Go back to active state
                        state =1
                elif code == "no gesture":
                    state = 0
            except Exception as e:
                print(e)
            time.sleep(0.02)