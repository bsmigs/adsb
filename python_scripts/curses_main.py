import numpy as np
from curseXcel import Table
from helper import convert_epoch_to_datestr
import curses
from constants import *
from ADSB import ADSB
import socket

col_names = ['Aircraft num', 'ICAO address', 'Callsign', 'Lat (deg)', 'Lon (deg)', 'Alt (ft)', 'Range (km)', 'Last seen']

def curses_main(stdscr):
    # create and open a socket connection
    s                   = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Socket made...")
    s.connect( (HOST, PORT) )
    print("Socket connected...")
    
    # create ADS-B object
    adsb                = ADSB(QTH_LAT, QTH_LON, QTH_ALT)

    # orig_size output is (y,x)
    orig_size           = stdscr.getmaxyx()
    
    table_width         = orig_size[1] 
    table_height        = orig_size[0] 
    n_cols              = len(col_names)
    n_rows              = round(0.9*table_height)
    cell_width          = round(0.9*table_width/n_cols)
    table               = Table(stdscr, n_rows, n_cols, cell_width, table_width, table_height, col_names=True, spacing=1)
    
    col                 = 0
    while col < n_cols:
        table.set_column_header(col_names[col], col)
        col             += 1
        
    entry_row_tuple     = {}
    entry_row_number    = 0
    screen_key          = 0
    try:
        # q in ASCII is 113
        while (True and screen_key != ord('q')):
            screen_key  = stdscr.getch()
            
            '''
            # Check if screen was re-sized (True or False)
            resize = curses.is_term_resized(orig_size[0], orig_size[1])
            
            # Action in loop if resize is True:
            if resize is True:
                
                y, x = stdscr.getmaxyx()
                
                print("resizing window with values y=",y,",x=",x)
                
                stdscr.clear()
                curses.resizeterm(y, x)
                stdscr.refresh()
            '''
    
        
            # grab current buffer. Returns bytes in python3
            curr_bytes_data = s.recv(BUFFER_SIZE)
            # convert bytes to string
            curr_str_data = curr_bytes_data.decode('utf-8')
            #print(curr_str_data)
    
            # process new messages
            hex_addr = adsb.process_new_messages(curr_str_data)
            
            # get current flight tuples
            flight_tuple = adsb.get_flight_tuple(hex_addr)
            
            # update fields in the table and add new fields 
            # that haven't been seen yet
        
            # we can only accommodate a number of
            # entries equal to n_rows. The column
            # headers already take up one row and
            # counting starts from 0, so
            # that's why we condition on n_rows-2
            if (len(entry_row_tuple) > n_rows-2):
                continue
            
            if (hex_addr not in entry_row_tuple):
                data_tuple = {}
                data_tuple['row_number'] = entry_row_number
                entry_row_tuple[hex_addr] = data_tuple
                
                # add a new row and populate it
                table.set_cell(entry_row_number, 0, entry_row_number+1)
                table.set_cell(entry_row_number, 1, hex_addr)
                
                # increment the counter
                entry_row_number += 1
                
            if ('callsign' in flight_tuple):
                entry_row_tuple[hex_addr]['callsign'] = flight_tuple['callsign']
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 2, flight_tuple['callsign'])                    
                
            if ('lla' in flight_tuple):
                lla = flight_tuple['lla']
                # update the other entries
                if (np.ndim(lla) == 1):
                    lat = np.around(lla[0], 4)
                    lon = np.around(lla[1], 4)
                    alt = np.around(lla[2], 2)
                else:
                    lat = np.around(lla[0,0], 4)
                    lon = np.around(lla[0,1], 4)
                    alt = np.around(lla[0,2], 2)
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 3, lat)
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 4, lon)
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 5, alt)
                
            if ('range' in flight_tuple):
                aircraft_range = np.around(adsb.get_most_recent_quantity(hex_addr, 'range')*1e-3, 1)
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 6, aircraft_range)
                
            if ('last_observed' in flight_tuple):
                last_seen = convert_epoch_to_datestr(adsb.get_most_recent_quantity(hex_addr, 'last_observed'))
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 7, last_seen)
            
            # delete entries we haven't seen anymore
            # because ADSB class dropped them due to timeout
            # of new data
            for hex_addr in list(entry_row_tuple.keys()):
                if (hex_addr not in flight_tuples):
                    # delete row if not seen
                    table.delete_row(entry_row_tuple[hex_addr]['row_number'])
                    del entry_row_tuple[hex_addr]
            
            # relable the row numbers corresponding to aircraft
            # num since we deleted some of them from the table
            entry_row_number = 0
            for hex_addr in entry_row_tuple:
                entry_row_tuple[hex_addr]['row_number'] = entry_row_number
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 0, entry_row_number+1)
                table.set_cell(entry_row_tuple[hex_addr]['row_number'], 1, hex_addr)
                
                entry_row_number += 1
            
            table.refresh()
    except KeyboardInterrupt:     
        print("Exiting out of program...")
        s.close()
    
    


stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
# make sure getch() is non-blocking
stdscr.nodelay(True)
print("Can change terminal colors =", curses.can_change_color())
if (curses.can_change_color()):
    curses.start_color()
    curses.init_pair(DEFAULT_COLOR_PAIR, curses.COLOR_GREEN, curses.COLOR_WHITE)
    
# main workhorse
curses.wrapper(curses_main)

curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()
