#!/usr/bin/env python

from sys import stdin
from math import floor
from datetime import datetime, timedelta
import re
import argparse

line_re = re.compile(
    r"(?P<from_hour>[0-9]{1,2}):(?P<from_min>[0-9]{2})"+ # e.g., 9:30
    r"\s*-\s*"+ # from - to (the line)
    r"(?P<to_hour>[0-9]{1,2}):(?P<to_min>[0-9]{2})"+ # e.g., 12.03
    r"(,)?\s+(?P<description>.*)" # Rest of the line
)

def calculate_total_time(lines):
    total_minutes = 0
    for line in lines:
        mo = line_re.match(line)
        if mo:
            from_dt = datetime(year=datetime.now().year,
                            month=datetime.now().month,
                            day=datetime.now().day,
                            hour=int(mo.group('from_hour')),
                            minute=int(mo.group('from_min')))
            to_dt   = datetime(year=datetime.now().year,
                            month=datetime.now().month,
                            day=datetime.now().day,
                            hour=int(mo.group('to_hour')),
                            minute=int(mo.group('to_min')))
            task_duration:timedelta = to_dt-from_dt
            total_minutes  += int(task_duration.total_seconds()/60.0)
    total_hours = floor(total_minutes/60)
    remaining_minutes = total_minutes-total_hours*60
    return (f"{total_hours}:{remaining_minutes:02d}")

def show_gui():
    import PySimpleGUI as sg
    total = ""
    sg.theme('Dark Blue 3')
    layout = [[sg.Multiline('Copy-Paste or write the timesheet here',
                            size=(60,10), key='-TIMESHEET TEXT-')],
              [sg.Button('Calculate'), sg.Button('Exit')]]
    window = sg.Window('Timesheet sum calculator', layout)
    while True:  # Event Loop
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        if event == 'Calculate':
            lines = re.split('\n\n|\r\n|\n', values['-TIMESHEET TEXT-'])
            total = calculate_total_time(lines)
            # Just append the total to the input field
            window['-TIMESHEET TEXT-'].update( 
                "" if not lines else "\n".join(lines)+
                '\n'+"Total "+total )
    window.close()
    return total

if __name__=='__main__':
    parser = argparse.ArgumentParser(description=
        'Calculates the sum of worked hours on a timesheet from stdin.\n'+
        'Valid lines are of the format "12.03-13:52 Did a lot".\n'+
        'Remember, on Windows, Ctrl+Z <ENTER> ends stdin input.' )
    parser.add_argument('--gui', action='store_true', dest='gui',
                        help='instead of reading from stdin, use a simple GUI')
    args = parser.parse_args()

    total = show_gui() if args.gui else calculate_total_time(stdin.readlines()) 
    if total:
        print(total)   
