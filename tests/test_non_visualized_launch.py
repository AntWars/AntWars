from World import Team
from gameController import gameController
from loader import Loader


class TestClass(object):
    def configure_game(self, strat_names):
        game = gameController(size=(10, 10), display=False)

        strategies = Loader().loadStrategies(strat_names)
        teams = {Team(AntClass=strategy.AntClass,
                      BaseClass=strategy.BaseClass,
                      team_id=i + 1,
                      team_name=strategy.name) for i, strategy in enumerate(strategies)}

        game.Init(teams=teams)
        return game

    def test_two_strategies(self):
        strat_names = ['strategies/BasicStrategy.py', 'strategies/BasicStrategy.py']
        game = self.configure_game(strat_names)
        result = game.launch()

        # successfully complete
        assert len(result['stat']) == 2

    def test_one_strategy(self):
        strat_names = ['strategies/BasicStrategy.py']
        game = self.configure_game(strat_names)
        result = game.launch()

        # successfully complete
        assert len(result) == 2
        assert len(result['stat']) == 1

    def test_zero_strategies(self):
        strat_names = []
        game = self.configure_game(strat_names)
        result = game.launch()

        # successfully complete
        assert result == {'day': 0, 'stat': []}
