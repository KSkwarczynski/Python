import ROOT
import numpy as np
import matplotlib.pyplot as plt

#WARNING It is easier to do in pyROOT, this is realy terible way to do this... 
hist = ROOT.TH2F("PDF", "PDF", 5, 0, 5, 2, 0, 1)
hist.Fill(0,0,1/10)
hist.Fill(1,0,1/10)
hist.Fill(2,0,1/10)
hist.Fill(3,0,1/10)

hist.Fill(2,1,1/10)
hist.Fill(3,1,2/10)
hist.Fill(4,1,2/10)
hist.Fill(5,1,2/10)
hist.Draw()



