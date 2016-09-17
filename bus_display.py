import argparse
import requests
from functools import wraps

from dothat import lcd
from dothat import backlight

COLUMNS = 16
ROWS = 3

parser = argparse.ArgumentParser('Display bus information for a given stop')
parser.add_argument(
    'stop_point', type=str,
    help='The TFL bus stop ID (see their documentation for details)')


def retry_on_network_error(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        for i in range(3):
            try:
                return f(*args, **kwargs)
            except IOError as e:
                pass
        raise e
    return wrapper


@retry_on_network_error
def get_json(url):
    response = requests.get(url, timeout=4)
    response_json = response.json()
    if response.status_code != 200:
        raise Exception(response_json['message'])
    return response_json


def reset_display():
    lcd.clear()
    backlight.rgb(175, 175, 175)
    lcd.set_cursor_position(0, 0)


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print e
            # Set the backlight to red and write the error message
            reset_display()
            backlight.rgb(150, 0, 0)
            lcd.write(str(e))
            raise e
    return wrapper


@handle_errors
def main(args):
    print args
    reset_display()
    lcd.write('Updating...')
    
    buses = get_json('https://api.tfl.gov.uk/StopPoint/%s/arrivals/' % args.stop_point)
    print buses
    sorted_buses = sorted(buses, key=lambda b: b['timeToStation'])[:ROWS]
    longest_bus_name_length = max(len(bus['lineName']) for bus in buses)

    reset_display()
    for line_number, bus in enumerate(sorted_buses):
        line_start = '{0} {1} '.format(
            line_number + 1,
            bus['lineName'].rjust(longest_bus_name_length)
        )

        minutes = bus['timeToStation'] / 60
        if minutes <= 1:
            due_time = ' due'
        else:
            due_time = ' %smin' % minutes

        middle_length = COLUMNS - len(line_start) - len(due_time)
        destination = bus['destinationName'][:middle_length]
        
        lcd.set_cursor_position(0, line_number)
        lcd.write('{0}{1}{2}'.format(line_start, destination, due_time))


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
