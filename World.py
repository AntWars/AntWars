# -*- coding: utf-8 -*-
from itertools import product
from random import uniform, randint, sample, choice

import states
from API import API
from Ant import Ant
from Base import Base
from Food import Food


class Team(object):
    """Обертка вокруг набора данных, относящихся к одной из команд"""
    def __init__(self, AntClass, BaseClass, team_id, team_name=''):
        self.AntClass = AntClass
        self.BaseClass = BaseClass
        self.team_id = team_id
        self.team_name = team_name
        self.food = 0
        self.base = None
        self.ants_set = set()


class World(object):
    """Игровой мир: игровое поле, обработка ходов команд, перемещение муравьев"""
    hit_prob = 0.9      # вероятность убить муравья при ударе
    cost_of_ant = 5     # стоимость создания одного муравья
    start_food_multiplier = 3   # на сколько муравьев хватит стартовой еды 
    food_prob = 0.3     # вероятность появления еды в клетке при создании планеты
    # магические константы при рандоме еды для размещения в клетку
    food_min_start_quantity_in_cell = 3
    food_max_start_quantity_in_cell = 7

    def __init__(self, size, log_name):
        self.log_name = log_name
        self.size = size
        self.coord_by_obj = dict()
        self.obj_by_coord = dict()
        self.teams_by_base = dict()
        self.cargo_by_ant = dict()   # по муравью дает его загрузку (едой)
        # хранит инорфмацию об изменении местоположения/удалении
        self.repaint_method_by_obj = dict()
        self.day = 0

        for coord in product(*map(range, self.size)):
            if 0 <= uniform(0, 1) < type(self).food_prob:
                quantity = randint(type(self).food_min_start_quantity_in_cell,
                                   type(self).food_max_start_quantity_in_cell)
                self.set_obj(obj=Food(quantity), coord=coord)
            else:
                self.obj_by_coord[coord] = None

    def add_team(self, team):
        team.base = team.BaseClass()
        self.teams_by_base[team.base] = team
        team.food = type(self).start_food_multiplier * type(self).cost_of_ant

    def Init(self, teams):
        for team in teams:
            self.add_team(team)

        # рандомим места для баз, размещаем их там и инициализируем
        coord_for_bases = sample(self.obj_by_coord, len(teams))
        for base, coord in zip(self.teams_by_base, coord_for_bases):
            API_for_setup = API(world=self)
            API_for_setup.Init(base)
            base.Init(API=API_for_setup)
            self.set_obj(obj=base, coord=coord)

    def set_obj(self, obj, coord):
        self.coord_by_obj[obj] = coord
        self.obj_by_coord[coord] = obj
        self.repaint_method_by_obj[obj] = 'createCell'

    def move_obj(self, obj, new_coord):
        dst_obj = self.obj_by_coord[new_coord]
        if dst_obj:
            self.del_obj(dst_obj)
        self.obj_by_coord[self.coord_by_obj[obj]] = None
        self.coord_by_obj[obj] = new_coord
        self.obj_by_coord[new_coord] = obj
        '''
        бывает, что база создала муравья, а муравей потом переместился в другую клетку.
        между моментом создания и моментом перемещения не было перерисовки, поэтому будем считать,
        что муравья создали в итоговой клетке
        '''
        if self.repaint_method_by_obj.get(obj, None) == 'createCell':
            pass
        else:
            self.repaint_method_by_obj[obj] = 'moveCell'

    def del_obj(self, obj):
        self.obj_by_coord[self.coord_by_obj[obj]] = None
        del self.coord_by_obj[obj]
        '''
        бывает, что еду на пустое место сбросил один муравей, тут же подобрал другой,
        и перерисовки между этими ходами еще не было. в таком случае с точки зрения перерисовки
        сброса вообще не было
        '''
        if self.repaint_method_by_obj.get(obj, None) == 'createCell':
            del self.repaint_method_by_obj[obj]
        else:
            self.repaint_method_by_obj[obj] = 'deleteCell'

    def hit(self, dst_coord, ant):
        enemy = self.obj_by_coord.get(dst_coord, None)
        if not isinstance(enemy, Ant):
            return
        else:
            if 0 <= uniform(0, 1) <= type(self).hit_prob:
                # удаляем муравья отовсюду
                self.teams_by_base[enemy.base].ants_set.difference_update({
                                                                          enemy})
                self.del_obj(enemy)
                self.cargo_by_ant.pop(enemy, None)

    def drop_food(self, dst_coord, ant):
        obj = self.obj_by_coord.get(dst_coord, None)
        if self.cargo_by_ant.get(ant, 0):
            self.cargo_by_ant[ant] = 0
            if isinstance(obj, Base):
                self.teams_by_base[obj].food += 1
            elif isinstance(obj, Food):
                obj.food += 1
            elif isinstance(obj, Ant):
                if not self.cargo_by_ant.get(obj, 0):
                    self.cargo_by_ant[obj] = 1
            elif dst_coord in self.obj_by_coord:
                food = Food(1)
                self.set_obj(obj=food, coord=dst_coord)

    def take_food(self, dst_coord, ant):
        obj = self.obj_by_coord.get(dst_coord, None)
        if isinstance(obj, Food):
            self.cargo_by_ant[ant] = 1
            if obj.food == 1:
                self.del_obj(obj)
            elif obj.food > 1:
                obj.food -= 1

    def move(self, dst_coord, ant):
        # todo: может быть стоит не пропускать ход в world.move(), если
        # перемещение некорректное, а бросать исключение?
        if dst_coord not in self.obj_by_coord:
            return
        elif self.coord_by_obj[ant] == dst_coord:
            return
        elif isinstance(self.obj_by_coord[dst_coord], (Ant, Base)):
            return
        else:
            self.move_obj(obj=ant, new_coord=dst_coord)

    def spawn(self, team, AntClass=None):
        """Обработка события "создать муравья". Возвращает True, если удалось, False иначе """

        AntClass = team.AntClass if AntClass is None else AntClass
        x_base, y_base = self.coord_by_obj[team.base]

        # если ресурсов достаточно для создания
        if team.food >= type(self).cost_of_ant:
            # может случиться, что возле базы нет свободной клетки
            try:
                coord = choice([(x_base + dx, y_base + dy)
                               for dx, dy in product(range(-1, 2), repeat=2)
                               if (x_base + dx, y_base + dy) in self.obj_by_coord
                               and self.obj_by_coord.get((x_base + dx, y_base + dy), None) is None])
                ant = AntClass(base=team.base)
                team.ants_set.update({ant})
                self.set_obj(obj=ant, coord=coord)
                team.food -= type(self).cost_of_ant
                return True
            except IndexError:
                return False
        else:
            return False

    def advance(self):
        """Ход планеты, он же игровой день"""
        self.repaint_method_by_obj.clear()
        for team in self.teams_by_base.itervalues():
            team.base.advance()
            for ant in team.ants_set:
                dst_coord, move = ant.move()
                # todo: вставить проверку на то, что муравей не прыгнул дальше
                # одной клетки
                getattr(self, move)(dst_coord, ant)
        if states.DEBUG:
            import ipdb; ipdb.set_trace()

        # срабатывает, если при запуске был задан флаг --logs
        self.dump()
        self.day += 1

    def dump(self):
        """ Сбрасывает текущее состояние поля str(world) в файл filename."""
        # если при запуске флаг "--logs" не был указан, то self.log_name == None
        if self.log_name:
            with open(self.log_name, mode='a') as f:
                f.write(str(self).replace('\n', '$') + '\n')

    def __str__(self):
        Buffer = list()
        for y in range(self.size[1]):
            for x in range(self.size[0]):
                figure = self.obj_by_coord[x, y]
                label = ' ' if figure is None \
                    else 'f' if isinstance(figure, Food) \
                    else 'B' if isinstance(figure, Base) \
                    else str(figure.base.team_id)
                Buffer.append(label)
            Buffer.append('\n')

        Buffer.extend([line + '\n' for line in self.getTeamStatList()])
        return "".join(Buffer)

    def getTeamStatList(self):
        return ['Team %d%s: food %d, ants %d' %
                (base.team_id,
                 (' (%s)' % self.teams_by_base[base].team_name) if self.teams_by_base[
                  base].team_name != '' else '',
                 self.teams_by_base[base].food,
                 len(self.teams_by_base[base].ants_set)
                ) for base in sorted(self.teams_by_base, key=lambda base: base.team_id)]
