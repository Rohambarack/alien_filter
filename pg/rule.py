import itertools
import random

def remove_dup(x:str):
    x_l = x.lower()
    if len(x_l) == len(set(x_l)):
        return x
    else:
        return 
    
def insert_before(a,idx,value):
    b=a[:idx-1] + value + a[idx-1:]
    return b
def insert_before_2(a,idx,value):
    b=a[:idx-3] + value + a[idx-3:]
    return b
def insert_after(a,idx,value):
    b=a[:idx+2] + value + a[idx+2:]
    return b
def insert_after_2(a,idx,value):
    b=a[:idx+4] + value + a[idx+4:]
    return b

def reassign_parentheses(rule:str):

    r_list = rule.split()
    #how many ors
    ors = len([i for i in  r_list if i == "or"])
    if ors == 0:
        pass
    ####  1 or
    elif ors== 1 and len(r_list) != 3:
        #if not in the middle or only two args
        if r_list[3] != "or" or (r_list[3] == "or" and len(r_list)==5):
            #decide to change or not (unif)
            change = random.randint(0,1)
            if change == 0:
                pass
            else:
                or_where = r_list.index("or")
                r_list = insert_before(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after(r_list, or_where,[")"])
        elif r_list[3] == "or":
            #if in the middle
            #decide to change non, mid, left, right
            change = random.randint(0,3)
            if change == 0:
                pass
            elif change == 1:
                or_where = r_list.index("or")
                r_list = insert_before(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after(r_list, or_where,[")"])
            elif change == 2:
                or_where = r_list.index("or")
                r_list = insert_before_2(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after(r_list, or_where,[")"])
            elif change == 3:
                or_where = r_list.index("or")
                r_list = insert_before(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after_2(r_list, or_where,[")"])
    elif ors== 1 and len(r_list) == 3:
        pass
    #### 2 or
    elif ors==2 and len(r_list) != 5:
        #if next to each other
        if r_list[r_list.index("or")+2] == "or":
            #decide to change or not (unif)
            change = random.randint(0,1)
            if change == 0:
                pass
            else:
                or_where = r_list.index("or")
                r_list = insert_before(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after_2(r_list, or_where,[")"])

        elif r_list[r_list.index("or")+2] != "or":
        #if not next to each other
        #decide to change non, both, left, right
            change = random.randint(0,3)
            if change == 0:
                    pass
            elif change == 1:
                r_list = insert_before(r_list, 5 ,["("])
                r_list = insert_after(r_list, 7,[")"])
                or_where = r_list.index("or")
                r_list = insert_before(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after(r_list, or_where,[")"])
            elif change == 2:
                or_where = r_list.index("or")
                r_list = insert_before(r_list, or_where,["("])
                or_where = r_list.index("or")
                r_list = insert_after(r_list, or_where,[")"])
            elif change == 3:
                r_list = insert_before(r_list, 5 ,["("])
                r_list = insert_after(r_list, 7,[")"])
    elif ors==2 and len(r_list) != 5:
        pass
    ### 3 ors
    elif ors == 3:
        pass

    return " ".join(r_list)

def eval_content_check(rule:str,
                       var_name:str="feature",
                       n_features:int=5):

    """ makes sure no nasty thing ends up in the eval() """
    possible_strs = [f"{var_name}[{i}]=={j}" for i in range(n_features) for j in range(2)]
    possible_strs = set(possible_strs + ["(",")","and","or"])
    
    rule_set = set(rule.split())

    assert  rule_set.issubset(possible_strs), f"unexpected chars in the formal rule: {rule}"

def verbal_to_formal(verbal_rule:str,var_name:str="feature"):

    """decodes the verbal rule to something that can be evaluated on an n_length map of features"""

    f_rule = verbal_rule.split()
    formal_rule_map = [{"idx":0,"Thin_Legs":0,"Thick_Legs":1},
                        {"idx":1,"Arms_Down":0,"Arms_Up":1},
                        {"idx":2,"No_Spots":0,"Spots":1},
                        {"idx":3,"Eyes_Without_Stalk":0,"Eyes_With_Stalk":1},
                        {"idx":4,"Blue":0,"Green":1}
    ]

    new_l = []
    for element in f_rule:
        if element in ["(",")","and","or"]:
            new_l.append(element)
        else:
            for decoding in formal_rule_map:
                if element in decoding.keys():
                    val = decoding.get(element)
                    idx = decoding.get("idx")
                    statement = f"{var_name}[{idx}]=={val}"
            new_l.append(statement)
    return " ".join(new_l)

def remove_dup(x:str):
    x_l = x.lower()
    if len(x_l) == len(set(x_l)):
        return x
    else:
        return 

def translate_rule(rule:str):

    rule_map = { "l": "Thin_Legs",
             "L": "Thick_Legs",
             "a": "Arms_Down",
             "A":"Arms_Up",
             "b": "No_Spots",
             "B": "Spots",
             "e": "Eyes_Without_Stalk",
             "E": "Eyes_With_Stalk",
             "c": "Blue",
             "C": "Green"}

    translated_l = []
    for i in rule:
        translated_l.append(rule_map.get(i))
        
    return translated_l

def assemble_sentence(features:list[str],
                      logics:list[int],
                      max_features:int=5):

    logic_operations = ["and","or"]
   
    segments = []
    #change to and if all 5 given in a rule
    if len(features) == max_features:
        logics = [0 for i in range(max_features-1)]

    for idx_f, feature in enumerate(features):
        try:
            segment = f"{feature} {logic_operations[logics[idx_f]]}"
            segments.append(segment)

        except IndexError:
            segments.append(f"{feature}")
     
    return " ".join(segments)
    
def rule_maker():
    # sample important dimensions (unif)
    n_dims = random.randint(1,5)

    # select feature dimensions
    dims = [ ''.join([*a]) for i in range(1,n_dims+1) for a in itertools.combinations('lLaAbBeEcC', i) if len(a)==n_dims]
    dims = [i for i in dims if remove_dup(i) != None]

    #translate properties
    #sample from dims (unif)
    pos_in_dims = random.randint(0,len(dims)-1)
    rule_abr = dims[pos_in_dims]
    rule_trans =translate_rule(rule_abr)

    # find logical connections 
    n_l_con = n_dims-1
    #assemble list
    l_pos = [random.randint(0,1) for i in range(n_l_con)]
    #assemble rule
    verbal_rule = assemble_sentence(rule_trans,l_pos)
    verbal_rule = reassign_parentheses(verbal_rule)
    #make it formal
    formal_rule = verbal_to_formal(verbal_rule)
    eval_content_check(formal_rule)
    
    return verbal_rule, formal_rule

def rule_evaluator(formal_rule:str,feature):
    eval_content_check(formal_rule)
    result = eval(formal_rule)
    return result

#stimuli randomizer
def stimuli_maker(n_features:int = 5):

    #randomize (unif)

    return [random.randint(0,1) for i in range(n_features)]

class Rule:
    def __init__(self, 
                 verbal_rule:str = "empty"):

        self.v_rule = verbal_rule
        
    def formalize_rule(self):
        assert self.v_rule != "empty", "No verbal rule found"
        formal_rule = verbal_to_formal(self.v_rule)
        eval_content_check(formal_rule)
        self.f_rule = formal_rule

    def check_stimuli(self,
                      feature:list[int]):
        
        eval_content_check(self.f_rule)
        result = eval(self.f_rule)
        return result
    
    def randomize_rule(self):
        self.v_rule, self.f_rule = rule_maker()
    
        
