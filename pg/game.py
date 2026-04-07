import random
from collections import defaultdict

from tqdm import tqdm

from plotnine import *
import pandas as pd

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
            for rule_data in turn_overview:
                self.turn_overviews.append(rule_data)
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
                                  #make a random choice model for comparison
                                  #"correct_r_stims":
                                  "max_p_rule":self.player.max_p_rule,
                                  "max_p":self.player.max_p}}
                    )
                break
            else:
                pass
            #update belief
            self.player.instant_resample(correct_c)


    #plotting     
    def plot_game(self,display_threshold = 0.5):
        """ 
        Plots the course of the game, displaying rule probability changes across turns
        """
        game_list = self.game_overview.get("game_data")
        disp_bound = display_threshold

        [i.update({"rule_disp":i.get("rule")}) if i.get("p") > disp_bound else i.update({"rule_disp":" "}) for i in game_list]
        #copy row for color matching
        [i.update({"rule_disp_c":i.get("rule_disp")}) for i in game_list]
        #remove multiple rule_disps for the same
        #  rule
        rule_disp_o = defaultdict(int)
        for i in game_list:
            rule_disp_o[i.get("rule_disp")] += 1

        [i.update({"rule_disp":" "}) for idx_i, i in enumerate(game_list) if i.get("rule_disp") in rule_disp_o.keys() and i.get("rule_disp") in [d.get("rule_disp") for d in game_list[:(idx_i-1)]]]

        #read rule to rule_disp_c if at some point the rule went below threshold
        rules_above_treshold = list(set([i.get("rule") for i in game_list if i.get("p") > disp_bound]))
        [i.update({"rule_disp_c":i.get("rule")}) for i in game_list if i.get("rule") in rules_above_treshold]

        plot_it = pd.DataFrame(game_list)

        return (
            ggplot(plot_it, aes("turn","p",group= "rule", color= "rule_disp_c"))
            + geom_point()
            + geom_line()
            + geom_text(aes(label = "rule_disp"), size = 5, nudge_x = -2)
            + xlim(0,max(plot_it["turn"])) 
            + theme(legend_position="none")
        )

