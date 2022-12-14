import dbm.gnu

import pprint as pp

# what is the file0 folders inside outRust-xxx?
# total: 381 possible mutants
# outRust-n, with n from 1 to 381. Does outRust-n kill mutation n?

"""
class MutationResult(Enum):
    TIMEOUT_KILLED = 1
    PANIC_KILLED = 2
    BINARY_DIFFERENCE_KILLED = 3
    OUTPUT_DIFFERENCE_KILLED = 4
"""

if __name__ == '__main__':
    db = dbm.gnu.open('./my_store')
    
    mutant_killed = {}
    for k in db.keys():
        # mapping of { mutant_number: kill_reason }
        # so [3]: {100: MutationResult.BINARY_DIFFERENCE_KILLED}
        # means that the 3rd file killed mutant number 100, in fashion BINARY_DIFFERENCE 
        mutant_killed[k.decode('ascii')] = db[k].decode('ascii')

    pp.pprint(mutant_killed)
    print("dict keys:", len(mutant_killed.keys()))

    db.close()