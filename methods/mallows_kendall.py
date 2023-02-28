import numpy as np
import itertools as it
from scipy import optimize

# NOTE: Everything related to alpha to beta may be removed because it is related to partial permutations.
def kendall_max_dist(n):
    return int(n * (n - 1) / 2)

# FIXME: Optimize this function
def kendallTau(A, B=None):
    # if any partial is B
    if B is None : B = list(range(len(A)))
    n = len(A)
    # FIXME: Since n is typically fixed, this could be done once outside this function.
    pairs = it.combinations(range(n), 2)
    distance = 0
    for x, y in pairs:
        a = A[x] - A[y]
        try:
            b = B[x] - B[y]
        except:
            print("ERROR kendallTau, check b",A, B, x, y)
        # print(b,a,b,A, B, x, y,a * b < 0)
        if (a * b < 0):
            distance += 1
    return distance


def find_phi(n, dmin, dmax):
    imin, imax = 0.0, 1.0
    iterat = 0
    while iterat < 500:
        med = imin + (imax - imin) / 2
        d = expected_dist_MM(n, theta=phi2theta(med))
        if d < dmax and d > dmin: return med
        elif d < dmin : imin = med
        elif d > dmax : imax = med
        iterat += 1
    assert False


def compose(s, p):
    return np.asarray(s[p])

def inverse(s):
    return np.argsort(s)

def borda(rankings):
    # Ranks breaking ties randomly.
    consensus = inverse(inverse(rankings.sum(axis=0)))
    return consensus

def check_theta_phi(theta, phi):
    assert phi is not None or theta is not None, "check_theta_phi: you need to provide either theta or phi"
    if phi is None:
        # In our case: theta and phi is always a number.
        if type(theta)!=list:
            phi = theta2phi(theta)
        else:
            # FIXME: we do not need this because it is already a numpy operation so it will vectorize.
            phi = [theta2phi(t) for t in theta]
    if theta is None:
        if type(phi)!=list:
            theta = phi2theta(phi)
        else:
            # FIXME: we do not need this because it is already a numpy operation so it will vectorize.
            theta = [phi2theta(p) for p in phi]
    return theta, phi

def expected_dist_MM(n, theta=None, phi=None):
    theta, phi = check_theta_phi(theta, phi)
    # FIXME: It is faster:
    # j = np.arange(1, n + 1)
    # exp_j_theta = np.exp(-j * theta)
    # exp_dist = (n * n.exp(-theta) / (1 - n.exp(-theta))) - np.sum(j * exp_j_theta / (1 - exp_j_theta)
    expected_dist = n * np.exp(-theta) / (1 - np.exp(-theta)) - np.sum([j * np.exp(-j*theta) / (1 - np.exp(-j*theta))  for j in range(1,n+1)])
    return expected_dist

def prob(n, theta, dist):
    # FIXME: You do not need the for-loop
    psi = np.array([(1 - np.exp(( - n + i )*(theta)))/(1 - np.exp( -theta)) for i in range(n-1)])
    psi = np.prod(psi)
    return np.exp(-theta*dist) / psi

def fit_MM(rankings, s0=None): #returns sigma, phi
    m, n = rankings.shape
    if s0 is None:
        s0 = borda(rankings)
    dist_avg = np.mean([kendallTau(s0, perm) for perm in rankings])
    s0, phi = fit_MM_phi(n, dist_avg)
    return s0, phi

def fit_MM_phi(n, dist_avg): #returns sigma, phi
    try:
        theta = optimize.newton(mle_theta_mm_f, 0.01, fprime=mle_theta_mm_fdev, args=(n, dist_avg), tol=1.48e-08, maxiter=500, fprime2=None)
    except:
        if dist_avg == 0.0:
            # FIXME: Why 5?
            return s0, np.exp(-5)#=phi
        print("error. fit_mm. dist_avg=",dist_avg, dist_avg == 0.0)
        print(rankings)
        print(s0)
        raise
    # theta = - np.log(phi)
    # FIXME: return theta2phi(theta)
    return np.exp(-theta)

def theta2phi(theta):
    return np.exp(-theta)

def phi2theta(phi):
    return -np.log(phi)

def mle_theta_mm_f(theta, n, dist_avg):
    aux = 0
    for j in range(1,n):
        k = n - j + 1
        aux += (k * np.exp(-theta * k))/(1 - np.exp(-theta * k))
    aux2 = (n-1) / (np.exp( theta ) - 1) - dist_avg
    return aux2 - aux

def mle_theta_mm_fdev(theta, n, dist_avg):
    aux = 0
    for j in range(1,n):
        k = n - j + 1
        aux += (k * k * np.exp( -theta * k ))/pow((1 - np.exp(-theta * k)) , 2 )
    aux2 = (-n + 1) * np.exp( theta ) / pow((np.exp( theta ) - 1) , 2 )
    # print(theta)
    return aux2 + aux

def likelihood_mm(perms, s0, theta):
    m, n = perms.shape
    psi = 1.0 / np.prod([(1-np.exp(-theta*j))/(1-np.exp(-theta)) for j in range(2,n+1)])
    probs = np.array([np.log(np.exp(-kendallTau(s0, perm)*theta)/psi) for perm in perms])
    # print(probs,m,n)
    return probs.sum()

def samplingMM(m,n,theta=None, phi=None, k=None):
    # k return partial orderings
    theta, phi = check_theta_phi(theta, phi)
    if k == n:
        k = None
    return samplingGMM(m, [theta] * (n-1), topk = k)

def samplingGMM(m,theta, topk=None):
    #  returns RANKINGS!!!!!!!*****
    n = len(theta)+1
    if topk is None or topk == n: k = n-1
    else: k = topk
    psi = [(1 - np.exp(( - n + i )*(theta[ i ])))/(1 - np.exp( -theta[i])) for i in range(k)]
    vprobs = np.zeros((n,n))
    for j in range(k): #range(n-1):
        vprobs[j][0] = 1.0/psi[j]
        for r in range(1,n-j):
            vprobs[j][r] = np.exp( -theta[j] * r ) / psi[j]#vprobs[j][ r - 1 ] + np.exp( -theta[j] * r ) / psi[j]
    sample = []
    vs = []
    for samp in range(m):
        v = [np.random.choice(n,p=vprobs[i,:]) for i in range(k)] # v = [np.random.choice(n,p=vprobs[i,:]/np.sum(vprobs[i,:])) for i in range(k)]
        #vs.append(v)
        #print(v, np.sum(v))
        # print(v, topk)
        if topk is None: v += [0] # la fun discordancesToPermut necesita, len(v)==n
        ranking = v2ranking(v, n)#discordancesToPermut(v,list(range(n)))
        # if topk is not None :
        #     ranking = np.concatenate([ranking, np.array([np.nan]*(n-topk))])
        sample.append(ranking)
    return sample

def ranking2v(perm):
    n = len(perm)
    return np.array([np.sum([perm[i]<perm[j] for i in range(j+1,n)], dtype=int) for j in range(n)])

def ranking2vinv(perm):
    inv = inverse(perm)
    n = len(perm)
    return np.array([np.sum([inv[i]<inv[j] for i in range(j+1,n)], dtype=int) for j in range(n)])

def v2ranking(v, n): ##len(v)==n, last item must be 0
    # n = len(v)
    rem = list(range(n))
    rank = np.array([np.nan]*n)# np.zeros(n,dtype=np.int)
    # print(v,rem,rank)
    for i in range(len(v)):
        # print(i,v[i], rem)
        rank[i] = rem[v[i]]
        rem.pop(v[i])
    return rank#[i+1 for i in permut];


def discordancesToPermut(indCode, refer):
    print("warning. discordancesToPermut is deprecated. Use function v2ranking")
    return v2ranking(indCode)
    # returns rNKING
    # n = len(indCode)
    # rem = refer[:] #[i for i in refer]
    # ordering = np.zeros(n,dtype=np.int)
    # for i in range(n):
    #     ordering[i] = rem[indCode[i]]
    #     rem.pop(indCode[i])
    # return ordering#[i+1 for i in permut];

def partial_ord2partial_rank(pord, n, k, type="beta"):#NO
    if type == "gamma": val = -1
    elif type == "beta": val = k

    # pord is a collection of partial orderings, each of which (1) has len n (2) np.nans for the unspecified places (3) is np.array
    #input partial ordering of the first k items. The first k positions have vals [0,n-1]
    #output partial ranking of the first k ranks. There are k positions have vals [0,k-1]. The rest have val=k (so the kendall dist can be compared)
    prank = []
    # n = len(pord[0])
    # for perm in pord:
    res = np.array([val]*n)
    for i,j in enumerate(pord[~np.isnan(pord)]):
        res[int(j)]=i
    # prank.append(res)
    return np.array(res)

# m'/M segun wolfram -((j - n) e^(j x))/(e^(n x) - e^(j x)) - (j e^x - j - n e^x + n + e^x)/(e^x - 1)
#
def Ewolfram(n,j,x):#NO
    return (-((j - n) * np.exp(j * x))/(np.exp(n* x) - np.exp(j *x)) - (j* np.exp(x) - j - n *np.exp(x) + n + np.exp(x))/(np.exp(x) - 1))
#(E^(x + 2 j x) + E^(x + 2 n x) - E^((j + n) x) (j - n)^2 - E^((2 + j + n) x) (j - n)^2 + 2 E^((1 + j + n) x) (-1 + j^2 - 2 j n + n^2))/((-1 + E^x)^2 (-E^(j x) + E^(n x))^2)
def Vwolfram(n,j,x):#NO
    numer = (np.exp(x + 2* j *x) + np.exp(x + 2* n *x) - np.exp((j + n) *x)*(j - n)**2 - np.exp((2+j+n)* x)* (j - n)**2 + 2 *np.exp((1 + j + n) *x)*(-1 + j**2 - 2* j *n + n**2))
    denom = ((-1 + np.exp(x))**2 *(-np.exp(j *x) + np.exp(n* x))**2)
    return numer/denom


## number of perms at each dist
def num_perms_at_dist(n):
    sk = np.zeros((n+1,int(n*(n-1)/2+1)))
    for i in range(n+1):
        sk[i,0] = 1
    for i in range(1,1+n):
        for j in range(1,int(i*(i-1)/2+1)):
            if j - i >= 0 :
                sk[i,j] = sk[i,j-1]+ sk[i-1,j] - sk[i-1,j-i]
            else:
                sk[i,j] = sk[i,j-1]+ sk[i-1,j]
    return sk.astype(np.uint64)

## random permutations at distance
def random_perm_at_dist(n, dist, sk):
    # param sk is the results of the function num_perms_at_dist(n)
    i = 0
    probs = np.zeros(n+1)
    v = np.zeros(n,dtype=int)
    while i<n and dist > 0 :
        rest_max_dist = (n - i - 1 ) * ( n - i - 2 ) / 2
        if rest_max_dist  >= dist:
            probs[0] = sk[n-i-1,dist]
        else:
            probs[0] = 0
        mi = min(dist + 1 , n - i )
        for j in range(1,mi):
            if rest_max_dist + j >= dist: probs[j] = sk[n-i-1, dist-j]
            else: probs[ j ] = 0
        v[i] = np.random.choice(mi,1,p=probs[:mi]/probs[:mi].sum())
        dist -= v[i]
        i += 1
    return v2ranking(v)


def u_phi(sample, s0, ws):
    m, n = np.asarray(sample).shape
    #if s0 is None: s0 = np.argsort(np.argsort(rankings.sum(axis=0))) #borda
    dist_avg = np.asarray([kendallTau(perm, s0) for perm in sample]*ws).sum()/ws.sum() #np.mean(np.array([kendallTau(s0, perm) for perm in rankings]))
    try:
        # FIXME: This is the same as fit_MM, no?
        theta = optimize.newton(mle_theta_mm_f, 0.01, fprime=mle_theta_mm_fdev, args=(n, dist_avg), tol=1.48e-08, maxiter=500, fprime2=None)
    except:
        #if dist_avg == 0.0: return s0, np.exp(-5)#=phi
        print("error. fit_mm. dist_avg=",dist_avg, dist_avg == 0.0)
        print(s0)
        raise
    if theta < 0:
        theta = 0.001
    return theta2phi(theta)

def uborda(sample, ws):
    return borda(sample * ws[:, None])

