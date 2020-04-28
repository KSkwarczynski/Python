#!/usir/bin/env python
import ROOT
import numpy as np
import matplotlib.pyplot as plt
#import pandas as pd
from mpl_toolkits.mplot3d import Axes3D
import sys
import math
# Try to load the project shared library. Might already be built.

def fTrackLenthgt(startX, startY, startZ, endX, endY, endZ ):
    Length = math.sqrt( (endX-startX)*(endX-startX)+(endY-startY)*(endY-startY)+(endZ-startZ)*(endZ-startZ) )
    return Length

def main():
    buildProject = False
    if (ROOT.gSystem.Load("SFGAnalysisProject/SFGAnalysisProject.so") < 0):
        buildProject = True
    # Get the ROOT TFile we will read.
    file = ROOT.TFile("/mnt/home/kskwarczynski/T2K2/Output/GENIEeventAnal.root","OLD")

    file_out = ROOT.TFile("/mnt/home/kskwarczynski/T2K2/kamilScripts/VAout.root","recreate")

    VertexString   =  ["1x1x1" , "3x3x3" , "5x5x5", "7x7x7", "9x9x9"]
    SelectionsName =  ["1mu1p", "1mu", "1muNp", "CC1Pi", "CCOther"]
    ReactionName   =  ["CCQE","2p2h", "RES", "DIS", "COH"]
        
    ReconstructionThreshold = 3.0
    
    VABox = [0., 1., 2., 3., 4.]
    hVertexActivityTrue = []
    hVertexActivityReco = []
    
    hVASplitSelection= []
    #[SelectionNumber][ReacTypeNum][5];
    
    
    FolderSplitedSelection = []
    #FolderSplitedSelection = file_out.mkdir(" TEST" )
    for ic in range(0, len(SelectionsName)):
        FolderSplitedSelection.append( file_out.mkdir('FolderSplited%s'%(SelectionsName[ic]) ) )
    
    
    for ic in range(0, len(SelectionsName)):  
        columnReac = []
        for ir in range(0, len(ReactionName)): 
            columnVA = []
            for ik in range(0, len(VertexString)):
                columnVA.append( ROOT.TH1F('VA%s_%s_%s'%(VertexString[ik], SelectionsName[ic], ReactionName[ir]), 'VA%s_%s_%s'%(VertexString[ik], SelectionsName[ic], ReactionName[ir]), 20, 0, 1000+ik*800) )
            columnReac.append(columnVA)
        hVASplitSelection.append(columnReac)
    
    
    for ik in range(0, len(VertexString)):
        hVertexActivityTrue.append( ROOT.TH1F('VAtrue%s'%(VertexString[ik]), 'VAtrue%s'%(VertexString[ik]), 100, 0, 10000+ik*10000) )
        hVertexActivityReco.append( ROOT.TH1F('VAreco%s'%(VertexString[ik]), 'VAreco%s'%(VertexString[ik]), 20, 0, 1000+ik*800) )

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
        VertexDepositT=np.zeros([5])
        VertexDepositR=np.zeros([5])
        VertexPos=np.zeros([3])
        RecoParticleCounter=np.zeros([4]) #[0-muon, 1-proton, 2-pion+, 3-pion-]
        
        ReactionSelection = list(bytearray(len(ReactionName)))  #CCQE 2p2h RES DIS COH
        TopologySelection= list(bytearray(len(SelectionsName))) #1mu1p 1mu 1muNp CC1Pi CCOther
        
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
        print "vertex module: in sfgd framework, vertex position is =",int((vt_x+985.92)/10.27),int((vt_y+287.56-46)/10.27),int((vt_z+2888.78)/10.27)
        VertexPos[0]=int((vt_x+985.92-5.135)/10.27)
        VertexPos[1]=int((vt_y+287.56-5.135)/10.27 - 4.6)
        VertexPos[2]=int((vt_z+2888.78-5.135)/10.27)

        reacMode=vertex.Vertices[0].ReactionCode
        #print reacMode
        
        if "Weak[CC],QES" in reacMode:
            print "CCQE"
            ReactionSelection[0] = True
        if "Weak[CC],MEC;" in reacMode:
            print "2p2h"
            ReactionSelection[1] = True
        if "Weak[CC],RES;" in reacMode:
            print "RES"
            ReactionSelection[2] = True
        if "Weak[CC],DIS;" in reacMode:
            print "DIS"
            ReactionSelection[3] = True
            
        #print "VERTEX TEST", VertexPos[0],"  ", VertexPos[1], " ", VertexPos[2] 
        if(vt_x<-986 or vt_x>986 or vt_y<-288+46 or vt_y>288+46 or vt_z<-2889 or vt_z>-998): print "vertex outside SFGD"
        if entry.NAlgoResults==0:
            print "end of event ",i
            print "-----------------"
            continue
        
        vt_true=np.zeros([4])
        vt_reco=np.zeros([4])
        VertexPosNew=np.zeros([4]) #X, Y , Z , DEP
        for h in entry.Hits:
            vt_reco[0]=h.Charge
            temp='{:032b}'.format(h.GeomId)
            vt_reco[1]=int(temp[10:18],2)
            vt_reco[2]=int(temp[18:24],2)
            vt_reco[3]=int(temp[24:32],2)
            if(abs(VertexPos[0]-vt_reco[1])<= 2 and abs(VertexPos[1]-vt_reco[2])<=2 and abs(VertexPos[2]-vt_reco[3])<=2 and vt_reco[0]>VertexPosNew[3]):
                VertexPosNew[0]=vt_reco[1]
                VertexPosNew[1]=vt_reco[2]
                VertexPosNew[2]=vt_reco[3]
                VertexPosNew[3]=vt_reco[0]
                
        #print "NEW vertex position X Y Z depo", VertexPosNew[0], " ", VertexPosNew[1]," ", VertexPosNew[2], " ", VertexPosNew[3]
        
        for traj in trueTree.Trajectories:
            pos_i=traj.InitPosition
            pos_f=traj.FinalPosition
            #print "true tree traj id = ",traj.ID,"PDG", traj.PDG, "parentID", traj.ParentID, "primaryId", traj.PrimaryID
            #print "start = ", pos_i[0]/10., pos_i[1]/10., pos_i[2]/10., " end = ", pos_f[0]/10., pos_f[1]/10., pos_f[2]/10.0
            #print "lenght", fTrackLenthgt(pos_i[0]/10., pos_i[1]/10., pos_i[2]/10., pos_f[0]/10., pos_f[1]/10., pos_f[2]/10.0)
            track_lenght = fTrackLenthgt(pos_i[0]/10., pos_i[1]/10., pos_i[2]/10., pos_f[0]/10., pos_f[1]/10., pos_f[2]/10.0)
            
            if(traj.PDG == 13 and traj.ParentID == 0 and track_lenght > ReconstructionThreshold): RecoParticleCounter[0]+= 1    #recoMuon
            if(traj.PDG == 2212 and traj.ParentID == 0 and track_lenght > ReconstructionThreshold): RecoParticleCounter[1]+= 1  #recoProton
            if(traj.PDG == 211 and traj.ParentID == 0 and track_lenght > ReconstructionThreshold): RecoParticleCounter[2]+= 1   #recoPion+
            if(traj.PDG == -211 and traj.ParentID == 0 and track_lenght > ReconstructionThreshold): RecoParticleCounter[3]+= 1  #recoPion-
        print "----------------------------"
        
        #Checking which Selection
        #1mu1p 1mu 1muNp CC1Pi CCOther
        if(RecoParticleCounter[0]==1 and RecoParticleCounter[1]==1 and RecoParticleCounter[2]==0 and RecoParticleCounter[3]==0): 
            TopologySelection[0]=True
        if(RecoParticleCounter[0]==1 and RecoParticleCounter[1]==0 and RecoParticleCounter[2]==0 and RecoParticleCounter[3]==0): 
            TopologySelection[1]=True
        if(RecoParticleCounter[0]==1 and RecoParticleCounter[1]>1  and RecoParticleCounter[2]==0 and  RecoParticleCounter[3]==0): 
            TopologySelection[2]=True
        if(RecoParticleCounter[0]==1 and RecoParticleCounter[2]==1 and RecoParticleCounter[1]==1 and RecoParticleCounter[3]==0): 
            TopologySelection[3]=True
        if(TopologySelection[0] == False and TopologySelection[3]==False ): 
            TopologySelection[4]=True
            
        vt_true=np.zeros([4])
        vt_reco=np.zeros([4])
        for h in entry.TrueHits:
            vt_true[0]=h.Charge
            temp='{:032b}'.format(h.GeomId)
            vt_true[1]=int(temp[10:18],2)
            vt_true[2]=int(temp[18:24],2)
            vt_true[3]=int(temp[24:32],2)

            
            for ik in range(0, len(VertexString)):
                if(abs(VertexPosNew[0]-vt_true[1])<= VABox[ik] and abs(VertexPosNew[1]-vt_true[2])<=VABox[ik] and abs(VertexPosNew[2]-vt_true[3])<=VABox[ik] ):
                    VertexDepositT[ik] += vt_true[0]
    
        for h in entry.Hits:
            vt_reco[0]=h.Charge
            temp='{:032b}'.format(h.GeomId)
            vt_reco[1]=int(temp[10:18],2)
            vt_reco[2]=int(temp[18:24],2)
            vt_reco[3]=int(temp[24:32],2)
            for ik in range(0, len(VertexString)):
                if(abs(VertexPosNew[0]-vt_reco[1])<= VABox[ik] and abs(VertexPosNew[1]-vt_reco[2])<=VABox[ik] and abs(VertexPosNew[2]-vt_reco[3])<=VABox[ik] ):
                    VertexDepositR[ik] += vt_reco[0]

 
        for ik in range(0, len(VertexString)): 
            hVertexActivityTrue[ik].Fill(VertexDepositT[ik])
            hVertexActivityReco[ik].Fill(VertexDepositR[ik])
            for ir in range(0, len(ReactionName)):
                for ic in range(0, len(SelectionsName)):
                    if(TopologySelection[ic] and ReactionSelection[ir]):
                        hVASplitSelection[ic][ir][ik].Fill(VertexDepositR[ik])


    for ik in range(0, len(VertexString)): 
        hVertexActivityTrue[ik].Write("")
    for ik in range(0, len(VertexString)): 
        hVertexActivityReco[ik].Write("")
    
    for ic in range(0, len(SelectionsName)):
        FolderSplitedSelection[ic].cd()
        for ir in range(0, len(ReactionName)):
            for ik in range(0, len(VertexString)):
                hVASplitSelection[ic][ir][ik].Write("")

    
    
    
if __name__ == '__main__':
    main()
