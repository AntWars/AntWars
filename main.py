# -*- coding: utf-8 -*-

import argparse
from datetime import datetime

from World import Team
from gameController import gameController
from ConfigDialog import ConfigDialog
from loader import Strategy, Loader

if __name__ == '__main__':
    # TODO: Return console interface.
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cli', dest='cli', action='store_true', help='Skip graphical config and use console options.')
    parser.add_argument('-s', '--size', type=str, dest='size', default='50 21', help='Size of map, pair of integer as "x_size y_size". By default equals to "50 21"')
    parser.add_argument('-d', '--delay', type=int, dest='delay', default=500, help='Delay between turns in ms.')
    parser.add_argument('--logs', action='store_true', dest='logs_flag', help='Enable logs gathering.')
    parser.add_argument('-t', '--theme', type=str, dest='theme', default='constructor', help='Theme for graphical interface.')
    parser.add_argument('-a', '--algorithms', type=str, dest='strategies', action='append', help='Specifes one strategy. Use few -s to specify few strategies')
   
    args = parser.parse_args()
    
    # # Not working anyway.
    # log_name = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    log_name = None
    
    if not args.cli:
        teams = set() 
        strategies = []
        config = dict()
        ConfigDialog(strategies, config)
        size = (config['width'], config['height'])
        delay = config['delay']
        ready_log_name = (log_name if config['enable_logs'] else None)
        themeStr=config['theme']
    else:
        size = tuple(map(int, args.size.split()))
        delay = args.delay
        ready_log_name = (log_name if args.logs_flag else None)
        themeStr = args.theme
        teams = set()
        strategies = Loader().loadStrategies(args.strategies)
    for i in range(len(strategies)):
        teams.update({Team(AntClass=strategies[i].AntClass, BaseClass=strategies[i].BaseClass, team_id=i + 1)})            
    AntWarsGame = gameController(size=size,
                                 delay=delay,
                                 log_name=ready_log_name,
                                 themeStr=themeStr
                                 )

    AntWarsGame.Init(teams=teams)
    AntWarsGame.launch()
