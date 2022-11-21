#!/usr/bin/python3
# November 2022 Cherry Pit

from lib import LCD_2inch
from os import walk, listdir
from PIL import Image, ImageFont, ImageDraw
from smbus import SMBus
from serial import Serial
from subprocess import Popen, PIPE
from threading import Thread
from time import time, sleep
import RPi.GPIO as GPIO
from random import shuffle, randint
from vlc import MediaListPlayer, Instance


def enter_menu():# this is the enter function
    
    global last_activity_timestamp, screen_asleep, main_current_index, file_list_len, thumbnail_art, path, selected_item, update_render_mp3
    sleep(0.2)
    if screen_asleep == True:
        last_activity_timestamp = int(time())
        screen_asleep = False
        update_render_mp3 = True
        return

    elif selected_item != -1:
#######################################################################################                
        if selected_item[-4:] == '.mp3' or selected_item[-5:] == '.flac' or selected_item[-4:] == '.cda':

            media_player.stop()
            media_player.set_media_list(player.media_list_new())
            media_list = player.media_list_new()

            track_list = [ x for x in file_tree[path] if x[-4:] != '.jpg' ]
            track_list = [ x for x in track_list if x[-4:] == '.mp3' or x[-5:] == '.flac' or x[-4:] == '.cda']
            track_list_len = len(track_list)

            first_track_index = track_list.index(selected_item)
            wrapping_indicies = (list( range( first_track_index , track_list_len) ) + list( range(0 , track_list_len-1) ))[1:track_list_len]
            if shuffle == True and len(wrapping_indicies) > 1:
                shuffle(wrapping_indicies)
            wrapping_indicies.insert(0, first_track_index)

            for index in wrapping_indicies:
                music_file_path = path + '/' + track_list[index]
                if music_file_path[-4:] == '.mp3' or music_file_path[-5:] == '.flac' or music_file_path[-4:] == '.cda':
                    media = player.media_new(music_file_path)
                    media_list.add_media(media)
            media_player.set_media_list(media_list)
            print('playing')
            media_player.play()

            del track_list, track_list_len, first_track_index, wrapping_indicies, index, music_file_path, media, media_list
            
            try:
                with Image.open(path + '/art.jpg') as thumbnail:
                    width, height = thumbnail.size
                    if width != 320 and height != 240:
                        thumbnail_art = thumbnail.resize(320, 240).convert("RGB")
                    else:
                        thumbnail_art = thumbnail.convert("RGB")
                    del thumbnail
            except:
                with Image.open(home_path + '/_bin/default_thumbnail.jpg') as thumbnail:
                    thumbnail_art = thumbnail.convert("RGB")
                del thumbnail

######################################################################################                

        elif '.' not in selected_item[-5:]:
            if selected_item not in path[-path[::-1].find('/')-1:]:
                path = path + '/' + selected_item
                main_current_index = 0
                update_render_mp3 = True
                file_list = file_tree[path]
                file_list_len = len(file_list)

    last_activity_timestamp = int(time())
    screen_asleep = False

def pause_play():# this is the pause/ play function
    sleep(0.2)
    media_player.pause()

def previous():
    sleep(0.2)
    media_player.previous()

def skip():
    sleep(0.2)
    media_player.next()

def random_index():
    sleep(0.2)
    global last_activity_timestamp, screen_asleep, main_current_index
    
    if screen_asleep == True:
        last_activity_timestamp = int(time())
        screen_asleep = False
        update_render_mp3 = True
        return
    
    main_current_index = randint(0,file_list_len)
    update_render_mp3 = True
    last_activity_timestamp = int(time())
    screen_asleep = False

def menu_back():
    
    global last_activity_timestamp, screen_asleep, main_current_index, file_list_len, path, update_render_mp3
    sleep(0.2)
    
    back_path = path[:-path[::-1].find('/')-1]
    if back_path == '/mnt':
        path = home_path
    else:
        path = back_path
    
    main_current_index = 0
    file_list = file_tree[path]
    file_list_len = len(file_list)
    last_activity_timestamp = int(time())
    screen_asleep = False
    update_render_mp3 = True

def enable_vlc_loop():
    sleep(0.2)
    media_player.set_playback_mode(vlc.PlaybackMode.loop)
def disable_vlc_loop():
    sleep(0.2)
    media_player.set_playback_mode(vlc.PlaybackMode.default)
    
def enable_shuffle():
    global shuffle
    shuffle = True
def disable_shuffle():
    global shuffle
    shuffle = False

def runBashCommand(command):
    process = Popen(['/bin/bash', '-c', command], stdout=PIPE)
    output, error = process.communicate()
    return output
    
def show_image(display_image):
    disp.ShowImage(display_image)    
    
def render():
    global selected_item, update_render_mp3, display_image, update_display, selected_item, \
            update_render_eq, display_image, update_display
    
    x_screen_buffer = 15
    y_screen_buffer = 30
    screen_x_res = 320
    screen_y_res = 240    
    distance_between_bars = 10
    y0 = screen_y_res-y_screen_buffer    
    
    while True:
        
        # EQ Rendering
        if update_render_eq:
            mix_levels = '     '.join([str(x) for x in [eq1_value, eq2_value, eq3_value, eq4_value, eq5_value]])
            
            img = eq_img_static.copy()

            ImageDraw.Draw(img).text((28, 100),  # Coordinates
                                     mix_levels,  # Text
                                    'white',  # Color
                                    font=font)
            #sleep(1)
            update_display = True
            update_render_eq = False  
            show_image(img)
            del img
            
        # MP3 Rendering
        elif update_render_mp3:
            
            file_list = file_tree[path]
            file_list_len = len(file_list)
            items_to_display = (list( range(main_current_index, file_list_len) ) + list( range(0, file_list_len )))[:3]

            x_screen_buffer = 8
            y_screen_buffer = 14
            screen_x_res = 320
            screen_y_res = 240

            img = render_static.copy()

            count = 0

            for x in items_to_display[:file_list_len]:

                main_text = file_list[x]

                main_line_x_stary = 5
                main_line_y_start = count*int(240/3)+y_screen_buffer

                if font.getsize(main_text)[0] < screen_x_res - x_screen_buffer*2:
                    ImageDraw.Draw(img).text((x_screen_buffer, main_line_y_start),  # Coordinates
                                            main_text,  # Text
                                            'White',  # Color
                                            font=font)

                    if count == 1:
                        ImageDraw.Draw(img).rectangle([ (0, y_screen_buffer + int(screen_y_res/3) - 10) , (320, y_screen_buffer + int(screen_y_res/3) + 50) ], fill=None, outline='#f54242', width=4)

                else:
                    split_index = len(main_text)
                    while font.getbbox(main_text[:split_index-1])[1] > screen_x_res - x_screen_buffer*2 or main_text[split_index-1] != ' ':
                        split_index -= 1
                        if split_index < 0:
                            split_index = len(main_text) >> 1
                            break

                    ImageDraw.Draw(img).text((x_screen_buffer, main_line_y_start ),  # Coordinates
                                                main_text[:split_index],  # Text
                                                'White',  # Color
                                                font=font)
                    ImageDraw.Draw(img).text((x_screen_buffer, main_line_y_start + 26),  # Coordinates
                                                main_text[split_index:],  # Text
                                                'White',  # Color
                                                font=font)            

                    if count == 1:
                        ImageDraw.Draw(img).rectangle([ (0, y_screen_buffer + int(screen_y_res/3) - 10 ) , (320, y_screen_buffer + int(screen_y_res/3) + 75) ], fill=None, outline='#f54242', width=4)

                count += 1

            if file_list_len > 1:
                selected_item = file_list[items_to_display[1]] # returning the selected item

            elif file_list_len == 1:
                selected_item = file_list[0]
            
            update_render_mp3 = False
            show_image(img)
            del img
            
        sleep(0.02)
    
def read_expansion(i2c_address):    
    p0 = int(b.read_byte_data(i2c_address, 0x01) == 0)
    p1 = int(b.read_byte_data(i2c_address, 0x02) == 0)
    p2 = int(b.read_byte_data(i2c_address, 0x04) == 0)
    p3 = int(b.read_byte_data(i2c_address, 0x08) == 0)
    p4 = int(b.read_byte_data(i2c_address, 0x10) == 0)
    p5 = int(b.read_byte_data(i2c_address, 0x20) == 0)
    p6 = int(b.read_byte_data(i2c_address, 0x40) == 0)
    p7 = int(b.read_byte_data(i2c_address, 0x80) == 0)
    b.write_byte(i2c_address, 0xff)
    return p0,p1,p2,p3,p4,p5,p6,p7

def expansion_1_irq(channel):
    global eq1_1st_status, eq2_1st_status, eq3_1st_status, eq4_1st_status, \
           eq1_2nd_status, eq2_2nd_status, eq3_2nd_status, eq4_2nd_status, \
           eq1_value,       eq2_value,       eq3_value,       eq4_value,   \
           update_render_eq, eq_change_timestamp, set_new_eq_level  
    
    p0,p1,p2,p3,p4,p5,p6,p7 = read_expansion(e1)
    
    if p0 | p1:
        new_status = (p0 << 1) | p1
        if new_status != eq1_2nd_status:
            transition = ( eq1_1st_status << 6 ) | ( eq1_2nd_status << 4 ) | ( new_status << 2)
            if transition == 0b10110100 and eq1_value >= 5: 
                print('down')
                eq1_value = round( ( eq1_value - 5 )/5) * 5
                set_new_eq_level = 1
            elif transition == 0b1111000 and eq1_value <= 95: 
                print('up')
                eq1_value = round( ( eq1_value + 5 )/5) * 5
                set_new_eq_level = 1
            if set_new_eq_level:
                update_render_eq, eq_change_timestamp = 1, time()
            eq1_1st_status = eq1_2nd_status
            eq1_2nd_status = new_status

    if p2 | p3:
        new_status = (p2 << 1) | p3
        if new_status != eq2_2nd_status:
            transition = ( eq2_1st_status << 6 ) | ( eq2_2nd_status << 4 ) | ( new_status << 2)
            if transition == 0b10110100 and eq2_value >= 5:
                print('down')
                eq2_value = round( ( eq2_value - 5 )/5) * 5
                set_new_eq_level = 1
            elif transition == 0b1111000 and eq2_value <= 95:
                print('up')
                eq2_value = round( ( eq2_value + 5 )/5) * 5
                set_new_eq_level = 1
            if set_new_eq_level:
                update_render_eq, eq_change_timestamp = 1, time()
            eq2_1st_status = eq2_2nd_status
            eq2_2nd_status = new_status
            
    if p4 | p5:
        new_status = (p4 << 1) | p5
        if new_status != eq3_2nd_status:
            transition = ( eq3_1st_status << 6 ) | ( eq3_2nd_status << 4 ) | ( new_status << 2)
            if transition == 0b10110100 and eq3_value >= 5:
                print('down')
                eq3_value = round( ( eq3_value - 5 )/5) * 5
                set_new_eq_level = 1
            elif transition == 0b1111000 and eq3_value <= 95:
                print('up')
                eq3_value = round( ( eq3_value + 5 )/5) * 5
                set_new_eq_level = 1
            if set_new_eq_level:
                update_render_eq, eq_change_timestamp = 1, time()
            eq3_1st_status = eq3_2nd_status
            eq3_2nd_status = new_status
            
    if p6 | p7:
        new_status = (p6 << 1) | p7
        if new_status != eq4_2nd_status:
            transition = ( eq4_1st_status << 6 ) | ( eq4_2nd_status << 4 ) | ( new_status << 2)
            if transition == 0b10110100 and eq4_value >= 5:
                print('down')
                eq4_value = round( ( eq4_value - 5 )/5) * 5
                set_new_eq_level = 1
            elif transition == 0b1111000 and eq4_value <= 95:
                print('up')
                eq4_value = round( ( eq4_value + 5 )/5) * 5
                set_new_eq_level = 1
            if set_new_eq_level:
                update_render_eq, eq_change_timestamp = 1, time()
            eq4_1st_status = eq4_2nd_status
            eq4_2nd_status = new_status
    
def expansion_2_irq(channel):
    global e2, shuffle, loop, eq5_last_status, eq5_value, bluetooth_mode, screen_asleep, last_activity_timestamp, set_new_eq_level, screen_asleep, last_activity_timestamp, set_new_eq_level, update_render_eq, eq_change_timestamp,\
            eq5_value, eq5_1st_status, eq5_2nd_status

    p0,p1,p2,p3,p4,p5,p6,p7 = read_expansion(e2)
        
    if p0 | p1:
        new_status = (p0 << 1) | p1
        if new_status != eq5_2nd_status:
            transition = ( eq5_1st_status << 6 ) | ( eq5_2nd_status << 4 ) | ( new_status << 2)
            if transition == 0b10110100 and eq5_value >= 5:
                print('down')
                eq5_value = round( ( eq5_value - 5 )/5) * 5
                set_new_eq_level = 1
            elif transition == 0b1111000 and eq5_value <= 95:
                print('up')
                eq5_value = round( ( eq5_value + 5 )/5) * 5
                set_new_eq_level = 1
            if set_new_eq_level:
                update_render_eq, eq_change_timestamp = 1, time()
            eq5_1st_status = eq5_2nd_status
            eq5_2nd_status = new_status
    
    if bluetooth_mode == False:

        if p2:
            skip()
        elif p3: 
            print('play')
            pause_play()
        elif p4:
            previous()
        elif p7:
            random_index()

        # checking toggles
        if p5 == 0 and shuffle == True:
            shuffle = False
        elif p5 == 1 and shuffle == False:
            shuffle = True

        if p6 == 0 and loop == True:
            loop = False
        elif p6 == 1 and loop == False:
            loop = True
    
def expansion_3_irq(channel):
    global e3, selector_last_status, main_current_index, bluetooth_mode, selected_item, file_list, file_list_len, screen_asleep, last_activity_timestamp, update_render_mp3
    
    if bluetooth_mode == False:
    
        p0,p1,p2,p3,p4,p5,p6,p7 = read_expansion(e3)
        
        if p0 | p1:
            display_new_selection = 0

            new_status = (p0 << 1) | p1
            if new_status != selector_last_status:
                transition = (selector_last_status << 2) | new_status
                if transition == 0b1110:
                    main_current_index -= 1
                    display_new_selection = 1
                elif transition == 0b1101:
                    main_current_index += 1
                    display_new_selection = 1
                if display_new_selection:
                    if main_current_index < 0:
                        main_current_index = file_list_len - 2
                    elif main_current_index >= file_list_len - 1:
                        main_current_index = 0
                    update_render_mp3, last_activity_timestamp, screen_asleep = 1, time(), 0          
                selector_last_status = new_status            
            
        if p2:
            menu_back()
        elif p3:
            print('enter')
            enter_menu()
        
def read_and_set_volume():
    global ser
    
    ser.write(b'1')
    sleep(0.1)
    # reading the serial port
    volume = b''
    while ser.inWaiting() != 0:
        volume += ser.read()              #read serial port
    volume = -1 if len(volume) == 0 else int(volume.decode("utf-8"))
    volume = -1 if volume > 100 else volume
    
    return volume

def set_eq_levels():
    
    global eq1_value, eq2_value, eq3_value, eq4_value, eq5_value
        
    runBashCommand(f"amixer -D equal -q set '00. 31 Hz' {eq1_value}%,{eq1_value}%")
    runBashCommand(f"amixer -D equal -q set '01. 63 Hz' {eq1_value}%,{eq1_value}%")

    runBashCommand(f"amixer -D equal -q set '02. 125 Hz' {eq2_value}%,{eq2_value}%")
    runBashCommand(f"amixer -D equal -q set '03. 250 Hz' {eq2_value}%,{eq2_value}%")

    runBashCommand(f"amixer -D equal -q set '04. 500 Hz' {eq3_value}%,{eq3_value}%")
    runBashCommand(f"amixer -D equal -q set '05. 1 kHz' {eq3_value}%,{eq3_value}%")

    runBashCommand(f"amixer -D equal -q set '06. 2 kHz' {eq4_value}%,{eq4_value}%")
    runBashCommand(f"amixer -D equal -q set '07. 4 kHz' {eq4_value}%,{eq4_value}%")

    runBashCommand(f"amixer -D equal -q set '08. 8 kHz' {eq5_value}%,{eq5_value}%")
    runBashCommand(f"amixer -D equal -q set '09. 16 kHz' {eq5_value}%,{eq5_value}%")

###############################
####### Boot Sequence #########
###############################

runBashCommand('sudo mount /dev/sda1 /mnt/volume')
runBashCommand(f'sudo chmod -R 777 /mnt/volume')

home_path = '/mnt/volume'
    

if '_bin' not in listdir(home_path):  
    runBashCommand(f'sudo mkdir {home_path}/_bin')
    runBashCommand(f'sudo chmod -R 777 {home_path}/_bin')
    
    runBashCommand(f'sudo cp _bin/default_thumbnail.jpg {home_path}/_bin/default_thumbnail.jpg')
    runBashCommand(f'sudo cp _bin/blutooth_thumbnail.jpg {home_path}/_bin/blutooth_thumbnail.jpg')
    runBashCommand(f'sudo cp _bin/readme.txt {home_path}/_bin/readme.txt')
    
else:
    _bin_files = listdir(home_path + '/_bin')    
    if 'default_thumbnail.jpg' not in _bin_files:
        runBashCommand(f'sudo cp _bin/default_thumbnail.jpg {home_path}/_bin/default_thumbnail.jpg')
    if 'blutooth_thumbnail.jpg' not in _bin_files:
        runBashCommand(f'sudo cp _bin/blutooth_thumbnail.jpg {home_path}/_bin/blutooth_thumbnail.jpg')
    if 'readme.txt' not in _bin_files:
        runBashCommand(f'sudo cp _bin/readme.txt {home_path}/_bin/readme.txt')
    del _bin_files

file_tree = {}
for root, dirs, files in walk(home_path):
    if root == home_path:
        dirs.remove('_bin')
        try:
            dirs.remove('System Volume Information')
        except:
            pass
        dirs.insert(0,'')
        file_tree[root] = dirs
    else:
        files.insert(0,'')
        file_tree[root] = [x for x in files if x[-4:] != '.jpg']
del root, dirs, files

# preparing the display
# setting up the black background
black_screen = Image.new("RGB", (320,240), "Black")
render_static = black_screen.copy()   
update_display = True
screen_busy = False
update_render_eq = False
set_new_eq_level = False
update_render_mp3 = False

disp = LCD_2inch.LCD_2inch()
disp.Init()
disp.clear()
show_image(black_screen)

RenderThread = Thread(target=render)
RenderThread.start()

# opening the serial port to get the volume value from the raspi pico
ser = Serial("/dev/ttyAMA0", 9600)    #Open port with baud rate

# setting up a static image for the eq
font = ImageFont.truetype('/home/pi/hipi/_bin/MADEAvenuePERSONALUSE-Regular.otf', 25)
small_font = ImageFont.truetype('/home/pi/hipi/_bin/MADEAvenuePERSONALUSE-Regular.otf', 20)

eq_img_static = black_screen.copy()
ImageDraw.Draw(eq_img_static).text((95, 1),  # Coordinates
                        'HiPi Equalizer',  # Text
                        'white',  # Color
                        font=font)
ImageDraw.Draw(eq_img_static).text((243, 214),  # Coordinates
                        'Trebble',  # Text
                        'white',  # Color
                        font=small_font)
ImageDraw.Draw(eq_img_static).text((15, 214),  # Coordinates
                        'Bass',  # Text
                        'white',  # Color
                        font=small_font)
ImageDraw.Draw(eq_img_static).line( [0, 211, 320, 211], fill='white', width=3)
ImageDraw.Draw(eq_img_static).line( [0, 30, 320, 30], fill='white', width=2)

with Image.open(home_path + '/_bin/default_thumbnail.jpg') as thumbnail:
    thumbnail_art = thumbnail.convert("RGB")     #.convert("RGB")     

with Image.open(home_path + '/_bin/blutooth_thumbnail.jpg') as thumbnail:
    bluetooth_art = thumbnail.convert("RGB")     #.convert("RGB")    

# Setting up GPIO
expansion_1_interrupt_pin = 11
expansion_2_interrupt_pin = 13
expansion_3_interrupt_pin = 12
fully_initialized_led_pin = 15 # this is set high to tell the raspi pico to stop pulsing the LED
function_toggle = 16 # determine if in bluetooth or mp3 mode
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
# setting up gpio interrrupts
GPIO.setup(expansion_1_interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 
GPIO.setup(expansion_2_interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) #
GPIO.setup(expansion_3_interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 
GPIO.setup(fully_initialized_led_pin, GPIO.OUT) # 
GPIO.setup(function_toggle, GPIO.IN, pull_up_down=GPIO.PUD_UP) # 

# getting the eq levels
eq1_value = runBashCommand("amixer -D equal sget '00. 31 Hz' ").decode("utf-8")[-15:]
percent_index = eq1_value.find('%')
eq1_value = round( int(eq1_value[percent_index-3: percent_index].replace('[',''))   /5 ) * 5
eq2_value = runBashCommand("amixer -D equal sget '02. 125 Hz' ").decode("utf-8")[-15:]
percent_index = eq2_value.find('%')
eq2_value = round( int(eq2_value[percent_index-3: percent_index].replace('[',''))   /5 ) * 5
eq3_value = runBashCommand("amixer -D equal sget '04. 500 Hz' ").decode("utf-8")[-15:]
percent_index = eq3_value.find('%')
eq3_value = round( int(eq3_value[percent_index-3: percent_index].replace('[',''))   /5 ) * 5
eq4_value = runBashCommand("amixer -D equal sget '06. 2 kHz' ").decode("utf-8")[-15:]
percent_index = eq4_value.find('%')
eq4_value = round( int(eq4_value[percent_index-3: percent_index].replace('[',''))   /5 ) * 5
eq5_value = runBashCommand("amixer -D equal sget '08. 8 kHz' ").decode("utf-8")[-15:]
percent_index = eq5_value.find('%')
eq5_value = round( int(eq5_value[percent_index-3: percent_index].replace('[',''))   /5 ) * 5

set_volume = runBashCommand("amixer -c 1 sget Speaker Playback Volume").decode("utf-8")[-25:]
percent_index = set_volume.find('%')
set_volume = round( int(set_volume[percent_index-3: percent_index].replace('[',''))   /5 ) * 5
del percent_index

# i2c address of the idfferent PCF8574
e1=0x24
e2=0x20
e3=0x23
# open the bus (0 -- original Pi, 1 -- Rev 2 Pi)
b = SMBus(1)
# make certain the pins are set high so they can be used as inputs
b.write_byte(e1, 0xff)
b.write_byte(e2, 0xff)
b.write_byte(e3, 0xff)

# setting the original values for the rotary encoders
p0,p1,p2,p3,p4,p5,p6,p7 = read_expansion(e3)
shuffle = p5
loop = p6

selector_last_status = 0
eq1_1st_status, eq2_1st_status, eq3_1st_status, eq4_1st_status, eq5_1st_status = 0,0,0,0,0
eq1_2nd_status, eq2_2nd_status, eq3_2nd_status, eq4_2nd_status, eq5_2nd_status = 0,0,0,0,0

del p0,p1,p2,p3,p4,p5,p6,p7

# creating a media player object
media_player = MediaListPlayer()
# creating Instance class object
player = Instance()         

runBashCommand('echo "power off \nquit" | bluetoothctl')

bluetooth_mode = False
last_activity_timestamp = int(time())
eq_change_timestamp = -1
last_media_player_is_playing = 0

#######################################################
############# finished boot sequence #################
######################################################

GPIO.add_event_detect(expansion_1_interrupt_pin, GPIO.FALLING, callback=expansion_1_irq)
GPIO.add_event_detect(expansion_2_interrupt_pin, GPIO.FALLING, callback=expansion_2_irq)
GPIO.add_event_detect(expansion_3_interrupt_pin, GPIO.FALLING, callback=expansion_3_irq)

# set loading led pin high to stop it from pulsing
GPIO.output(fully_initialized_led_pin, 1)
print('ready')
while True:
    
    if GPIO.input(function_toggle) == GPIO.LOW:
        print('bt mode')
        bluetooth_mode = True
        show_image(bluetooth_art)
        runBashCommand('echo "power on \nquit" | bluetoothctl')
        while GPIO.input(function_toggle) == GPIO.LOW:    # if true bluetooth mode on
            
            volume = read_and_set_volume()
            if ( abs(set_volume - volume) > 2 and volume != -1) or ( volume == 0 and set_volume != 0 ):
                runBashCommand(f"amixer -c 1 sset Speaker Playback Volume {volume}%,{volume}%")
                set_volume = volume
            
            if set_new_eq_level == 1 and update_render_mp3 == 0 and time() - eq_change_timestamp > 3:
                set_eq_levels()
                show_image(bluetooth_art)
                screen_asleep = True
                set_new_eq_level = 0
            
            sleep(0.25)
            
        show_image(thumbnail_art)
        runBashCommand('echo "power off \nquit" | bluetoothctl')  

    else:

        bluetooth_mode = False
        screen_asleep = False
        update_render_mp3 = True
        
        path = home_path
        file_list = file_tree[path]
        file_list_len = len(file_list)           
        
        main_current_index = 0

        # start loop
        print('mp3 mode')
        while GPIO.input(function_toggle) == GPIO.HIGH:

            volume = read_and_set_volume()
            if ( abs(set_volume - volume) > 2 and volume != -1) or ( volume == 0 and set_volume != 0 ):
                runBashCommand(f"amixer -c 1 sset Speaker Playback Volume {volume}%,{volume}%") 
                set_volume = volume
                print(set_volume)
                
            if set_new_eq_level == 1 and update_render_mp3 == 0 and time() - eq_change_timestamp > 3:
                set_eq_levels()
                show_image(thumbnail_art)
                screen_asleep = True
                set_new_eq_level = 0
            
            if time() - last_activity_timestamp  > 10 and screen_asleep == False: # time in seconds to put the display to sleep
                show_image(thumbnail_art)
                screen_asleep = True
                
            if media_player.is_playing() == 0 and last_media_player_is_playing == 1:
                with Image.open(home_path + '/_bin/default_thumbnail.jpg') as thumbnail:
                    thumbnail_art = thumbnail.convert("RGB")     #.convert("RGB")   
                    show_image(thumbnail_art)
                    last_media_player_is_playing = 0
            
            last_media_player_is_playing = media_player.is_playing()

            sleep(0.25)
            
        # close loop
        media_player.stop()
