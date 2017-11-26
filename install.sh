#/bin/bash
printf "\e[92mInstalling dependencies...\e[39m\n"
sudo apt-get -y update
sudo apt-get -y install git python-pip python-setuptools
sudo easy_install -U pip

printf "\e[92mInstalling super-pi-cheerlights...\e[39m\n"
printf "\e[92mCloning super-pi-cheerlights...\e[39m\n"
git clone https://github.com/Tugzrida/super-pi-cheerlights.git /home/pi/super-pi-cheerlights/
chmod +x /home/pi/super-pi-cheerlights/super-pi-cheerlights.py /home/pi/super-pi-cheerlights/getsun.py /home/pi/super-pi-cheerlights/list_tz.py

printf "\e[92mDownloading web dependencies...\e[39m\n"
mkdir /home/pi/super-pi-cheerlights/www/spectrum
wget "https://github.com/bgrins/spectrum/archive/1.8.0.zip" -O /home/pi/super-pi-cheerlights/www/spectrum/spectrum.zip &> /dev/null
unzip /home/pi/super-pi-cheerlights/www/spectrum/spectrum.zip -d /home/pi/super-pi-cheerlights/www/spectrum/ &> /dev/null
mv /home/pi/super-pi-cheerlights/www/spectrum/spectrum-1.8.0/spectrum.js /home/pi/super-pi-cheerlights/www/spectrum/
mv /home/pi/super-pi-cheerlights/www/spectrum/spectrum-1.8.0/spectrum.css /home/pi/super-pi-cheerlights/www/spectrum/
rm -r /home/pi/super-pi-cheerlights/www/spectrum/spectrum-1.8.0/ /home/pi/super-pi-cheerlights/www/spectrum/spectrum.zip 

mkdir /home/pi/super-pi-cheerlights/www/bootstrap-slider
wget "https://github.com/seiyria/bootstrap-slider/archive/v10.0.0.zip" -O /home/pi/super-pi-cheerlights/www/bootstrap-slider/bootstrap-slider.zip &> /dev/null
unzip /home/pi/super-pi-cheerlights/www/bootstrap-slider/bootstrap-slider.zip -d /home/pi/super-pi-cheerlights/www/bootstrap-slider/ &> /dev/null
mv /home/pi/super-pi-cheerlights/www/bootstrap-slider/bootstrap-slider-10.0.0/dist/bootstrap-slider.min.js /home/pi/super-pi-cheerlights/www/bootstrap-slider/
mv /home/pi/super-pi-cheerlights/www/bootstrap-slider/bootstrap-slider-10.0.0/dist/css/bootstrap-slider.min.css /home/pi/super-pi-cheerlights/www/bootstrap-slider/
rm -r /home/pi/super-pi-cheerlights/www/bootstrap-slider/bootstrap-slider-10.0.0/ /home/pi/super-pi-cheerlights/www/bootstrap-slider/bootstrap-slider.zip

wget "https://code.jquery.com/jquery-3.2.1.min.js" -O /home/pi/super-pi-cheerlights/www/jquery.min.js &> /dev/null

mkdir /home/pi/super-pi-cheerlights/www/bootstrap
wget "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" -O /home/pi/super-pi-cheerlights/www/bootstrap/bootstrap.min.css &> /dev/null
wget "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" -O /home/pi/super-pi-cheerlights/www/bootstrap/bootstrap.min.js &> /dev/null


printf "\e[92mInstalling python dependencies...\e[39m\n"
sudo pip install bottle python-dateutil pytz requests

printf "\e[92mDone! Now follow the setup info at https://github.com/Tugzrida/super-pi-cheerlights#sun-times-schedule-setup\e[39m\n"
