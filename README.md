Readme

# Installation of rtl-sdr

You can obtain the latest repo commit from:

git clone git://git.osmocom.org/rtl-sdr.git

and navigate to https://osmocom.org/projects/rtl-sdr/wiki

When building rtl-sdr I had some problems running the rtl_test executable
located in the build/src directory of the rtl-sdr repo. I think this resulted
from needing to copy the rtl-sdr.rules file to the /etc/udev/rules.d directory
and then rebooting

Another thing I did (which may or may not have helped) was blacklisted native 
Raspbian kernels for the rtl-sdr dongle. To help with this problem, I created
a file called /etc/modprobe.d/rtl-sdr.conf and added the lines
- blacklist dvb_usb_rtl28xxu
- blacklist rtl2832
- blacklist rtl2830
- blacklist rtl2838

(The rtl2838 is the model I currently have)

After doing these steps (and rebooting the RPi appropriately) everything worked

# Installation of dump1090

There are 2 variants I have seen. 
- Malcolm Robb's [repo](https://github.com/MalcolmRobb/dump1090)
- Antirez's [repo](https://github.com/antirez/dump1090)

Once obtained and if running on a Linux platform or Raspberry pi, open your /etc/rc.local file and type:

`/path/to/dump1090 --aggressive --interactive --net --net-sbs-port 30003 &`

This will assure it runs on startup

An explanation of the flags and ports chosen can be found on Malcolm Robb's dump1090 github repo: 

# Using curseXcel

One can do two things to install this code
- Run `pip install curseXcel` and it will install it automatically
If, however, you want to install your local copy (from a github repo for example), then navigate to the cloned repo and run:
- `pip install -e ./`

# Running ADS-B Analysis Code

Once dump1090 is collecting ADS-B data, in my repo, go into the `python_scripts` directory and open the script `client_adsb_analysis.py`. There, one will likely have to modify the:
- `os.environ` path 
- `QTH_LAT`, `QTH_LON` (these are your home coordinates)
- For me I have the coordinates of Logan airport in Boston, MA, and Manchester airport in Manchester, NH. For anyone else, you can choose your own local airports and load in their coordinates.

Once your happy with your changes, you should be able to run:

`python client_adsb_analysis.py` and the script should kickoff



