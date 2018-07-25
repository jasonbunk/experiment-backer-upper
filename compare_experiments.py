#!/usr/bin/env python
import os,sys

#------------------------------------------------------------------------
# TODO: if there are differences, optionally unzip the associated zips
#       and launch a nicer comparator like Meld
#------------------------------------------------------------------------

def _editdist_ssdeep(h1,h2):
    import editdistance
    return 1. - float(editdistance.eval(h1,h2)) \
              / float(max(len(h1),len(h2)))

def ssdeep_similarity(hash1, hash2):
    assert isinstance(hash1,str) and hash1.count(':') == 2, str(hash1)
    assert isinstance(hash2,str) and hash2.count(':') == 2, str(hash2)
    hs1 = hash1.split(':')
    hs2 = hash2.split(':')
    if   int(hs1[0]) ==   int(hs2[0]):
        return _editdist_ssdeep(hs1[1],hs2[1])
    elif int(hs1[0]) == 2*int(hs2[0]):
        return _editdist_ssdeep(hs1[1],hs2[2])
    elif int(hs1[0])*2 == int(hs2[0]):
        return _editdist_ssdeep(hs1[2],hs2[1])
    return _editdist_ssdeep(hs1[1],hs2[1])

def read_meta_file(metafile):
    assert isinstance(metafile,str), str(type(metafile))
    assert os.path.isfile(metafile), metafile
    ret = {}
    with open(metafile,'r') as infile:
        spacings = []
        nlines = 0
        whichhash = None
        for line in infile:
            line = line.strip('\r\n')
            nlines += 1
            if nlines == 1:
                assert line.startswith('filename '), line
                spacings = [int(line.find(key)) for key in ('modified','bytes')]
                for key in ('md5','ssdeep'):
                    if key in line:
                        whichhash = key
                        spacings.append(int(line.find(key)))
                        break
                assert whichhash is not None, 'could not find hash in header\n'+str(line)+'\n'
                spacings.append(len(line))
            elif nlines == 2:
                assert len(line) <= 2, str(line)
            elif line.startswith('---------- git log -------------'):
                break
            else:
                filename     =         line[           :spacings[0]].strip(' ')
                assert filename not in ret, 'duplicate key '+filename+'\n'+str(line)
                ret[filename] = {
                            'modified':line[spacings[0]:spacings[1]].strip(' '),
                            'bytes':   line[spacings[1]:spacings[2]].strip(' '),
                            'hash':    line[spacings[2]:spacings[3]].strip(' '),
                            'hashtype':whichhash,
                        }
    return ret

def print_files_in_1_but_not_2(check1, check2, fname1, fname2):
    assert isinstance(check1,dict) and isinstance(check2,dict)
    assert isinstance(fname1,str)  and isinstance(fname2,str)
    files_in_1_but_not_2 = set(check1.keys()) - set(check2.keys())
    if len(files_in_1_but_not_2) > 0:
        print("files in \'"+fname1+"\' not in \'"+fname2+"\':")
        print('\n'.join(sorted(['  '+ff for ff in files_in_1_but_not_2])))

def compare_hashes(check1, check2, fname1, fname2):
    assert isinstance(check1,dict) and isinstance(check2,dict)
    assert isinstance(fname1,str)  and isinstance(fname2,str)
    commonfiles = set(check1.keys()) & set(check2.keys())
    if len(commonfiles) <= 0:
        print("no files in common between \'"+fname1+"\' and \'"+fname2+"\'")
    else:
        print("checking "+str(len(commonfiles))+" common files\' hashes")
    for fname in sorted(list(commonfiles)):
        hash1 = check1[fname]['hash']
        hash2 = check2[fname]['hash']
        if hash1 != hash2:
            if check1[fname]['hashtype'] != \
               check2[fname]['hashtype']:
                print("different hash types for files! \'"  + \
                        check1[fname]['hashtype']+"\' vs \'"+ \
                        check2[fname]['hashtype']+"\'")
                return
            if check1[fname]['hashtype'] == 'ssdeep':
                print("file changed: "+str(fname)+": "+str(ssdeep_similarity(hash1,hash2))+" similarity")
            else:
                print("file changed: "+str(fname))

if __name__ == '__main__':
    try:
        infile1 = sys.argv[1]
        infile2 = sys.argv[2]
    except:
        print("usage:  {meta-file-1}  {meta-file-2}")
        quit()
    assert os.path.isfile(infile1), infile1
    assert os.path.isfile(infile2), infile2

    meta1 = read_meta_file(infile1)
    meta2 = read_meta_file(infile2)

    print_files_in_1_but_not_2(meta1, meta2, infile1, infile2)
    print_files_in_1_but_not_2(meta2, meta1, infile2, infile1)
    compare_hashes(meta1, meta2, infile1, infile2)

