#!/usir/bin/env python
import ROOT
import numpy as np
import matplotlib.pyplot as plt
#import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import sys
# Try to load the project shared library. Might already be built.

buildProject = False
if (ROOT.gSystem.Load("SFGAnalysisProject/SFGAnalysisProject.so") < 0):
	buildProject = True
# Get the ROOT TFile we will read.
file = ROOT.TFile("/mnt/home/kskwarczynski/T2K2/Output/BOMBeventAnal.root","OLD")

file_out = ROOT.TFile("/mnt/home/kskwarczynski/T2K2/kamilScripts/VAout.root","recreate")

VertexString = ["1x1x1" , "3x3x3" , "5x5x5", "7x7x7", "9x9x9"]
VABox = [0., 1., 2., 3., 4.]
hVertexActivity = []
for ik in range(0, len(VertexString)):
    hVertexActivity.append( ROOT.TH1F('VA%s'%(VertexString[ik]), 'VA%s'%(VertexString[ik]), 50, 0, 4000+ik*3000) ) #



#hXY = ROOT.TH2F('hXY', 'hXZ', 204, 0.5, 204+0.5, 56, 0.5, 56+0.5)
#hXZ = ROOT.TH2F('hXZ', 'hXZ', 204, 0.5, 204+0.5, 188, 0.5, 188+0.5)
#hYZ = ROOT.TH2F('hYZ', 'hYZ', 56, 0.5, 56+0.5, 188, 0.5, 188+0.5)

# Build the project shared library if it's needed. This loads it too.

if (buildProject):
	file.MakeProject("SFGAnalysisProject","ND::TSFGReconModule","recreate++")
# Get the SFG reconstruction tree. There are other trees too.
sfgTree = file.Get("ReconDir/SFG")
trueTree = file.Get("TruthDir/Trajectories")
vertex = file.Get("TruthDir/Vertices")
# Look at each entry in the treei.
#WARNING pozniej to wywal albo ustaw wlasnorecznie
count=raw_input("enter no. of events: ")
track=0
q=[]
print "----------------------------"
for entry in sfgTree:
    c=[]
    VertexDeposit=np.zeros([5])
    VertexPos=np.zeros([3])
    i=entry.EventID
    print i, count
    trueTree.GetEntry(i)
    vertex.GetEntry(i)
    if i==int(count):
        print "analyzed",count,"events"
        break
    if entry.NAlgoResults==0: continue
    vt_x=vertex.Vertices[0].Position[0]
    vt_y=vertex.Vertices[0].Position[1]
    vt_z=vertex.Vertices[0].Position[2]
    print "vertex module: global coord vertex position ",entry.EventID, vertex.NVtx, vt_x, vt_y, vt_z
    print "vertex module: in sfgd framework, vertex position is =",int((vt_x+985.92)/10.27),int((vt_y+287.56)/10.27),int((vt_z+2888.78)/10.27)
    VertexPos[0]=int((vt_x+985.92)/10.27)
    VertexPos[1]=int((vt_y+287.56)/10.27)
    VertexPos[2]=int((vt_z+2888.78)/10.27)

    print "VERTEX TEST", VertexPos[0],"  ", VertexPos[1], " ", VertexPos[2] 
    if(vt_x<-986 or vt_x>986 or vt_y<-288 or vt_y>288 or vt_z<-2889 or vt_z>-998): print "vertex outside SFGD"
    if entry.NAlgoResults==0:
        print "end of event ",i
        print "-----------------"
        continue
    vt_true=np.zeros([4])
    vt_reco=np.zeros([4])
    for h in entry.TrueHits:
        #if vt_true[0]<h.Charge:
        vt_true[0]=h.Charge
        temp='{:032b}'.format(h.GeomId)
        vt_true[1]=int(temp[10:18],2)
        vt_true[2]=int(temp[18:24],2)
        vt_true[3]=int(temp[24:32],2)
        #print "DEBUG X", abs(VertexPos[0]-vt_true[1]), "DEBUG Y", abs(VertexPos[1]-vt_true[2]),"DEBUG Z",  abs(VertexPos[2]-vt_true[3])
        #hXY.Fill(vt_true[1], vt_true[2], vt_true[0])
        #hXZ.Fill(vt_true[1], vt_true[3], vt_true[0])
        #hYZ.Fill(vt_true[2], vt_true[3], vt_true[0])
        if(VertexPos[0]==vt_true[1] and VertexPos[1]==vt_true[2] and VertexPos[2]==vt_true[3]):
            print("KURWA")
        
        for ik in range(0, 5):
            if(abs(VertexPos[0]-vt_true[1])<= VABox[ik] and abs(VertexPos[1]-vt_true[2])<=VABox[ik] and abs(VertexPos[2]-vt_true[3])<=VABox[ik] ):
                #print "PETLA DEBUG box", ik," x ",  vt_true[1], " y ",vt_true[2], " z ", vt_true[3]
                VertexDeposit[ik] += vt_true[0]
                hVertexActivity[ik].Fill(vt_true[0])
                #print "DEBUG X", abs(VertexPos[0]-vt_true[1]), "DEBUG Y", abs(VertexPos[1]-vt_true[2]),"DEBUG Z",  abs(VertexPos[2]-vt_true[3])
   
    #print "true hit vertex charge = ",vt_true[0],"position = ",vt_true[1],vt_true[2],vt_true[3]
    for h in entry.Hits:
        #if vt_reco[0]<h.Charge:
        vt_reco[0]=h.Charge
        temp='{:032b}'.format(h.GeomId)
        vt_reco[1]=int(temp[10:18],2)
        vt_reco[2]=int(temp[18:24],2)
        vt_reco[3]=int(temp[24:32],2)
        #print "reco X", vt_reco[1]," Y", vt_reco[2]," Z",  vt_reco[3], "CHARGE", vt_reco[0]
        #for ik in range(0, len(VertexString)):
            #if(abs(VertexPos[0]-vt_true[1])<= VABox[ik] and abs(VertexPos[1]-vt_true[2])<=VABox[ik] and abs(VertexPos[2]-vt_true[3])<=VABox[ik] ):
                #print "PETLA RECO DEBUG"
    for ik in range(0, len(VertexString)):  
        hVertexActivity[ik].Fill(VertexDeposit[ik])

file_out.Write()
