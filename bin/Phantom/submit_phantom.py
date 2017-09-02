#!/usr/bin/python
# - upload the script to my version of genproduction
# - prepare the script for the event generation
# - upload it to genproduction and find a way to test it
# - example for the next step:
#   https://github.com/cms-sw/genproductions/blob/master/bin/Powheg/runcmsgrid_powheg.sh
#   - il compiler usato da phantom puo' essere quello di phantom e non quello di cmssw?
#     --> sembra che cmssw non venga chiamato nella produzione dei LHE file
#   - come passo un seed random a phantom?
# - include the submission script in the gridpack, does it have to be shell?
# - FIXME new version of Phantom compiles also with CMS compilers,
#   we should produce compiled releases for various architectures
#   and check the correct choice of the phantom release wrt the cmssw version used to setup the environment
# - FIXME if I do the compilation, I should also pickup the same LHAPDF libraries of the CMSSW release?
#    - are they the same for all the releases with the same architecture?
#    - how do I get the list of architectures and most importantly the configurations?
#      slc6_amd64_gcc493 CMSSW_7_6_6_patch1 
#      slc6_amd64_gcc630 CMSSW_9_3_0_pre4   
#      slc5_amd64_gcc462 CMSSW_5_3_17       
#      slc5_amd64_gcc472 CMSSW_6_2_0_SLHC15 
#      slc6_amd64_gcc530 CMSSW_9_2_10       
#      slc5_amd64_gcc434 CMSSW_4_2_10_patch2
#      slc6_amd64_gcc491 CMSSW_7_5_8_patch7 
#      slc6_amd64_gcc481 CMSSW_7_1_29       
#      slc6_amd64_gcc472 CMSSW_5_3_36       
#       
# dettagli da josh su come funzionano le chiamate degli script
# so there are two places
# 
# 
# one for the traditional wmLHE workflow
# 
# and one for the new susy parameter scan workflow
# 
# for the wmLHE workflow: https://github.com/cms-sw/cmssw/blob/master/GeneratorInterface/LHEInterface/plugins/ExternalLHEProducer.cc#L253
# 
# https://github.com/cms-sw/cmssw/blob/master/GeneratorInterface/LHEInterface/plugins/ExternalLHEProducer.cc#L366
# 
# for the newer susy workflow which is only used for parameter scans so far:
# https://github.com/cms-sw/cmssw/blob/master/GeneratorInterface/Core/interface/GeneratorFilter.h#L247
# 
# https://github.com/cms-sw/cmssw/blob/09c3fce6626f70fd04223e7dacebf0b485f73f54/GeneratorInterface/Core/src/BaseHadronizer.cc#L78


import sys
import os
import commands
from commands import getstatusoutput
import datetime
import argparse
import datetime
import math
import ConfigParser
import re
import time


# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def replaceParameterInFile (inputFile, outputFile, substitute): 
    f = open (inputFile)
    lines = f.readlines ()
    f.close ()
    f = open (outputFile, 'w')
    for line in lines:
        if line.startswith ('*') or line.startswith (' ') or len (line) < 3 or line.startswith ('.') :
            f.write (line)
        else:
            words = line.split (' ')
            if words[0] in substitute.keys ():
                f.write (words[0] + ' ' + substitute[words[0]])
            else:
                f.write (line) 
    f.close ()


# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def execute (command, verbosity = False) :
    if (verbosity == True):
        print '---> running:'
        print command
    retCode = getstatusoutput (command)
    if (verbosity == True):
        for ri in retCode: print ri
    return retCode


# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def findLhapdfUsed (makefilename):
    f = open (makefilename, 'r')
    for line in f.readlines ():
        if line.startswith ('#') : continue
        if re.match ('^\s*PDFLIBDIR\s*=', line):
            return line.split()[2]
    

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def modifySubmitfileIntelCompiler (submitfilename, pdfgridfolder, phantompdflib):
    submitfile = open (submitfilename, 'read')
    lines = submitfile.readlines ()
    submitfile.close ()
    submitfile = open (submitfilename, 'write')
    submitfile.write ('#!/bin/bash\n\n')
    submitfile.write ('source /afs/cern.ch/sw/IntelSoftware/linux/setup.sh intel64\n')
    submitfile.write ('source /afs/cern.ch/sw/IntelSoftware/linux/x86_64/xe2016/compilers_and_libraries/linux/bin/compilervars.csh intel64\n')
    submitfile.write ('export LHAPDF=' + pdfgridfolder + '\n')
    submitfile.write ('export PDFLIBDIR=/afs/cern.ch/work/b/ballest/public/phantom/LHAPDF-6.1.5_work/lib\n')
#    submitfile.write ('export PDFLIBDIR=' + phantompdflib + '\n')
#    submitfile.write ('export PDFLIBDIR=' + pdfgridfolder + '/../../lib\n')
    submitfile.write ('export LD_LIBRARY_PATH=$PDFLIBDIR:$LD_LIBRARY_PATH\n')
    for i in range (1, len (lines)) :
        submitfile.write (lines[i])
    

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def modifySubmitfileCMSSWCompiler (submitfilename, pdfgridfolder, phantompdflib, cmssw, shell):
    submitfile = open (submitfilename, 'read')
    lines = submitfile.readlines ()
    submitfile.close ()
    submitfile = open (submitfilename, 'write')
    submitfile.write ('#!/bin/bash\n\n')
    submitfile.write ('source /afs/cern.ch/sw/IntelSoftware/linux/setup.sh intel64\n')
    submitfile.write ('source /afs/cern.ch/sw/IntelSoftware/linux/x86_64/xe2016/compilers_and_libraries/linux/bin/compilervars.csh intel64\n')
    submitfile.write ('scram project CMSSW ' + cmssw + '\n')
    submitfile.write ('eval `scram runtime -' + shell + '\n')
    submitfile.write ('export LHAPDF=' + pdfgridfolder + '\n')
    submitfile.write ('export PDFLIBDIR=/afs/cern.ch/work/b/ballest/public/phantom/LHAPDF-6.1.5_work/lib\n')
#    submitfile.write ('export PDFLIBDIR=' + phantompdflib + '\n')
#    submitfile.write ('export PDFLIBDIR=' + pdfgridfolder + '/../../lib\n')
    submitfile.write ('export LD_LIBRARY_PATH=$PDFLIBDIR:$LD_LIBRARY_PATH\n')
    for i in range (1, len (lines)) :
        submitfile.write (lines[i])
    

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def prepareEventProductionScript (productionfilename, pdfgridfolder, phantompdflib, cmssw, shell):
    productionfile = open (productionfilename, 'write')
    productionfile.write ('#!/bin/bash\n\n')
    productionfile.write ('source /afs/cern.ch/sw/IntelSoftware/linux/setup.sh intel64\n')
    productionfile.write ('source /afs/cern.ch/sw/IntelSoftware/linux/x86_64/xe2016/compilers_and_libraries/linux/bin/compilervars.csh intel64\n')
    productionfile.write ('scram project CMSSW ' + cmssw + '\n')
    productionfile.write ('eval `scram runtime -' + shell + '\n')
    productionfile.write ('export LHAPDF=' + pdfgridfolder + '\n')
    productionfile.write ('export PDFLIBDIR=/afs/cern.ch/work/b/ballest/public/phantom/LHAPDF-6.1.5_work/lib\n')
#    productionfile.write ('export PDFLIBDIR=' + phantompdflib + '\n')
#    productionfile.write ('export PDFLIBDIR=' + pdfgridfolder + '/../../lib\n')
    productionfile.write ('export LD_LIBRARY_PATH=$PDFLIBDIR:$LD_LIBRARY_PATH\n')
    for i in range (1, len (lines)) :
        productionfile.write (lines[i])
    

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def addGridsToRin (filename, grids, debug = False):
    if debug : print 'preparing ' + filename + '\n'
    configfile = open (filename, 'read')
    lines = configfile.readlines ()
    configfile.close ()
    configfile = open (filename, 'write')
    for line in lines:
        if line.startswith ('nfiles'):
            configfile.write (line)
            break
        configfile.write (line)
    for gridfile in grids.split ():
        if debug : print 'adding ' + gridfile + '\n'
        configfile.write (gridfile + '\n')
    configfile.close ()    
    

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


def wordInFile (word, filename):
    thefile = open (filename, 'r')
    s = thefile.read ()
    thefile.close ()
    if word in s: return True
    return False

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----


if __name__ == '__main__':

    if len (sys.argv) < 2 :
        print 'config file missing, exiting'
        sys.exit (1)

    debugging = False
    if len (sys.argv) > 2 : debugging = True
    rootfolder = os.getcwd ()

    # values to be inserted in the phantom r.in file
    substitute = {}
        
    config = ConfigParser.ConfigParser ()
    config.optionxform = str # to preserve the case when reading options
    print 'reading config file:',sys.argv[1]
    config.read (sys.argv[1])
    for section in config.sections ():
        options = config.options (section)
        for option in options:
            print '[' + section + '] ' + option, ':', config.get (section, option)
            if (section == 'parameters') :
                substitute [option] = config.get (section, option)
    # this means gridpack production
    substitute['ionesh'] = '0'  
  
    # prepare the folder for the gridpack creation
    foldername = os.getcwd () + '/phantomGrid_' + datetime.datetime.now().strftime('%y-%m-%d-%H-%M')
    if config.has_option ('general', 'foldername') :
        foldername = os.getcwd () + '/' + config.get ('general', 'foldername')
    if os.path.exists (foldername + '.tgz'):
        print 'gridpack ' + foldername + '.tgz already existing, exiting'
        sys.exit (1)
    print 'creating gridpack in folder: ' + foldername ;
    os.system ('rm -rf ' + foldername)
    os.system ('mkdir ' + foldername)
    os.chdir (foldername)
    workingfolder = os.getcwd ()

    # get the precompiled phantom code, untar it and get the name of the pdf libraries
    # used in the compilation
    phantom = config.get ('general', 'package')
    if not os.path.isfile (phantom):
        print 'Phantom package ' + phantom + ' not found, exiting'
        sys.exit (1)
    execute ('cp ' + phantom + ' ' + workingfolder, True)
    execute ('tar xzf ' + phantom.split ('/')[-1], True)
    phantomfolder = phantom.split ('/')[-1]
    dummy = '.tar.gz'
    phantomfolder = phantomfolder[0:-len(dummy)] if phantomfolder.endswith(dummy) else phantomfolder    
    dummy = '.tgz'
    phantomfolder = phantomfolder[0:-len(dummy)] if phantomfolder.endswith(dummy) else phantomfolder    
    phantompdflib = findLhapdfUsed (workingfolder + '/' + phantomfolder + '/makefile')

    # get the cmssw environment and the location of the pdf grids
    cmssw = config.get ('general', 'CMSSW')
    os.environ['SCRAM_ARCH'] = config.get ('general', 'ARCH')
    shell = 'sh'
    if os.environ['SHELL'].find ('c') != -1 :
        shell = 'csh'
    returnCode = execute ('scram project CMSSW ' + cmssw, True)
    if returnCode[0] != 0 :
        print 'cmssw release: ', cmssw, 'not found, exiting'
        sys.exit (1)
    os.chdir (cmssw + '/src')
    execute ('pwd', True)
    result = execute ('eval `scram runtime -' + shell + '` ; printenv | grep LHAPDF_DATA_PATH', True)
    os.chdir (workingfolder)
    # get the pdf grid
#    execute ('printenv | grep LHAPDF_DATA_PATH', True)
#    pdfgridfolder = os.environ['LHAPDF_DATA_PATH']
    for line in result[1].split('\n'):
        if line.startswith ('LHAPDF_DATA_PATH=') : 
            pdfgridfolder = line[len ('LHAPDF_DATA_PATH='):]
            break
    pdfgrids = pdfgridfolder+'/' + config.get ('parameters','PDFname')
    if not os.path.exists (pdfgrids):
        print 'PDF grids ' + pdfgrids + ' not found, exiting'
        sys.exit (1)    
    # NB this should happen before creating the phantom config file!
    substitute['PDFname'] = pdfgrids

    # prepare the r.in phantom config file
    templatefile = 'nonEsisto'  
    if config.has_option ('general', 'template'):
        templatefile = rootfolder + '/' + config.get ('general', 'template')
    if not os.path.exists (templatefile):
        templatefile = workingfolder + '/' + phantomfolder + '/r.in'
        print 'r.in template not found, using the default one in the phantom release'
    replaceParameterInFile (templatefile, workingfolder + '/r.in', substitute)

    # get the setupdir2 script from the phantom folder
    execute ('cp ' + workingfolder + '/' + phantomfolder + '/tools/setupdir2.pl ' + workingfolder, True)    

    channel = config.get ('generation','channel')
    command = './setupdir2.pl'
    command += ' -b ' + workingfolder + '/' + phantomfolder
    if int (config.get ('generation', 'topnumber')) > 0 : 
        command += ' -T ' + config.get ('generation', 'topnumber')
    command += ' -d ' + workingfolder
    command += ' -t ' + workingfolder + '/r.in'
    command += ' -i "' + channel + '" -q ' + str (8 - len (channel.split ())) 
    command += ' -s ' + config.get ('submission','scheduler') + ' -n ' + config.get ('submission', 'queue')
    if substitute['i_signal'] == '1' :
        command += ' -Hs '
    elif substitute['i_signal'] == '2' :
        command += ' -S '
    submitfilename = workingfolder + '/LSFfile'

    # create the executable script to submit the gridpack production
    execute (command, True)

    # in case of QCD or QCD+EWK generation requests
    if config.get ('parameters','perturbativeorder') == '2' or config.get ('parameters','perturbativeorder') == '3':
        submitsinglegrids = []
        submitfile = open (submitfilename, 'read')
        for line in submitfile.readlines () :
            if 'bsub' in line: submitsinglegrids.append (line)
        submitfile.close ()

        # modify the channel variable adding the gluon legs
        channel = channel + ' g g' 
        
        command = './setupdir2.pl'
        command += ' -b ' + workingfolder + '/' + phantomfolder
        if int (config.get ('generation', 'topnumber')) > 0 : 
            command += ' -T ' + config.get ('generation', 'topnumber')
        command += ' -d ' + workingfolder
        command += ' -t ' + workingfolder + '/r.in'
        command += ' -i "' + channel + '" -q ' + str (8 - len (channel.split ())) 
        command += ' -s ' + config.get ('submission','scheduler') + ' -n ' + config.get ('submission', 'queue')
        if substitute['i_signal'] == '1' :
            command += ' -Hs '
        elif substitute['i_signal'] == '2' :
            command += ' -S '

        # create the executable script to submit the gridpack production
        # for the component w/ real gluons
        execute (command, True)
        
        # extend the executable script with the part w/o real gluons
        submitfile = open (submitfilename, 'a')
        submitfile.write ('\n')
        for line in submitsinglegrids :
            submitfile.write (line)
        submitfile.close ()

    # get the list of process folders
    processoutputs = []
    submitfile = open (submitfilename, 'read')
    for line in submitfile.readlines () :
        if 'bsub' in line: processoutputs.append (line.split()[6])
    submitfile.close ()

    # add to the LSFfile the environment setupdir
    # configuration to be setup before running the phantom program
    modifySubmitfileIntelCompiler (submitfilename, pdfgridfolder, phantompdflib)
    # modifySubmitfileCMSSWCompiler (submitfilename, pdfgridfolder, phantompdflib, cmssw, shell):

    # launch the submission script
    execute ('source ' + workingfolder + '/LSFfile', True)

    # wait until all jobs finish, before calculating the cross-section 
    # and compressing the gridpack
    finished = False
    while not finished:
        finished = True
        unfinished = int (0)
        for fil in processoutputs:
            if not os.path.exists (fil):
                finished = False
                unfinished += 1
        sys.stdout.write ('waiting for: ' + str (unfinished) + ' jobs\r' )
        sys.stdout.flush ()
        time.sleep (60) # seconds

    # log file of the generation parameters
    logfilename = workingfolder + '/log.txt'
    logfile = open (logfilename, 'write')

    # verify that all jobs finished successfully,
    finished = True
    for fil in processoutputs:
        if not wordInFile ('SIGMA', fil):
            print 'the following job had issues:\n  ' + fil
            logfile.write ('the following job had issues: ' + fil)
            finished = False

    if finished == False :
        print 'gridpack preparation failed'
        logfile.write ('gridpack preparation failed')
        logfile.close ()
        exit (1)

    # calculate the cross-section
    command = 'cd ' + workingfolder + '; grep SIGMA */run.out > res ; '
    command += workingfolder + '/' + phantomfolder + '/tools/totint.exe > result '
    execute (command, True)            
    result = execute ('tail -n 1 ' + workingfolder + '/result', True)
    Xsection = result[1] + ' pb'

    logfile.write ('CONFIG FILE\n\n')
    for section in config.sections ():
        options = config.options (section)
        for option in options:
            logfile.write ('[' + section + '] ' + option + ' : ' + config.get (section, option) + '\n')
    logfile.write ('\nSETUP COMMAND\n\n')
    logfile.write (command + '\n') 
    logfile.write ('\nRESULTING CROSS-SECTION FROM GRID CREATION\n\n')
    logfile.write (Xsection + '\n') 
    logfile.close ()

    # NB removing the phantom to save space, it will have to be put back (reasonably in the same place)
    #    when generating the events
    execute ('rm -rf ' + phantomfolder + '*', True)
    execute ('rm -rf CMSSW*', True)
    execute ('rm -rf LSFJOB*', True)
    
    # prepare the r.in file for the event production, starting from the template one
    execute ('rm -rf LSFJOB*', True)

    # to be run in workingfolder, get all the grids
    gridfiles = execute ('for fil in `find -L . -name "phavegas*"` ; do echo `pwd`/$fil ; done', True)

    replacement = {'ionesh':'1\n', 'nfiles': str(len (gridfiles[1].split ()))+'\n'} 
    replaceParameterInFile (workingfolder + '/r.in', workingfolder + '/r_GEN.in', replacement)
    addGridsToRin (workingfolder + '/r_GEN.in', gridfiles[1], debuigging)

    os.chdir (rootfolder)
    # FIXME does the gridpack require NOT to have a folder?
    execute ('cp ' + sys.argv[1] + ' ' + foldername, True)

    execute ('tar czf ' + foldername + '.tgz ' + foldername, True)
    print 'gridpack ' + foldername + '.tgz created'
    
    sys.exit (0)
    
