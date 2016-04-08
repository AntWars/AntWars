# -*- coding: utf-8 -*-
from Tkinter import *
from functools import partial
from itertools import izip, product
from random import randint

import yaml

from Ant import Ant
from Base import Base
from Food import Food
from World import World


class gameController:
    def __init__(self, size, delay=None, log_name=None, themeStr=None, display=True):
        self.world = World(size, log_name)
        self.figure_by_obj = dict()
        self.winner_id = None
        self.display = display

        if display:
            with open(themeStr) as f:
                self.theme = yaml.load(f)
            self.delay = delay
            self.teamColors = []
            self.statStringVars = []
            self.master = Tk()
            self.canvas = Canvas(self.master,
                                 width=size[0] * self.theme['CELL_SIZE'],
                                 height=size[1] * self.theme['CELL_SIZE'],
                                 bg=self.theme['BG_COLOR']
                                 )

    def Init(self, teams):
        self.world.Init(teams)

        if self.display:
            def hexToRGB(s):
                return map(partial(int, base=16), [s[i:i+2] for i in range(1, 7, 2)])

            def isClose(la, ra):
                return abs(la[0] - ra[0]) < 40\
                       or abs(la[1] - ra[1]) < 40 \
                       or abs(la[2] - ra[2]) < 40

            def isCloseWithOther(newColor):
                return any(isClose(hexToRGB(newColor), hexToRGB(color)) for color in self.teamColors)

            def getNewColor():
                newColor = ''
                while not newColor \
                        or isClose(hexToRGB(newColor), (255, 255, 255)) \
                        or isClose(hexToRGB(newColor), (0, 0, 0)) \
                        or isClose(hexToRGB(newColor), (255, 0, 0)) \
                        or isCloseWithOther(newColor):
                    newColor = ("#%06x" % randint(0, 0xFFFFFF))
                return newColor

            self.master.title('Ant Wars')
            self.master['bg'] = self.theme['BG_COLOR']
            self.canvas.create_rectangle(0,
                                         0,
                                         (self.world.size[0] + 1) * self.theme['CELL_SIZE'],
                                         (self.world.size[1] + 1) * self.theme['CELL_SIZE'],
                                         fill=self.theme['EMPTY_CELL_COLOR'],
                                         )
            if self.theme['EMPTY_OUTLINE']:
                for x, y in product(*map(range, self.world.size)):
                    self.canvas.create_rectangle(x * self.theme['CELL_SIZE'],
                                                 y * self.theme['CELL_SIZE'],
                                                 (x + 1) * self.theme['CELL_SIZE'],
                                                 (y + 1) * self.theme['CELL_SIZE'],
                                                 fill='',
                                                 outline=self.theme[
                                                     'OUTLINE_COLOR']
                                                 )
            self.canvas.pack(ipadx=0, ipady=0)
            self.teamColors = [getNewColor() for _ in sorted(
                self.world.teams_by_base, key=lambda base: base.team_id)]
            self.statStringVars = [StringVar() for _ in sorted(
                self.world.teams_by_base, key=lambda base: base.team_id)]
            for stringVar, color in izip(self.statStringVars, self.teamColors):
                lbl = Label(self.master, textvariable=stringVar,
                            fg=color, bg=self.theme['BG_COLOR'])
                lbl.pack()
            self.repaint()

    def check_winner(self):
        statList = self.world.getTeamStatList()
        statistics = [
            {
                'id': team.team_id,
                'name': team.team_name,
                'food': team.food,
                'ants': len(team.ants_set),
            } for team in self.world.teams_by_base.itervalues()
        ]
        statistics.sort(key=lambda t: (t['food'], t['ants']), reverse=True)

        if len(statistics) == 0:
            self.winner_id = -1
        elif len(self.world.teams_by_base) == 1:
            self.winner_id = statistics[0]['id']
        elif sum(True for tmp in map(lambda s: s.split(' '), statList) if
                 tmp[-1] != '0'  # ants
                 or int(tmp[-3][:-1]) >= type(self.world).cost_of_ant  # food
                 ) < 2:
            self.winner_id = statistics[0]['id']
        return statistics

    def repaint(self):
        for obj, method in self.world.repaint_method_by_obj.items():
            getattr(self, method)(obj)

        self.check_winner()
        if self.winner_id == -1:
            # all died
            self.master.destroy()
            self.advance = self.stopGame

        for stringVar, line in izip(self.statStringVars, self.world.getTeamStatList()):
            stringVar.set(line)

    def deleteCell(self, obj):
        self.canvas.delete(self.figure_by_obj[obj])
        self.canvas.update_idletasks()

    def moveCell(self, obj):
        x, y = self.world.coord_by_obj[obj]
        figure = self.figure_by_obj[obj]
        self.canvas.coords(figure,
                           x * self.theme['CELL_SIZE'],
                           y * self.theme['CELL_SIZE'],
                           (x + 1) * self.theme['CELL_SIZE'],
                           (y + 1) * self.theme['CELL_SIZE']
                           )
        self.canvas.update_idletasks()

    def createCell(self, obj):
        x, y = self.world.coord_by_obj[obj]
        if obj is None:
            color = self.theme['EMPTY_CELL_COLOR']
        elif isinstance(obj, Food):
            color = self.theme['FOOD_COLOR']
        elif isinstance(obj, Base):
            color = self.theme['BASE_COLOR']
        elif isinstance(obj, Ant):
            color = self.teamColors[obj.base.team_id - 1]
        figure = self.canvas.create_rectangle(x * self.theme['CELL_SIZE'],
                                              y * self.theme['CELL_SIZE'],
                                              (x + 1) * self.theme['CELL_SIZE'],
                                              (y + 1) * self.theme['CELL_SIZE'],
                                              fill=color,
                                              outline=self.theme[
                                                  'OUTLINE_COLOR'],
                                              )
        self.figure_by_obj[obj] = figure
        self.canvas.update_idletasks()

    def advance(self):
        if self.winner_id:
            self.advance = self.stopGame
        else:
            self.world.advance()
            self.repaint()
        self.master.after(self.delay, self.advance)

    def launch(self):
        if self.display:
            self.master.after(1, self.advance)
            self.master.mainloop()
        else:
            statistics = self.check_winner()
            while not self.winner_id:
                self.world.advance()
                statistics = self.check_winner()
            return {'day': self.world.day, 'stat': statistics}

    def stopGame(self):
        for stringVar, line in izip(self.statStringVars, self.world.getTeamStatList()):
            if int(line.split(' ')[1]) != self.winner_id:
                line = ''
            else:
                line = 'GAME OVER! ' + line + ' GAME OVER!'
            stringVar.set(line)
