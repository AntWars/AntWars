# -*- coding: utf-8 -*-
from Ant import Ant
from Base import Base

class API(object):
    world = None

    def __init__(self, world):
        type(self).world = world
        self.team = None

    def Init(self, base):
        self.team = type(self).world.teams_by_base[base]

    def get_team_id_by_base(self, base):
        '''Возвращает идентификатор команды'''
        world = type(self).world
        return world.teams_by_base[base].team_id

    def ask_for_spawn(self, AntClass=type(None)):
        '''Пытается создать нового муравья'''
        world = type(self).world
        return world.spawn(self.team, AntClass)

    def get_list_of_ants(self):
        '''Возвращает копию списка живых муравьев вашей команды'''
        return list(self.team.ants_set)

    def get_size_of_world(self):
        '''Возвращает кортеж (x_size, y_size)'''
        return type(self).world.size

    def get_cost_of_ant_spawn(self):
        '''Возвращает стоимость создания нового муравья'''
        world = type(self).world
        return world.cost_of_ant

    def get_coord_by_obj(self, obj):
        '''Возвращает кортеж координат заданного объекта'''
        world = type(self).world
        return world.coord_by_obj.get(obj, None)

    def get_type_by_coord(self, *coords):
        '''Возвращает тип объекта, находящегося по заданным координатам'''
        world = type(self).world
        if len(coords) == 1:    # дали кортеж (x, y)
            coords = coords[0]
        return type(world.obj_by_coord.get(coords, None))
    
    def get_food_load(self, *args):
        '''Возвращает количество еды.

        Если передается объект, то он должен быть экземпляром Ant, Base или иметь тип type(None).
        Иначе это должны быть координаты -- либо два аргумента, либо кортеж (x, y) '''
        world = type(self).world
        obj_by_coord = lambda coord: world.obj_by_coord.get(coord, None)

        if len(args) == 1:
            smth = args[0]
            if isinstance(smth, Base):
                return world.teams_by_base[smth].food
            elif isinstance(smth, Ant):
                return world.cargo_by_ant.get(smth, 0)
            elif isinstance(smth, type(None)):
                return 0
            elif isinstance(smth, tuple):
                return self.get_food_load(obj_by_coord(smth))
            else:
                return smth.food                                    
        else:
            return get_food_by_coord(obj_by_coord(args))

    def is_enemy_by_coord(self, *coord):
        if len(coord) == 1:
            coord = coord[0]

        world = type(self).world
        other_ant = world.obj_by_coord.get(coord, None)
        if not isinstance(other_ant, Ant):
            return False
        else:
            return self.team != world.teams_by_base[other_ant.base]
