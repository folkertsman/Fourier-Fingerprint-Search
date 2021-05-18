import helper as _hp
import fingerprint as _fp
import plyvel
import math
class Database:
    """
    Key-Value storage.

    Schema:
    1) Signatures DB:
        +-------------------+-------------------+
        | Key               | Value             |
        +-------------------+-------------------+
        | signature_hash    | [ filename_hash ] |
        +-------------------+-------------------+
    2) Anchors DB:
        +-------------------+-------------------+
        | Key               | Value             |
        +-------------------+-------------------+
        | signature_hash    | [ anchor_hash ]   |
        +-------------------+-------------------+
    3) Filenames DB:
        // maybe change the key to filecontents hash
        +-------------------+-------------------+
        | Key               | Value             |
        +-------------------+-------------------+
        | filename_hash     | filename          |
        +-------------------+-------------------+

    Neighborhoods:
    +-----------+-------------------------------+
    | Key       | Value                         |
    +-----------+-------------------------------+
    | Anchor_id | [ signature_from_anchor_id ]  |
    +-----------+-------------------------------+
    """


    def __init__(self, database_name):
        """
        Open database_name database. Create it if does not exist.
        """
        self.database_name = database_name
        self.db = plyvel.DB(database_name, create_if_missing=True)
        # Generate prefixed databases
        self.signatures_db = self.db.prefixed_db(b'signatures')
        self.anchors_db = self.db.prefixed_db(b'anchors')
        self.filenames_db = self.db.prefixed_db(b'filenames')
        self.invertsig_db = self.db.prefixed_db(b'invert_sig')


    def close_db(self):
        """
        Close the database.
        """
        self.db.close()


    def add_signatures(self, neighborhoods, filename):
        """
        Add list of signatures to database. Each signature points to a list of file names. Refer to schema.
        """
        # Generate SHA1 hash of filename
        filename_hash = _hp.sha1_hash(filename.encode())
        # Store filename hash in the filenames prefixed database
        self.filenames_db.put(filename_hash, filename.encode())
        # Iterate over all signatures of the file
        for _, hashes_lst in neighborhoods.items():
            # Compute the anchor hash based on the signatures it has
            anchor_hash = _hp.sha1_hash_lst(hashes_lst)
            self.invertsig_db.put(filename_hash, hashes_lst)
            for sig in hashes_lst:
                print(len(sig))
                # Get the list of filename hashes
                filehashes_lst = self.signatures_db.get(sig)
                # If this is the first occurrence of this hash
                if filehashes_lst is None:
                    self.signatures_db.put(sig, filename_hash)
                    self.anchors_db.put(sig, anchor_hash)
                else: # If we have seen this hash previously, check if it's from a different file
                    self.signatures_db.put(sig, filehashes_lst+filename_hash)
                    self.anchors_db.put(sig, self.anchors_db.get(sig) + anchor_hash)


def search_signatures(self, neighborhoods):
        """
        Search in database given a list of signatures. Return top NUMBER_OF_MATCHES mathced files.
        """
        matched_files = {}
        total_signatures = 0
        # Iterate over all signatures of the file
        for _, hashes_lst in neighborhoods.items():
            for sig in hashes_lst:
                filehashes_lst = self.signatures_db.get(sig)
                if filehashes_lst is None:
                    continue
                anchor_hashes_lst = self.anchors_db.get(sig)
                # Get the list of filenames. Split by HASH_DIGEST_SIZE bytes.
                filehashes_lst = [ filehashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(filehashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # Get the list of anchor hashes that . Split by HASH_DIGEST_SIZE bytes.
                anchor_hashes_lst = [ anchor_hashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(anchor_hashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # for filename_hash in filehashes_lst:
                for i in range(len(filehashes_lst)):
                    filename_hash = filehashes_lst[i]
                    filename = self.filenames_db.get(filename_hash).decode("utf-8")
                    anchor_hash = anchor_hashes_lst[i]
                    # If this is the first hash for that filename create a new inner dict
                    if filename not in matched_files:
                        matched_files[filename] = {}
                        matched_files[filename]['total'] = 1
                    # Count occurences
                    if anchor_hash not in matched_files[filename]:
                        matched_files[filename][anchor_hash] = []
                        matched_files[filename]['anchors_matched'] = 0
                    matched_files[filename][anchor_hash].append(sig)
                    matched_files[filename]['total'] += 1
                total_signatures += 1
        # Check how many signatures and neighborhoods matched
        anchor_matches = {}
        signatures_matches = {}
        signatures_dict = {}
        for filename, anchors in matched_files.items():
            signatures_dict[filename] = {}
            signatures_dict[filename]['total'] = matched_files[filename]['total']
            # for each anchor and the hashes in its neighborhood
            for anch, sigs in anchors.items():
                # Skip the counters
                if anch == 'anchors_matched' or anch == 'total':
                    continue
                if len(sigs) >= _hp.MIN_SIGNATURES_TO_MATCH:
                    matched_files[filename]['anchors_matched'] += 1
                for s in sigs:
                    signatures_dict[filename][s] = 1
            anchor_matches[filename] = anchors['anchors_matched'] / len(neighborhoods)
            signatures_matches[filename] = (len(signatures_dict[filename]) - 2) / total_signatures
        # Find top-K matches with 2 different criteria.
        anchor_matches = sorted(anchor_matches.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
        signatures_matches = sorted(signatures_matches.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
        # return lists of tuples
        _hp.normalize(anchor_matches)
        _hp.normalize(signatures_matches)
        return anchor_matches, signatures_matches


def destroy_db(database_name):
    """
    Delete database_name database.
    """
    print('Database destroyed.\n')
    plyvel.destroy_db(database_name)

##################### Test #################################
def joint_avg_search_signatures(self, neighborhood):
    anchorm, signaturem = search_signatures(self, neighborhood)

    combined_dict = {}
    for fi, score in anchorm:
        combined_dict[fi] = score
    for fi, score in signaturem:
        if fi not in combined_dict:
            combined_dict[fi] = score
        else:
            combined_dict[fi] += score
            combined_dict[fi] /= 2
        
        
    matches = sorted(combined_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
    return matches, matches


def weighted_search_signatures(self, neighborhood):
        """
        Search in database given a list of signatures. Return top NUMBER_OF_MATCHES mathced files.
        """
        matched_files = {}
        total_signatures = 0
        weighted_signatures = {} 
        weighted_sig_total = 0
        # Iterate over all signatures of the file
        for _, hashes_lst in neighborhood.items():
            for sig in hashes_lst:
                filehashes_lst = self.signatures_db.get(sig)
                if filehashes_lst is None:
                    continue
                anchor_hashes_lst = self.anchors_db.get(sig)
                # Get the list of filenames. Split by HASH_DIGEST_SIZE bytes.
                filehashes_lst = [ filehashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(filehashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # Get the list of anchor hashes that . Split by HASH_DIGEST_SIZE bytes.
                anchor_hashes_lst = [ anchor_hashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(anchor_hashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # for filename_hash in filehashes_lst:
                for i in range(len(filehashes_lst)):
                    filename_hash = filehashes_lst[i]
                    filename = self.filenames_db.get(filename_hash).decode("utf-8")
                    anchor_hash = anchor_hashes_lst[i]
                    # If this is the first hash for that filename create a new inner dict
                    if filename not in matched_files:
                        matched_files[filename] = {}
                        matched_files[filename]['total'] = 1
                    # Count occurences
                    if anchor_hash not in matched_files[filename]:
                        matched_files[filename][anchor_hash] = []
                        matched_files[filename]['anchors_matched'] = 0
                    matched_files[filename][anchor_hash].append(sig)
                    matched_files[filename]['total'] += 1
                total_signatures += 1
                weighted_signatures[sig] = 1/len(filehashes_lst)
                weighted_sig_total += 1/len(filehashes_lst)
                #print(1/len(filehashes_lst))
        # Check how many signatures and neighborhoods matched
        anchor_matches = {}
        signatures_matches = {}
        signatures_dict = {}
        for filename, anchors in matched_files.items():
            signatures_dict[filename] = {}
            signatures_dict[filename]['total'] = matched_files[filename]['total']
            sig_total = 0
            # for each anchor and the hashes in its neighborhood
            for anch, sigs in anchors.items():
                # Skip the counters
                if anch == 'anchors_matched' or anch == 'total':
                    continue
                if len(sigs) >= _hp.MIN_SIGNATURES_TO_MATCH:
                    matched_files[filename]['anchors_matched'] += 1
                for s in sigs:
                    signatures_dict[filename][s] = 1
                    sig_total += float(weighted_signatures[s])
            anchor_matches[filename] = anchors['anchors_matched'] / len(neighborhood) 
            #signatures_matches[filename] = (len(signatures_dict[filename]) - 2) / total_signatures
            signatures_matches[filename] = sig_total / weighted_sig_total #(signatures_dict[filename]['weight'] - 2) / weighted_signatures
        # Find top-K matches with 2 different criteria.
        anchor_matches = sorted(anchor_matches.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
        signatures_matches = sorted(signatures_matches.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
        # return lists of tuples
        _hp.normalize(anchor_matches)
         #_hp.normalize(signatures_matches)
            
        return anchor_matches, signatures_matches

def joint_mult_search_signatures(self, neighborhood):
    anchorm, signaturem = search_signatures(self, neighborhood)

    combined_dict = {}
    for fi, score in anchorm:
        combined_dict[fi] = score
    for fi, score in signaturem:
        if fi not in combined_dict:
            combined_dict[fi] = score
        else:
            combined_dict[fi] *= score
            combined_dict[fi] = math.sqrt(combined_dict[fi])
        
        
    matches = sorted(combined_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
    return matches, matches


def feedback_search_signatures1(self, neighborhood):
    
    anch, signa = search_signatures(self, neighborhood)

    anch_dict = {}
    sig_dict = {}
    #iterate through code
    for fi, score in anch:
        anch_dict[fi] = score
    wgt_scale = 1.5
    total_anch_wgt = 1
    for fi, score in anch:
        wgt = score/wgt_scale
        if wgt < 0.01:
            break
        new_neigh = _fp.fingerprint(fi, _hp.NUM_OF_SLICES, _hp.NUM_OF_PEAKS, _hp.FAN_VALUE, _hp.ROTATE, _hp.INTERP, _hp.STAR_ROTATE)
        new_anch, new_sig = search_signatures(self, new_neigh)
        for nfi, nsc in new_anch:
            if nfi not in anch_dict:
                anch_dict[nfi] = wgt*nsc
            else:
                anch_dict[nfi] += wgt*nsc
        total_anch_wgt += wgt
        wgt_scale+=0.1

    for fi, score in signa:
        sig_dict[fi] = score
    wgt_scale=1.5
    total_sig_wgt = 1
    for fi, score in signa:
        wgt = score/wgt_scale
        if wgt < 0.01:
            break
        new_neigh = _fp.fingerprint(fi, _hp.NUM_OF_SLICES, _hp.NUM_OF_PEAKS, _hp.FAN_VALUE, _hp.ROTATE, _hp.INTERP, _hp.STAR_ROTATE)
        new_anch, new_sig = search_signatures(self, new_neigh)
        for nfi, nsc in new_sig:
            if nfi not in sig_dict:
                sig_dict[nfi] = wgt*nsc
            else:
                sig_dict[nfi] += wgt*nsc
        total_sig_wgt += wgt
        wgt_scale+=0.1

    for fi in anch_dict:
        anch_dict[fi] /= total_anch_wgt
    for fi in sig_dict:
        sig_dict[fi] /= total_sig_wgt

    #now sort
    anch = sorted(anch_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
    signa = sorted(sig_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]

    return anch, signa

def joint_max_search_signatures(self, neighborhood):
    anchorm, signaturem = search_signatures(self, neighborhood)

    combined_dict = {}
    for fi, score in anchorm:
        combined_dict[fi] = score
    for fi, score in signaturem:
        if fi not in combined_dict:
            combined_dict[fi] = score
        elif score > combined_dict[fi]:
            combined_dict[fi] = score


    matches = sorted(combined_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
    return matches, matches
def joint_min_search_signatures(self, neighborhood):
    anchorm, signaturem = search_signatures(self, neighborhood)

    combined_dict = {}
    for fi, score in anchorm:
        combined_dict[fi] = score
    for fi, score in signaturem:
        if fi not in combined_dict:
            combined_dict[fi] = score
        elif score < combined_dict[fi]:
            combined_dict[fi] = score


    matches = sorted(combined_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
    return matches, matches



def feedback_search_signatures2(self, neighborhood):
        """
        Search in database given a list of signatures. Return top NUMBER_OF_MATCHES mathced files.
        """
        matched_files = {}
        total_signatures = 0
        weighted_signatures = {} 
        weighted_total = 0
        feedback_sig = []
        # Iterate over all signatures of the file
        for _, hashes_lst in neighborhood.items():
            for sig in hashes_lst:
                filehashes_lst = self.signatures_db.get(sig)
                if filehashes_lst is None:
                    continue
                anchor_hashes_lst = self.anchors_db.get(sig)
                # Get the list of filenames. Split by HASH_DIGEST_SIZE bytes.
                filehashes_lst = [ filehashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(filehashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # Get the list of anchor hashes that . Split by HASH_DIGEST_SIZE bytes.
                anchor_hashes_lst = [ anchor_hashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(anchor_hashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # for filename_hash in filehashes_lst:
                for i in range(len(filehashes_lst)):
                    filename_hash = filehashes_lst[i]
                    filename = self.filenames_db.get(filename_hash).decode("utf-8")
                    anchor_hash = anchor_hashes_lst[i]
                    # If this is the first hash for that filename create a new inner dict
                    if filename not in matched_files:
                        matched_files[filename] = {}
                        matched_files[filename]['total'] = 1
                    # Count occurences
                    if anchor_hash not in matched_files[filename]:
                        matched_files[filename][anchor_hash] = []
                        matched_files[filename]['anchors_matched'] = 0
                    matched_files[filename][anchor_hash].append(sig)
                    matched_files[filename]['total'] += 1
                total_signatures += 1

        # Check how many signatures and neighborhoods matched
        anchor_matches = {}
        signatures_matches = {}
        signatures_dict = {}
        for filename, anchors in matched_files.items():
            signatures_dict[filename] = {}
            signatures_dict[filename]['total'] = matched_files[filename]['total']
            sig_total = 0
            # for each anchor and the hashes in its neighborhood
            for anch, sigs in anchors.items():
                # Skip the counters
                if anch == 'anchors_matched' or anch == 'total':
                    continue
                if len(sigs) >= _hp.MIN_SIGNATURES_TO_MATCH:
                    matched_files[filename]['anchors_matched'] += 1
                for s in sigs:
                    signatures_dict[filename][s] = 1
            anchor_matches[filename] = anchors['anchors_matched'] / len(neighborhood)
            signatures_matches[filename] = (len(signatures_dict[filename]) - 2) / total_signatures
        # Find top-K matches with 2 different criteria.
        anchor_matches = sorted(anchor_matches.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
        signatures_matches = sorted(signatures_matches.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
        # return lists of tuples
        _hp.normalize(anchor_matches)
        # _hp.normalize(signatures_matches)
        for fi, sc in signatures_matches[:3]:
            wgt = sc/2
            sigs = self.invertsig_db.get(_hp.sha1_hash(fi.encode()))
            for sig in sigs:
                filehashes_lst = self.signatures_db.get(sig)
                if filehashes_lst is None:
                    continue
                anchor_hashes_lst = self.anchors_db.get(sig)
                # Get the list of filenames. Split by HASH_DIGEST_SIZE bytes.
                filehashes_lst = [ filehashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(filehashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # Get the list of anchor hashes that . Split by HASH_DIGEST_SIZE bytes.
                anchor_hashes_lst = [ anchor_hashes_lst[i * _hp.HASH_DIGEST_SIZE:(i + 1) * _hp.HASH_DIGEST_SIZE] for i in range((len(anchor_hashes_lst) + _hp.HASH_DIGEST_SIZE - 1) // _hp.HASH_DIGEST_SIZE ) ]
                # for filename_hash in filehashes_lst:
                for i in range(len(filehashes_lst)):
                    filename_hash = filehashes_lst[i]
                    filename = self.filenames_db.get(filename_hash).decode("utf-8")
                    anchor_hash = anchor_hashes_lst[i]
                    # If this is the first hash for that filename create a new inner dict
                    if filename not in matched_files:
                        matched_files[filename] = {}
                        matched_files[filename]['total'] = 1
                    # Count occurences
                    if anchor_hash not in matched_files[filename]:
                        matched_files[filename][anchor_hash] = []
                        matched_files[filename]['anchors_matched'] = 0
                    matched_files[filename][anchor_hash].append(sig)
                    matched_files[filename]['total'] += 1
                total_signatures += 1
                weighted_signatures[sig] += wgt
        total_weight = 0
        for ws in weighted_signatures:
            total_weight += ws

        for filename, anchors in matched_files.items():
            signatures_dict[filename] = {}
            signatures_dict[filename]['total'] = matched_files[filename]['total']
            sig_total = 0
            # for each anchor and the hashes in its neighborhood
            for anch, sigs in anchors.items():
                # Skip the counters
                if anch == 'anchors_matched' or anch == 'total':
                    continue
                if len(sigs) >= _hp.MIN_SIGNATURES_TO_MATCH:
                    matched_files[filename]['anchors_matched'] += 1
                filewgt = 0 
                for s in sigs:
                    signatures_dict[filename][s] = 1
                    filewght+=weighted_signatures[s]
            anchor_matches[filename] = anchors['anchors_matched'] / len(neighborhood)
            signatures_matches[filename] = file_wght / total_weight


        return anchor_matches, signatures_matches

def feedback_search_signatures3(self, neighborhood):
    
    anch, signa = search_signatures(self, neighborhood)

    anch_dict = {}
    sig_dict = {}
    #iterate through code
    for fi, score in signa:
        sig_dict[fi] = score
    for fi, score in anch:
        anch_dict[fi] = score
   
    wgt_scale = 1
    total_anch_wgt = 1
    total_sig_wgt = 1
    for fi, score in anch:
        wgt = score/wgt_scale
        if wgt < 0.01:
            break
        new_neigh = _fp.fingerprint(fi, _hp.NUM_OF_SLICES, _hp.NUM_OF_PEAKS, _hp.FAN_VALUE, _hp.ROTATE, _hp.INTERP, _hp.STAR_ROTATE)
        new_anch, new_sig = search_signatures(self, new_neigh)
        for nfi, nsc in new_anch:
            if nfi not in anch_dict:
                anch_dict[nfi] = wgt*nsc
            else:
                anch_dict[nfi] += wgt*nsc
        for nfi, nsc in new_sig:
            if nfi not in sig_dict:
                sig_dict[nfi] = wgt*nsc
            else:
                sig_dict[nfi] += wgt*nsc
        total_sig_wgt += wgt
        total_anch_wgt += wgt
        wgt_scale+=0.1

    wgt_scale=1
    for fi, score in signa:
        wgt = score/wgt_scale
        if wgt < 0.01:
            break
        new_neigh = _fp.fingerprint(fi, _hp.NUM_OF_SLICES, _hp.NUM_OF_PEAKS, _hp.FAN_VALUE, _hp.ROTATE, _hp.INTERP, _hp.STAR_ROTATE)
        new_anch, new_sig = search_signatures(self, new_neigh)
        for nfi, nsc in new_sig:
            if nfi not in sig_dict:
                sig_dict[nfi] = wgt*nsc
            else:
                sig_dict[nfi] += wgt*nsc
        for nfi, nsc in new_anch:
            if nfi not in anch_dict:
                anch_dict[nfi] = wgt*nsc
            else:
                anch_dict[nfi] += wgt*nsc
        total_sig_wgt += wgt
        total_anch_wgt += wgt
        wgt_scale+=0.1

    for fi in anch_dict:
        anch_dict[fi] /= total_anch_wgt
    for fi in sig_dict:
        sig_dict[fi] /= total_sig_wgt

    #now sort
    anch = sorted(anch_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]
    signa = sorted(sig_dict.items(), key=lambda x: x[1], reverse=True)[:_hp.NUMBER_OF_MATCHES]

    return anch, signa


