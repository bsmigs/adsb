HOST                = "192.168.1.58" # RPi IP address
PORT                = 30003 # dump1090 port we are listening to
BUFFER_SIZE         = 1024 # make it nice and big
myLowerLon          = -74.5
myLowerLat          = 40.5
myUpperLon          = -68
myUpperLat          = 46
EARTH_RADIUS        = 6371000#6366707.0 # (m)
WGS84_SEMIMAJOR_AXIS = 6378137
WGS84_ECCENTRICITY  = 0.0818191908426215
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
FT_TO_M             = 0.3048


ADSB_FIELDS         = ["message_type", "transmission_type", "session_ID", "aircraft_ID", "hex_address", "flight_ID","date_message_generated", "time_message_generated", "date_message_logged", "time_message_logged", "callsign", "altitude", "ground_speed", "track", "latitude", "longitude", "vertical_rate", "squawk", "alert_squawk_change", "emergency", "SPI_Ident", "is_on_ground"] 
