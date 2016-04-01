# -*- coding: utf-8 -*-
import curses
import time


def handle_with_courses(advancer, get_field, delay):
    stdscr = curses.initscr()

    while True:
        try:
            frame_start_time = time.time()
            advancer()

            stdscr.clear()
            for h, line in enumerate(get_field()):
                stdscr.addstr(h, 0, line)
            stdscr.refresh()

            # Adding a delay if needed
            real_delay = delay - (time.time() - frame_start_time)
            if real_delay > 0:
                time.sleep(real_delay)
        finally:
            curses.endwin()
