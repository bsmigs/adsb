HOST                = "192.168.1.58" # RPi IP address
PORT                = 30003 # dump1090 port we are listening to
BUFFER_SIZE         = 1024 # make it nice and big

# define/initialize plots for animation
myLowerLon          = -74.5
myLowerLat          = 40.5
myUpperLon          = -68
myUpperLat          = 46
EARTH_RADIUS        = 6366707.0 # (m)
QTH_LAT             = 42.647690 # my home's latitude
QTH_LON             = -71.253783 # my home's longitude
QTH_ALT             = 0 # my home's altitude (need to convert to ASL)
LOGAN_LAT           = 42.3656 # Logan latitude
LOGAN_LON           = -71.0096 # Logan longitude
MANCHESTER_LAT      = 42.9297 # Manchester lat
MANCHESTER_LON      = -71.4352 # Manchester lon
DEFAULT_COLOR_PAIR  = 1
N_DIFF_TRACKS       = 100
AIRCRAFT_ID_MSG     = 3
NUM_MAX_DATA        = 50 # number of aircraft to cache
MAX_TIME_UNOBSERVED = 150 # (sec) amt of time elapsed before removing 
LEN_OF_VALID_STRING = 22
MAX_FILE_SIZE_GB    = 1

