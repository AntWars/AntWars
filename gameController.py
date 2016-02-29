# -*- coding: utf-8 -*-

import os.path
from Tkinter import *
from World import Food, World
from Base import Base
from Ant import Ant
from random import randint
from itertools import izip, product
from functools import partial

class gameController:
    def loadTheme(self, themeStr):
        if not os.path.isfile('themes/' + themeStr + '.py'):
            raise ValueError('Incorrect theme specified.')
        with open('themes/' + themeStr + '.py') as themeFile:
            exec(themeFile.read())
        if not hasattr(self, 'theme'):
            raise ValueError('Smth goes wrong, theme loading crashed')

    def __init__(self, size, delay, log_name, themeStr):
        # todo: написать спецификацию для loadTheme() и файлов с темами
        self.loadTheme(themeStr)
        self.world = World(size, log_name)
        self.delay = delay
        self.teamColors = []
        self.statStringVars = []
        self.master = Tk()
        self.figure_by_obj = dict()
        self.winner = None
        self.canvas = Canvas(self.master,
                             width=size[0] * self.theme['CELL_SIZE'],
                             height=size[1] * self.theme['CELL_SIZE'],
                             bg=self.theme['BG_COLOR']
                             )

    def Init(self, teams):
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
                    or isCloseWithOther(newColor)\
                    :
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
                                             outline=self.theme['OUTLINE_COLOR']
                                             )
        self.canvas.pack(ipadx=0, ipady=0)
        self.world.Init(teams)
        self.teamColors = [getNewColor() for _ in sorted(self.world.teams_by_base, key=lambda base: base.team_id)]
        self.statStringVars = [StringVar() for _ in sorted(self.world.teams_by_base, key=lambda base: base.team_id)]
        for stringVar, color in izip(self.statStringVars, self.teamColors):
            lbl = Label(self.master, textvariable=stringVar, fg=color, bg=self.theme['BG_COLOR'])
            lbl.pack()
        self.repaint()

    def repaint(self):
        for obj, method in self.world.repaint_method_by_obj.items():
            getattr(self, method)(obj)

        statList = self.world.getTeamStatList()
        if len(self.world.teams_by_base) == 0:
            self.master.destroy()
            self.advance = self.stopGame()
        elif len(self.world.teams_by_base) == 1:
            self.winner = next(self.world.teams_by_base.itervalues())
        elif sum(True for tmp in map(lambda s: s.split(' '), statList) if
               tmp[-1] != '0'   # ants
               or int(tmp[-3][:-1]) >= type(self.world).cost_of_ant     # food
               ) < 2:
            self.winner = next(team for team in self.world.teams_by_base.itervalues() if team.ants_set)

        for stringVar, line in izip(self.statStringVars, statList):
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
        elif isinstance(obj, Base):
            color = self.theme['BASE_COLOR']        
        elif isinstance(obj, Food):
            color = self.theme['FOOD_COLOR']
        elif isinstance(obj, Ant):
            color = self.teamColors[obj.base.team_id - 1]
        figure = self.canvas.create_rectangle(x * self.theme['CELL_SIZE'],
                                              y * self.theme['CELL_SIZE'],
                                              (x + 1) * self.theme['CELL_SIZE'],
                                              (y + 1) * self.theme['CELL_SIZE'],
                                              fill=color,
                                              outline=self.theme['OUTLINE_COLOR'],
                                              )
        self.figure_by_obj[obj] = figure
        self.canvas.update_idletasks()

    def advance(self):
        if self.winner:
            self.advance = self.stopGame
        else:
            self.world.advance()
            self.repaint()
        self.master.after(self.delay, self.advance)

    def launch(self):
        self.master.after(1, self.advance)
        self.master.mainloop()

    def stopGame(self):
        for stringVar, line in izip(self.statStringVars, self.world.getTeamStatList()):
            if int(line.split(' ')[1]) != self.winner.team_id:
                line = ''
            else:
                line = 'GAME OVER! ' + line + ' GAME OVER!'
            stringVar.set(line)