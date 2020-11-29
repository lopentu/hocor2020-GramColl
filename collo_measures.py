from math import log2, log, sqrt
from scipy.stats import fisher_exact

def cca(freq_table):
    """
    Covarying Collexeme Analysis
    freq_table: dict. Format: {(Slot1, Slot2): freq, (Slot1, Slot2): freq, ...}
    
    Contingency table:
                    L_slot1     ~L_slot1
        L_slot2       o11          o12
        ~L_slot2      o21          o22

    References:
        Desagulier, G. (2017). Corpus Linguistics and Statistics with R. p213-221.
    """

    # Get total size
    corp_size = sum(v for k, v in freq_table.items())
    
    # Get marginal sizes
    subj_totals = {}
    act_totals = {}
    for k, v in freq_table.items():
        subj, act = k
        if subj not in subj_totals: subj_totals[subj] = 0
        if act not in act_totals: act_totals[act] = 0
        subj_totals[subj] += v
        act_totals[act] += v
    
    # Compute collocation scores
    new_freq_table = {}
    for k, v in freq_table.items():
        subj, act = k
        subj_total, act_total = subj_totals[subj], act_totals[act]
        othersubj_total, otheract_total = corp_size - subj_total, corp_size - act_total
        
        # Compute observed frequencies
        o11 = v
        o12 = subj_total - o11
        o21 = act_total - o11
        o22 = othersubj_total - o21

        if o11 < 0 or o12 < 0 or o21 < 0 or o22 < 0:
            print(k)
            print(o11, o12, o21, o22)
            print(subj_total, act_total)
            raise Exception('negative freq')

        # Compute expected frequencies
        contingency_table = {
            'o11': o11,
            'o12': o12,
            'o21': o21,
            'o22': o22
        }
        new_freq_table[k] = measures(**contingency_table)
    
    return new_freq_table



def dca(freq_table):
    """
    Distinctive Collexeme Analysis
    freq_table: dict. Format: {C1: {L1: freq, L2: freq, ...}, C2: {L1: freq, L2: freq, ...}}

    Contingency table:
             Lj     ~Lj
        C1   o11    o12
        C2   o21    o22

    References:
        Desagulier, G. (2017). Corpus Linguistics and Statistics with R. p213-221.
    """
    cnst_keys = list(freq_table.keys())
    C1 = cnst_keys[0]
    C2 = cnst_keys[1]

    words = set()
    freq_totals = {}
    for key in cnst_keys:
        freq_totals[key] = 0
        for w in freq_table[key]:
            words.add(w)
            freq_totals[key] += freq_table[key][w]
    
    # Compute collocation measures
    scores = {}
    for w in words:
        a = freq_table[C1].get(w, 0)
        b = freq_totals[C1] - a
        c = freq_table[C2].get(w, 0)
        d = freq_totals[C2] - c
        try:
            scores[w] = measures(o11=a, o12=b, o21=c, o22=d)
        except:
            print(a, b, c, d)
    
    print(f'Pos: attract to {C1}\nNeg: attract to {C2}')
    return scores #{'scores': scores, 'pos': C1}



def measures(o11, o12, o21, o22):
    """
    Compute a list of association measures from the contingency table.

    G2: 3.8415 (p < 0.05); 10.8276 (p < 0.01)
    """

    o1_ = o11 + o12
    o2_ = o21 + o22
    o_1 = o11 + o21
    o_2 = o12 + o22
    _, fisher_exact_pvalue = fisher_exact([[o11, o12], [o21, o22]])
    fisher_attract = -log(fisher_exact_pvalue)

    total = o1_ + o2_
    e11 = o1_ * o_1 / total
    e12 = o1_ * o_2 / total
    e21 = o2_ * o_1 / total
    e22 = o2_ * o_2 / total
    
    # Compute G2
    if o11 == 0: o11 = 0.00000000001
    try:
        t11 = o11*log(o11/e11) if o11 != 0 else 0
        t12 = o12*log(o12/e12) if o12 != 0 else 0
        t21 = o21*log(o21/e21) if o21 != 0 else 0
        t22 = o22*log(o22/e22) if o22 != 0 else 0
    except:
        print(o11, o12, o21, o22, e11, e12, e21, e22)
        raise Exception('math error')
    G2 = 2 * (t11 + t12 + t21 + t22)
    if o11 < e11: 
        G2 = -G2
        fisher_attract = -fisher_attract

    return {
        'freq': o11,
        'fisher_exact': fisher_attract,
        "G2": G2,
        'MI': log2(o11/e11),
        'MI3': log2(o11 ** 3 / e11),
        'MI_logf': log2(o11/e11) * log(o11 + 1),
        't': (o11 - e11) / sqrt(e11),
        'Dice': 2 * e11 / (o1_ + o_1),
        "deltaP21": o11/o1_ - o21/o2_,
        "deltaP12": o11/o_1 - o21/o_2
    }


def rank_collo(collo_measures, nodeword=None, nodeword_idx=0, sort_by='G2', reverse=True, freq_cutoff=None):
    if freq_cutoff is None: freq_cutoff = 0
    out = sorted( ((k, v[sort_by], v['freq']) for k, v in collo_measures.items() if v['freq'] >= freq_cutoff),
    key=lambda x: x[1], reverse=reverse)

    if nodeword:
        return [ x for x in out if x[0][nodeword_idx] == nodeword.strip() ]
    else:
        return out