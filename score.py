import os

similar = {}

def score(matches, ground_truth, num_samples):
    define_similar_category()
    i = 0
    score = 0
    idl_score = 0

    num_sample = len(os.listdir(ground_truth[:ground_truth.rindex('/')]))
    print(num_sample)
    for match in matches:
        i += 1
        idl_rank = ideal_rank(i, num_samples)
        
        rank = 0
        if same_file(match[0], ground_truth):
            rank = 3
        elif same_path(match[0], ground_truth):
            rank = 2
        elif similar_category(match[0], ground_truth):
            rank = 1
        else:
            rank = 0
#            print(match[0], ground_truth)
        
        score += dcg_score(rank, i)
        idl_score += dcg_score(idl_rank, i)
    if(idl_score == 0):
        return 0
    return (score/idl_score)
       
def same_file(path1, path2):
    path1_sp = path1.strip("./")
    path2_sp = path2.strip("./")
    return (path1_sp==path2_sp)

def same_path(path1, path2):
    path1_sp = path1.strip("./").split('/')
    path2_sp = path2.strip("./").split('/')
    for i in range(min(len(path1_sp)-1, len(path2_sp)-1)):
        #print(path1_sp[i], "\t", path2_sp[i])
        if path1_sp[i] != path2_sp[i]:
            return False
    return True
 
def similar_category(path1, path2):
    global similar
    path1_sp = path1.strip("./").split('/')
    path2_sp = path2.strip("./").split('/')
    for i in range(min(len(path1_sp)-2, len(path2_sp)-2)):
        if path1_sp[i] != path2_sp[i]:
            return False
    subclass1 = path1_sp[len(path1_sp)-2]
    subclass2 = path2_sp[len(path2_sp)-2]

    if subclass2 not in similar[subclass1]:
        return False
    
    return True
      
def define_similar_category():
    global similar
    similar['Bearings'] = ['Bearings','O_Rings', 'Grommets']
    similar['Bolts'] = ['Bolts', 'Socket_Head_Screws']
    similar['Brackets'] = ['Brackets']
    similar['Bushing'] = ['Bushing', 'Thumb_Screws', 'Pipe_Fittings']
    similar['Bushing_Damping_Liners'] = ['Bushing_Damping_Liners']
    similar['Collets'] = ['Collets', 'Slotted_Flat_Head_Screws']
    similar['Gasket'] = ['Gasket']
    similar['Grommets'] = ['Bearings','O_Rings', 'Grommets']
    similar['HeadlessScrews'] = ['HeadlessScrews']
    similar['Hex_Head_Screws'] = ['Hex_Head_Screws']
    similar['Keyway_Shaft'] = ['Keyway_Shaft', 'Rotary_Shaft']
    similar['Machine_Key'] = ['Machine_Key']
    similar['Nuts'] = ['Nuts']
    similar['O_Rings'] = ['O_Rings', 'Bearings', 'Grommets']
    similar['Pipe_Fittings'] = ['Pipe_Fittings', 'Bushing', 'Thumb_Screws']
    similar['Pipe_Joints'] = ['Pipe_Joints']
    similar['Pipes'] = ['Pipes']
    similar['Rollers'] = ['Rollers']
    similar['Rotary_Shaft'] = ['Rotary_Shaft', 'Keyway_Shaft']
    similar['Shaft_Collar'] = ['Shaft_Collar']
    similar['Slotted_Flat_Head_Screws'] = ['Slotted_Flat_Head_Screws', 'Collets']
    similar['Socket_Head_Screws'] = ['Socket_Head_Screws', 'Bolts']
    similar['Thumb_Screws'] = ['Thumb_Screws', 'Bushing', 'Pipe_Fittings']
    similar['Washers'] = ['Washers']

def ideal_rank(i, num):
    if(i == 1):
        return 3
    elif(i < num):
        return 2
    return 0

    #NCDG_LOG = max(1,log2(i))
NCDG_LOG = [1,1,1.584962501,2,2.321928095,2.584962501,2.807354922,3,3.169925001,3.321928095,3.459431619,3.584962501,3.700439718,3.807354922,3.906890596,4,4.087462841,4.169925001,4.247927513,4.321928095,4.392317423,4.459431619,4.523561956,4.584962501,4.64385619]
def dcg_score(rank, i):
    discount = NCDG_LOG[-1]  
    if(i>0 and i < len(NCDG_LOG)):
        discount = NCDG_LOG[i]
    return (rank/discount)

def bash_same_path(a,b):
    if same_path(a,b):
        print(1)
    else:
        print(0)
