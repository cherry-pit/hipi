# sudo apt-get install -y xinetd tftpd tftp
# chmod +x /home/pi/hipi/megainstall2.sh && /home/pi/hipi/megainstall2.sh && rm /home/pi/hipi/megainstall2.sh
################################################################
################################################################
################################# Setup


mkdir /home/pi/hipi/_bin
mkdir /home/pi/hipi/lib
mkdir /home/pi/hipi/scripts

7z e _bin.7z -o/home/pi/hipi/_bin
7z e lib.7z -o/home/pi/hipi/lib

rm -r _bin.7z
rm -r lib.7z

chmod +x /home/pi/hipi/hipi.py

sudo mkdir /mnt/volume && sudo chmod 770 /mnt/volume

sudo apt-get update && sudo apt-get upgrade

wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.71.tar.gz && tar zxvf bcm2835-1.71.tar.gz && cd bcm2835-1.71/ && sudo ./configure && sudo make && sudo make check && sudo make install && cd .. && wget https://project-downloads.drogon.net/wiringpi-latest.deb && sudo dpkg -i wiringpi-latest.deb && cd && rm -r bcm2835-1.71.tar.gz && rm -r wiringpi-latest.deb

sudo apt-get install -y i2c-tools
sudo apt-get install -y python3-serial
sudo apt-get install -y python3-pip
sudo apt-get install -y python3-pil
sudo apt-get install -y python3-numpy
sudo apt-get install -y python3-smbus
sudo apt-get install -y RPi.GPIO
sudo apt-get install -y vlc
sudo pip3 install RPi.GPIO spidev python-vlc
sudo apt-get install pulseaudio


####################################################################
####################################################################
############################ BLUETOOTH


# prepare the environment
sudo apt install -y bluez-alsa-utils


#### Bluetooth A2DP sink using bluealsa

# This is based on using the built-in Pi 3 bluetooth radio, but networking with 
# ethernet ONLY, so that the internal wifi radio is disabled and can't interfere

# Pi OS 11 'Bullseye' Lite includes bluetooth and bthelper@hci0 services only

# bluealsa not present in Pi bullseye repos - get it from 'Bookworm Raspbian'
# credit https://www.sigmdel.ca/michel/ha/rpi/bluetooth_in_rpios_02_en.html#bluealsa3
echo "deb http://archive.raspbian.org/raspbian/ bookworm main" | sudo tee /etc/apt/sources.list.d/armbian.list
printf 'Package: *\nPin: release n=bookworm\nPin-Priority: 100\n' | sudo tee --append /etc/apt/preferences.d/limit-bookworm
sudo apt update
sudo apt install -y bluez-alsa-utils


##### options for newly-installed bluez-alsa.service

sudo tee /etc/default/bluez-alsa <<EOF!
# Config file for blues-alsa.service - set the service runtime options
# credit https://www.sigmdel.ca/michel/ha/rpi/bluetooth_in_rpios_02_en.html#bluealsa3
#OPTIONS="-p a2dp-source -p a2dp-sink"
# but we only need the sink
OPTIONS="--profile=a2dp-sink"
# although using a USB Bluetooth radio you might need "--device=hciX"
# help - https://github.com/Arkq/bluez-alsa/blob/master/doc/bluealsa.8.rst
EOF!
sudo systemctl restart bluez-alsa.service
sudo systemctl status bluez-alsa.service


# These sections are derived from 
# https://github.com/artmg/rpi-audio-receiver/blob/master/install-bluetooth.sh
# but original credit to https://github.com/nicokaiser/rpi-audio-receiver


##### bluealsa-aplay.service starts after bluez-alsa to pass A2DP to Alsa device

sudo tee /etc/systemd/system/bluealsa-aplay.service <<EOF!
[Unit]
Description=BlueALSA player
Requires=bluez-alsa.service
After=bluez-alsa.service
Wants=bluetooth.target sound.target
[Service]
Type=simple
User=pi
ExecStartPre=/bin/sleep 2 
# ExecStart=/usr/bin/bluealsa-aplay --pcm=default --pcm-buffer-time=250000 00:00:00:00:00:00
ExecStart=/usr/bin/bluealsa-aplay -D equal --pcm-buffer-time=250000 00:00:00:00:00:00
# help - https://github.com/Arkq/bluez-alsa/blob/master/doc/bluealsa-aplay.1.rst
[Install]
WantedBy=graphical.target
EOF!

##### udev rule restarts the A2DP player when a device connects to bluetooth

sudo tee /etc/udev/rules.d/61-bluealsa-aplay.rules <<EOF!
# syntax generated by connecting to bluetooth whilst using 
#udevadm monitor --environment --udev --kernel
ACTION=="add", SUBSYSTEM=="bluetooth", RUN+="/bin/systemctl restart bluealsa-aplay.service"
EOF!
# not bothered with udev script for connect/disconnect sounds from original


##### Bluetooth settings

sudo tee /etc/bluetooth/main.conf <<EOF!
[General]
# With bluetooth Class of Device (CoD), the Service Class (>0x2000) might be ignored
#Class = 0x200414
# Major device class: Audio/Video; Minor device class: Hifi audio device;
#Class = 0x0428
# Major device class: Audio/Video; Minor device class: Loudspeaker;
Class = 0x0414
DiscoverableTimeout = 0
[Policy]
AutoEnable=true
EOF!

sudo service bluetooth restart
sudo hciconfig hci0 piscan
sudo hciconfig hci0 sspmode 1

##### ALSA settings

sudo sed -i.orig 's/^options snd-usb-audio index=-2$/#options snd-usb-audio index=-2/' /lib/modprobe.d/aliases.conf


##### Bluetooth open pairing agent

# use modified version of BlueZ 'simple agent' python test script
wget https://raw.githubusercontent.com/bluez/bluez/master/test/simple-agent
# credit - https://github.com/RPi-Distro/repo/issues/291#issuecomment-1149427137
sed -i.orig 's/capability = "KeyboardDisplay"/capability = "NoInputNoOutput"/' simple-agent
sed -i.orig 's/return raw_input(prompt)/return "yes"/' simple-agent
sudo cp simple-agent /usr/local/bin/bluetooth-open-pairing
sudo chmod 755 /usr/local/bin/bluetooth-open-pairing
# and required library script
wget https://raw.githubusercontent.com/bluez/bluez/master/test/bluezutils.py
sudo cp bluezutils.py /usr/local/bin/
sudo chmod 755 /usr/local/bin/bluezutils.py
# I chose this script as it comes from the Bluez project itself. 
# If it ever changes and you can't make it work, consider a simpler derivative like 
# https://gist.github.com/mill1000/74c7473ee3b4a5b13f6325e9994ff84c#file-a2dp-agent

sudo tee /etc/systemd/system/bluetooth-open-pairing.service <<EOF!
# runs a modified copy of bluez simple-agent to silently allow all pairing requests
[Unit]
Description=Bluetooth open pairing agent
Requires=bluetooth.service
After=bluetooth.service
[Install]
WantedBy=bluetooth.target
[Service]
Type=simple
ExecStartPre=/bin/hciconfig hci0 piscan
ExecStartPre=/bin/hciconfig hci0 sspmode 1
ExecStart=/usr/local/bin/bluetooth-open-pairing
Restart=always
RestartSec=10
EOF!

# install pairing agent script dependencies 
sudo apt install -y python3-gi python3-dbus

# now let's run it all
sudo systemctl daemon-reload
sudo systemctl enable --now bluealsa-aplay
sudo systemctl enable --now bluetooth-open-pairing.service

# Now you should be able to pair with your Pi and send sound 
# that you can hear when you plug into the internal headphone jack

###############################################################################
###############################################################################
############################## Equalizer

sudo apt-get install -y libasound2-plugin-equal

sudo tee /home/pi/.asoundrc <<EOF!
ctl.equal {
    type equal;
}

pcm.plugequal {
    type equal;
    # Normally, the equalizer feeds into dmix so that audio
    # from multiple applications can be played simultaneously:
    # slave.pcm "plug:dmix";
    # If you want to feed directly into a device, specify it instead of dmix:
    slave.pcm "plughw:1,0";
}

# Configuring pcm.!default will make the equalizer your default sink
#pcm.!default {
# If you do not want the equalizer to be your default,
# give it a different name, like pcm.equal commented below
# Then you can choose it as the output device by addressing
# it in individual apps, for example mpg123 -a equal 06.Back_In_Black.mp3
pcm.equal {
    type plug;
    slave.pcm plugequal;
}
EOF!


###############################################################################
###############################################################################
############################## Closing


# configure the raspberry pi
sudo raspi-config nonint do_hostname hipi
sudo raspi-config nonint do_serial 2
sudo raspi-config nonint do_i2c 1
sudo raspi-config nonint do_spi 1
sudo raspi-config nonint do_memory_split 32
cat /boot/cmdline.txt