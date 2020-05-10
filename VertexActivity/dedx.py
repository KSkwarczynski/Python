#!/usir/bin/env python
import ROOT
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import sys
# Try to load the project shared library. Might already be built.

buildProject = False
if (ROOT.gSystem.Load("SFGAnalysisProject/SFGAnalysisProject.so") < 0):
	buildProject = True
# Get the ROOT TFile we will read.
file = ROOT.TFile(sys.argv[1],"OLD")
# Build the project shared library if it's needed. This loads it too.

if (buildProject):
	file.MakeProject("SFGAnalysisProject","ND::TSFGReconModule","recreate++")
# Get the SFG reconstruction tree. There are other trees too.
sfgTree = file.Get("ReconDir/SFG")
trueTree = file.Get("TruthDir/Trajectories")
vertex = file.Get("TruthDir/Vertices")
# Look at each entry in the treei.
count=raw_input("enter no. of events: ")
f=open("pbomb.txt","w+")
f.write("event charge\r\n")
track=0
q=[]
print "----------------------------"
for entry in sfgTree:
 p1=[]
 p2=[]
 p3=[]
 c=[]
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
 if(vt_x<-986 or vt_x>986 or vt_y<-288 or vt_y>288 or vt_z<-2889 or vt_z>-998): print "vertex outside SFGD"
 if entry.NAlgoResults==0:
  print "end of event ",i
  print "-----------------"
  continue
 vt_true=np.zeros([4])
 vt_reco=np.zeros([4])
 for h in entry.TrueHits:
  if vt_true[0]<h.Charge:
   vt_true[0]=h.Charge
   temp='{:032b}'.format(h.GeomId)
   vt_true[1]=int(temp[10:18],2)
   vt_true[2]=int(temp[18:24],2)
   vt_true[3]=int(temp[24:32],2)
 print "true hit vertex charge = ",vt_true[0],"position = ",vt_true[1],vt_true[2],vt_true[3]
 for h in entry.Hits:
  if vt_reco[0]<h.Charge:
   vt_reco[0]=h.Charge
   temp='{:032b}'.format(h.GeomId)
   vt_reco[1]=int(temp[10:18],2)
   vt_reco[2]=int(temp[18:24],2)
   vt_reco[3]=int(temp[24:32],2)
 print "reco hit vertex charge = ",vt_reco[0],"position = ",vt_reco[1],vt_reco[2],vt_reco[3]
 #x=0
 #y=0
 #for algo in entry.AlgoResults:
 # print algo.AlgorithmName, algo.Tracks.size()
 for trk in entry.AlgoResults[0].Tracks:
  #z=0
  #trk=entry.AlgoResults[0].Tracks[itrk]
  energy=entry.Tracks[trk].EDeposit/400.
  length=entry.Tracks[trk].Length/10.
  dedx=energy/length
  for node in entry.Tracks[trk].Nodes:
   pos=entry.Nodes[node].Position
   for h in entry.Nodes[node].Hits: 
    #h=entry.Nodes[node].Hits[0]
    temp='{:032b}'.format(entry.Hits[h].GeomId)
    x=int(temp[10:18],2)
    y=int(temp[18:24],2)
    z=int(temp[24:32],2)
    p1.append(x)
    p2.append(y)
    p3.append(z)
#    p1.append(x)
#    p2.append(y)
#    p3.append(z)
    c.append(entry.Hits[h].Charge)
    #print "position = ",pos[0]/10., pos[1]/10., pos[2]/10., "geom id = ",x, y, z, " charge = ",entry.Hits[h].Charge
  for traj in entry.Tracks[trk].Truth_TrajIds:
   print "true traj id = ",traj
  #for hit in entry.Tracks[trk].Hits:
   #z=z+entry.Hits[hit].Charge
  #z=z+entry.Tracks[itrk].EDeposit
  print trk, "de/dx =", dedx, "edep=", energy, "length=",length
 for traj in trueTree.Trajectories:
   pos_i=traj.InitPosition
   pos_f=traj.FinalPosition
   print "true tree traj id = ",traj.ID, traj.PDG
   print "start = ", pos_i[0]/10., pos_i[1]/10., pos_i[2]/10., " end = ", pos_f[0]/10., pos_f[1]/10., pos_f[2]/10.0
 print "----------------------------"
 fig = plt.figure()
 #fig, axs = plt.subplots(2, 4, constrained_layout=True)
 ax = fig.add_subplot(221, projection='3d')
 img=ax.scatter(p1,p2,p3,c=c,cmap=plt.hot())
 fig.suptitle(" 3d and 2d projection of reconstruted pion track in SFGD")
 ax.set_xlabel("X(in cm)")
 ax.set_ylabel("Y(in cm)")
 ax.set_zlabel("Z(in cm)")
 fig.colorbar(img)
 
 ax = fig.add_subplot(222)
 img=ax.scatter(p1,p2,c=c,cmap=plt.hot())
 ax.set_xlabel("X(in cm)")
 ax.set_ylabel("Y(in cm)")
 fig.colorbar(img)

 ax = fig.add_subplot(223)
 img=ax.scatter(p2,p3,c=c,cmap=plt.hot())
 ax.set_xlabel("Y(in cm)")
 ax.set_ylabel("Z(in cm)")
 fig.colorbar(img)

 ax = fig.add_subplot(224)
 img=ax.scatter(p1,p3,c=c,cmap=plt.hot())
 ax.set_xlabel("X(in cm)")
 ax.set_ylabel("Z(in cm)")
 fig.colorbar(img)
 #ax.scatter(p1,p2,p3)
 plt.show()
