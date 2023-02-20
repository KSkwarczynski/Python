#https://dirac.readthedocs.io/en/stable/CodeDocumentation/DataManagementSystem/Client/DataManager.html
#https://dirac.readthedocs.io/en/stable/DeveloperGuide/AddingNewComponents/DevelopingCommands/index.html#coding-commands


#  Relevant functions
#
# DataManager module
  # putAndRegister(lfn, fileName, diracSE, guid=None, path=None, checksum=None, overwrite=False)
  #  e.g.  print dm.putAndRegister('/t2k.org/user/king/test_api_DFCname.txt', './test_api.txt', 'UKI-LT2-QMUL2-disk')



from DIRAC.Core.Base import Script
Script.parseCommandLine()

from DIRAC.DataManagementSystem.Client.DataManager import DataManager
dm = DataManager()


######## Parts to Edit ########

# local list of files (read-only)
file_list = open('filesnu60-79.lst', 'r')

# local directory of files
local_folder = '/mnt/home/share/t2k/jlagoda/sand-muons-2022/sand-nu/anal'


# LFNs that correspond to list of files (read-only)
# Usuaully we use the file list to also deifne the LFNs
# But you could provide a different list of corresponding LFNs if you wish
lfn_list = open('filesnu60-79.lst', 'r')

# DFC directory of files
# If the DFC folder does not exist, it will be created automatically
dfc_folder = '/t2k.org/nd280/production007/validation/V07/mcp/neut_D/2010-11-air/sand/run3/anal'

# Site where you wish to copy the files to
site = 'IN2P3-CC-XRD-disk'

#############################

#print('debug 1')
#print dm.putAndRegister( '/t2k.org/user/king/t1.txt', '/data/king/t2k/GRID/dirac/dirac_api_tests/t1.txt' , site )
#print('debug 2')

for i,j in  zip(file_list, lfn_list):

    # use  rstrip() to remove the '\n' from reading the text file
    local = local_folder + '/' + i.rstrip('\n')
    dfc =   dfc_folder   + '/' + j.rstrip('\n')

    print('')
    print(local)
    print(dfc)
    print('')

    print dm.putAndRegister( dfc, local, site )


file_list.close()
lfn_list.close()
