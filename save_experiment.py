#!/usr/bin/env python
import os,sys
thispath = os.path.dirname(os.path.abspath(__file__))
import subprocess
import hashlib
from datetime import datetime

#------------------------------------------------------------------------
# Hash and zip all script/config files in a directory (including subfolders)
#
# Optional: ssdeep fuzzy hashing
#     sudo apt install ssdeep
# Optional: the zip can be deterministically hashed, for reproduceability.
#           Otherwise, the exact same code on two different machines
#           will produce two different zip hashes unless you strip nondeterminism
#     sudo apt install strip-nondeterminism
#------------------------------------------------------------------------

default_directory = thispath
default_filetypes = ('.py', '.yaml')
default_hasher    = 'md5'
deterministic_zip = False

#------------------------------------------------------------------------

if hasattr(subprocess,'DEVNULL'):
    devnull = subprocess.DEVNULL
else:
    devnull = open(os.devnull,'rb')

def md5_of(fpath):
    hasher = hashlib.md5()
    with open(fpath, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    return hasher.hexdigest()
def ssdeep_of(fpath):
    ret = subprocess.check_output(['ssdeep',fpath],stderr=devnull).decode('ascii').split('\n')
    return ret[1][:ret[1].rfind(',\"')] # remove filename, we already save ourselves

def pad_spaces(ff,nspace):
    ff = str(ff)
    while len(ff) < nspace:
        ff += ' '
    return ff
def bytes2string(somestr):
    if isinstance(somestr,bytes):
        return somestr.decode('ascii')
    assert isinstance(somestr,str), str(type(somestr))
    return somestr

def figure_out_equal_spacing(list_of_entries_to_print):
    spacings = None
    for entry in list_of_entries_to_print:
        if isinstance(entry,tuple) or isinstance(entry,list):
            entry = tuple(str(ee) for ee in entry)
            if spacings is None:
                spacings = list([len(ee) for ee in entry])
            else:
                assert len(entry) == len(spacings), str(len(entry))+' vs '+str(len(spacings))
                spacings = list([max(len(entry[ii]),spacings[ii]) for ii in range(len(entry))])
    spacings = [ss+2 for ss in spacings[:-1]]+[spacings[-1],]
    returnstr = ""
    for entry in list_of_entries_to_print:
        if isinstance(entry,tuple) or isinstance(entry,list):
            entry = tuple(str(ee) for ee in entry)
            for ii in range(len(entry)):
                returnstr += pad_spaces(entry[ii],spacings[ii])
            returnstr += '\n'
        else:
            returnstr += str(entry)+'\n'
    return returnstr

def files_in_recursive_subdirs(mainfold, filetypes):
    assert os.path.isdir(mainfold)
    mainfold = os.path.abspath(mainfold)
    allret = []
    for root,dirs,filens in os.walk(mainfold):
        assert root.startswith(mainfold), root+'\n'+mainfold
        root = root[len(mainfold):]
        if root.startswith('/'):
            root = root[1:]
        for filen in filens:
            if any(filen.endswith(ft) for ft in filetypes):
                fpath = os.path.join(root,filen)
                allret.append((fpath,
                               int(round(os.path.getmtime(fpath))),
                               int(os.path.getsize(fpath)),
                               globals()[default_hasher+'_of'](fpath)))
    return allret


def experiment_info_save(zip_output_path, file_types_to_zip=default_filetypes, directory=default_directory):
    assert zip_output_path.endswith('.zip'), zip_output_path
    if os.path.isfile(zip_output_path):
        newbasename = None
        if '-' in zip_output_path[-20:]:
            maybeint = zip_output_path[zip_output_path.rfind('-')+1:-4]
            try:
                maybeint = int(maybeint)
            except ValueError:
                maybeint = None
            if maybeint is not None:
                newbasename = zip_output_path[:zip_output_path.rfind('-')]
        if newbasename is None:
            newbasename = zip_output_path[:-4]
        suffix_int = 0
        while os.path.isfile(zip_output_path):
            zip_output_path = newbasename+'-'+str(suffix_int)+'.zip'
            suffix_int += 1

    zipfs = files_in_recursive_subdirs(directory, filetypes=file_types_to_zip)

    # files meta should be sorted by timestamp (most recently modified at top)
    with open(zip_output_path[:-4]+'.txt', 'w') as outfile:
        printm = []
        printm.append(('filename','modified','bytes',default_hasher))
        printm.append("")
        # print files sorted by timestamp, descending
        for zipf in sorted(zipfs, key=lambda tup:tup[1], reverse=True):
            timestr = datetime.fromtimestamp(zipf[1]).isoformat()
            printm.append((zipf[0],timestr,zipf[2],zipf[3]))
        outfile.write(figure_out_equal_spacing(printm))
        # also save git info
        try:
            cout_log    = subprocess.check_output(['git','log','-1'],cwd=directory)+'\n'
        except subprocess.CalledProcessError:
            cout_log    = ''
        try:
            cout_status = subprocess.check_output(['git','status'],cwd=directory)
        except subprocess.CalledProcessError:
            cout_status = ''
        outfile.write('\n---------- git log -------------\n'+bytes2string(cout_log)
                       +'---------- git status ----------\n'+bytes2string(cout_status))

    # files passed to zip should be sorted by filename (deterministic)
    fnames = list(sorted([tup[0] for tup in zipfs]))
    zargs = ['zip', '-X', '-R', zip_output_path[:-4]] + fnames
    subprocess.check_output(zargs, cwd=directory)
    if deterministic_zip:
        subprocess.check_output(['strip-nondeterminism', '-t', 'zip', zip_output_path])
    return zip_output_path, md5_of(zip_output_path)


if __name__ == '__main__':
    try:
        inputpath = sys.argv[1]
        zoutpath  = sys.argv[2]
    except:
        print("usage:  {input-path}  {zip-output-path}")
        quit()

    zoutpath, themd5 = experiment_info_save(zoutpath, directory=inputpath)
    print("saved \'"+os.path.basename(zoutpath)+"\' with md5 "+str(themd5))

