import random
from rule import *

from datasets import Dataset, concatenate_datasets

#create a player class
class Player_Base:
    def __init__(self, all_rules_ds:Dataset, memory:int=5):
        self.memory = memory
        self.all_rules = all_rules_ds
        self.current_rules = []
        #keeps track of rules removed, mostly for diagnostic reasons
        self.removed_rules = []

    #rule sampler
    def random_sampler_remove(self):
        """ 
        Randomly samples from all available rules based on memory
        Removes from current rules from all rules, so all rules will
        enter memory max 1 times.
        """
        n_rules = self.memory - len(self.current_rules)
        s1 = random.sample(range(len(self.all_rules)),n_rules)

        self.current_rules = Dataset.from_dict(self.all_rules[s1])

        self.all_rules = self.all_rules.filter(lambda ds:ds["rule"] not in self.current_rules["rule"])

    #probability updater
    def proportional_p_update(self):
        """ 
        Assigns the probability of a rule being the correct one based on how many turns it has been in.
        The longer a rule stays in memory, the higher the p.
        """
        def _r_r(ds):
            """ 
            Increases the rule relevance by 1.
            Starts with 1 for all rules in turn 1
            e.g.:
            If memory == 5
            [1,1,1,1,1]

            If rule[0] stays for 3 turns and rule[2] stays for 2:
            [3,1,2,1,1]
            """
            try:
                r_r = ds["r_r"] + 1
            except (KeyError,TypeError):
                r_r = 1
            ds.update({"r_r":r_r})
            return ds
        self.current_rules = self.current_rules.map(_r_r)

        def _proportional_re_weigh(ds,weights):
            """ 
            Proportionally changes rule ps
                If r_r == [1,1,1,1,1]
                    p = [.2,.2,.2,.2,.2]
                If r_r == [3,1,2,1,1]
                    p = [.375,.125,.25,.125,.125]
            """
            w_sums = sum(weights)
            new_weight = ds["r_r"] / w_sums
            ds.update({"p":new_weight})
            return ds
        self.current_rules = self.current_rules.map(
            _proportional_re_weigh,
            fn_kwargs={"weights" : self.current_rules["r_r"]})
        
    #Use rule
    def use_rule(self,stimuli:list[int]):
        """ 
        All rules ar updated at the same time
        Highest prob rule is the "guess"
        """
        def _compare_stimuli(ds:Dataset,
                            stimuli:list[int]):
            "All rules in memory are checked for passing the stimuli"
            if stimuli in ds["passes"]:
                passed_stim = True
            else:
                passed_stim = False
            ds.update({"passed_stim":passed_stim})
            return ds
        self.current_rules = self.current_rules.map(
            _compare_stimuli,
            fn_kwargs={"stimuli":stimuli}
            )
        
    #get guess
    def get_guess(self):
        """ guess made based on highest rule prob"""
        max_p_r_idx = self.current_rules["p"].index(
            max(self.current_rules["p"])
            )
        self.max_p_rule = self.current_rules[max_p_r_idx]["rule"]
        self.guess_correct = self.current_rules[max_p_r_idx]["passed_stim"]

    #resample based on feedback
    def instant_resample(self,correct_c):
        """
        removes rules if they did not pass criteria,
        fills up with new rules until n_max reached
        correct_c : whether the actual game rule passes the stim or not
        """
        def _remove_incorrect(ds,correct_c):
            if ds["passed_stim"] != correct_c:

                self.removed_rules.append(ds["rule"])
                return False
            else:
                return True
            
        self.current_rules = self.current_rules.filter(
            _remove_incorrect,
            fn_kwargs={"correct_c":correct_c})
        
        #refill memory
        if len(self.current_rules) < self.memory:
            self.temp_rules = self.random_sampler_remove(self)

            self.current_rules = concatenate_datasets(
                [self.temp_rules,self.current_rules])
        else:
            pass