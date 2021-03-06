Readme

# Installation of dump1090

There are 2 variants I have seen. 
- Malcolm Robb's [repo](https://github.com/MalcolmRobb/dump1090)
- Antirez's [repo](https://github.com/antirez/dump1090)

Once obtained and if running on a Linux platform or Raspberry pi, open your /etc/rc.local file and type:

`/home/pi/dump1090/dump1090 --aggressive --interactive --net --net-sbs-port 30003 &`

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



