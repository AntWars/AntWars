# -*- coding: utf-8 -*-

import argparse
from time import sleep
from datetime import datetime

from AntWars import World, Team
from BasicStrategy import BasicAnt, BasicBase
from courses_tools import handle_with_courses


def dump(planet, filename):
    ''' Сбрасывает текущее состояние поля str(planet) в файл filename.'''
    with open(filename, mode='a') as f:
        f.write(str(planet).replace('\n', '$') + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--size', type=str, dest='size', default='50 21', help='Size of map, pair of integer as "x_size y_size". By default equals to "50 21"')
    parser.add_argument('-d', '--delay', type=float, dest='delay', default=0.5, help='Delay between turns in second. By deafult equals to 0.3 sec.')
    parser.add_argument('--logs', action='store_true', dest='logs_flag', help='Enable log gathering.')

    args = parser.parse_args()
    log_name = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    team1 = Team(AntClass=BasicAnt, BaseClass=BasicBase, team_id=1)
    team2 = Team(AntClass=BasicAnt, BaseClass=BasicBase, team_id=2)
    Earth = World(size=tuple(map(int, args.size.split())))
    Earth.Init(teams={team1, team2})

    handle_with_courses(advancer=Earth.advance, get_field=Earth.get_field, delay=args.delay)
