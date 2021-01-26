'''
compute election results for the democratit (diversitySPAV)
argv[1] - candidates file (2nd line on is "cID, {f, m}, name")
argv[2] - voters file (2nd line on is "vID, cID")
'''
import sys
import operator


# print things
verbose = False


'''
return (C, V); C = {cID: [{f, m}, name}}; V = {vID: [cID]}
'''
def read_data(Cfile, Vfile):
    # populate C
    C = {} # will be {cID: [{f, m}, name]}
    with open(Cfile) as f:
        content = f.readlines()[1:] # ignore first line
        content = [[x.strip().split(',')[0], x.strip().split(',')[1:]] for x in content] # csv
        C = dict(content) # {cID: [{f, m}, name]}
    # populate V
    V = {} # will be {vID: [cID]}
    with open(Vfile) as f:
        content = f.readlines()[1:] # ignore first line
        content = [x.strip().split(',') for x in content] # csv
        for l in content: # l[0] is vID, initalize to []
            V[l[0]] = []
        for l in content:
            V[l[0]].append(l[1]) # add the approval to the list for vID
        for v in V: # remove duplicates
            V[v] = list(set(V[v]))
    return (C, V)


'''
return (C, V); C = {cID: [{f, m}, name}}; V = {vID: [cID]}
'''
def read_new_data(Cfile, Vfile):
    # populate C
    C = {} # will be {cID: [{f, m}, name]}
    with open(Cfile) as f:
        content = f.readlines()[1:] # ignore first line
        content = [[x.strip().split(',')[0], x.strip().split(',')[1:]] for x in content] # csv
        C = dict(content) # {cID: [{f, m}, name]}
    # populate V
    V = {} # will be {vID: [cID]}
    vID = 1
    with open(Vfile) as f:
        content = f.readlines()[:] # do not ignore first line
        content = [x.strip().replace('"', '').split(',') for x in content] # csv
        for l in content: # l[0] is vID, initalize to []
            V[vID] = []
            for cID in l:
              V[vID].append(cID) # add the approval to the list for vID
            vID += 1
        for v in V: # remove duplicates
            V[v] = list(set(V[v]))
    return (C, V)


'''
check if the next iteration must be female (to preclude male strict majority)
S is a partial result
C is the complete candidates gender map
'''
def must_be_female(S, C):
    if len(S) < 4: # consider the 'ahuz hasima'
        return False
    # array of gender of candidates sofar selected
    genderS = list(map(lambda x: C[x][0], S))
    # number of F/M so far selected
    Fsofar = len(list(filter(lambda x: x == 'f', genderS)))
    Msofar = len(list(filter(lambda x: x == 'm', genderS)))
    # avoid M *strict* majority if next selecting M (hence the +1)
    return Msofar + 1 > Fsofar


'''
compute diversity-aware SPAV (given C and V, return [ranked] list)
'''
def SPAV(Coriginal, V):
    # the solution array, initialized empty
    S = []
    # the scores of the winners (for verbose)
    winnerScores = []
    # the remaining candidates (as we will remove each selected candidate)
    C = dict(Coriginal)
    # the inverse weights array (i.e, instead of 1/k, we put k)
    weightInverse = {}
    for v in V: # initialze all voters to have weight 1
        weightInverse[v] = 1
    # main loop (in each iteration, we will append a candidate)
    while len(S) < len(Coriginal): # |C|-many iterations, or halt when not possible due to diversity
        # score = {cID: score}
        score = {}
        for c in C:
            score[c] = 0 # initialize all scores to 0
        # take each v into account (by its weight)
        for v in V:
            for c in V[v]:
                # add the weight of v to each c in v's ballot
                if c in C:
                    score[c] += 1 / weightInverse[v] # add the inverse weight to the chosen cID by the vID
        # score holds the score of each candidate
        relevantScore = score # filter score to F if diversity requires, otherwise score
        if must_be_female(S, Coriginal):
            relevantScore = {k: score[k] for k in score if C[k][0] == 'f'}
        # populate next winner
        if not len(relevantScore): # if filtered to F perhaps no more F candidates
            while len(S) < len(Coriginal): # simply add -1 dummies to finish loop (will be removed)
                S.append(-1)
            continue
        # make the world go round
        relevantScore = {k: round(relevantScore[k], 5) for k in relevantScore}
        if verbose:
            print('\n--- iteration number %d'%(len(S) + 1)) # print iteration number
        if verbose:
            print('+++ scores =>', {k: round(score[k], 5) for k in score}) # prettyprint score
        # hc wins the iteration (the cID with the maximum score)
        hc = max(relevantScore.items(), key=operator.itemgetter(1))[0]
        # print the winner (say if we actually did tie breaking; as hc returns just one)
        allWinners = {k: v for k, v in relevantScore.items() if relevantScore[k] == relevantScore[hc]}
        if len(allWinners) > 1:
            # say that we have a tie
            if verbose:
                print('>>> tie: %s'%({k : C[k][1] for k, v in allWinners.items()}))
            # break ties lexicographically
            hc = min({k: C[k][1] for k, v in allWinners.items()}.items(), key=operator.itemgetter(1))[0]
        if verbose:
            print('*** winner => %s'%(hc))
        winnerScores.append([hc, relevantScore[hc]])
        # put hc in and do not consider it anymore in C and in V
        S.append(hc)
        C.pop(hc)
        for v in V:
            if hc in V[v]:
                V[v].remove(hc)
                # reweight according to harmonic series
                # (if this is removed than we do approval!)
                weightInverse[v] += 1
    if verbose:
        print('\n\n\n*** WinnerScores:\n', winnerScores, '\n\n\n')
    return (list(filter(lambda x: x != -1, S)), winnerScores) # remove the -1 dummies


'''
save democracy
'''
def main():
    # read data and print
    (C, V) = read_data(sys.argv[1], sys.argv[2])
    if verbose:
        print('Candidate genders:\n\t', C)
        print('Voter ballots    :\n\t', V)
    # compute results and print
    (S, winnerScores) = SPAV(C, V)
    if verbose:
        print('\nElection results:\n\t', S, '\n')
    for i in range(len(S)):
        if verbose:
            print('%2d %s (%d)'%(i + 1, C[S[i]][1], winnerScores[i][1]))
        else:
            print('%2d %s'%(i + 1, C[S[i]][1],))
main()
