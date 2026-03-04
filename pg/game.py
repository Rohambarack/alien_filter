import random

from tqdm import tqdm

from rule import Rule
from player import Player_Base

class alien_game:
    def __init__(self, 
                 rule:Rule, 
                 player: Player_Base,
                 n_guesses_win:int=8, 
                 max_turns:int=100,
                 stimuli_features:int=5):
        self.rule = rule
        self.player = player
        self.ncg = n_guesses_win
        self.m_turns = max_turns
        self.s_f = stimuli_features
        #self.max_p_rules = []
        #self.max_p = []
        #self.guesses = []
        self.correct_guess_counter = 0
        self.turn_overviews = []
        self.game_overview = {}

    #stimuli randomizer
    def stimuli_maker(self):
        #randomize (unif)
        self.stimuli = [random.randint(0,1) for i in range(self.s_f)]

    def play(self):
        """ 
        Plays the alien game:
        In each turn the player
        - chooses rules
        - assesses their probability
        - makes a guess
        - updates based on feedback
        - (chooses new rules)
        """
        for turn in tqdm(range(self.m_turns)):
            #present stimulus
            self.stimuli_maker()
            #player makes a guess
            self.player.random_sampler_remove()
            self.player.proportional_p_update()
            self.player.use_rule(self.stimuli)
            self.player.get_guess()
            #game metadata
            guess = self.player.guess
            correct_c = self.rule.check_stimuli(self.stimuli)
            if guess == correct_c:
                self.correct_guess_counter +=1
            else:
                self.correct_guess_counter = 0
            turn_overview = [{"turn":turn,
                             "rule":r.get("rule"),
                             "p":r.get("p")
            }for r in self.player.current_rules]
            self.turn_overviews.append(turn_overview)
            #end game
            if self.correct_guess_counter == self.ncg:
                self.game_overview.update(
                    {"game_data":self.turn_overviews,
                     "meta_data":{"status":"win",
                                  "n_turns":turn,
                                  "correct_rule":self.rule.v_rule,
                                  "max_p_rule":self.player.max_p_rule,
                                  "max_p":self.player.max_p}}
                    )
                break 
            elif turn == self.m_turns:
                self.game_overview.update(
                    {"game_data":self.turn_overviews,
                     "meta_data":{"status":"loss",
                                  "n_turns":turn,
                                  "correct_rule":self.rule.v_rule,
                                  "max_p_rule":self.player.max_p_rule,
                                  "max_p":self.player.max_p}}
                    )
                break
            else:
                pass
            #update belief
            self.player.instant_resample(correct_c)
            


