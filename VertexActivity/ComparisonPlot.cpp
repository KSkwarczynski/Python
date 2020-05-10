#include <TH1.h>
#include <TH2F.h>
#include <fstream>
#include <iostream>
#include "TStyle.h"
#include <TColor.h>
#include <TLatex.h>

void ComparisonPlot()
{
    // -- WhichStyle --
    // 1 = presentation large fonts
    // 2 = presentation small fonts
    // 3 = publication/paper
    Int_t WhichStyle = 2;
    
    Int_t FontStyle = 22;
    Float_t FontSizeLabel = 0.035;
    Float_t FontSizeTitle = 0.05;
    Float_t YOffsetTitle = 1.3;

  switch(WhichStyle) 
  {
    case 1:
        FontStyle = 42;
        FontSizeLabel = 0.05;
        FontSizeTitle = 0.065;
        YOffsetTitle = 1.19;
        break;
    case 2:
        FontStyle = 42;
        FontSizeLabel = 0.035;
        FontSizeTitle = 0.05;
        YOffsetTitle = 1.6;
        break;
    case 3:
        FontStyle = 132;
        FontSizeLabel = 0.035;
        FontSizeTitle = 0.05;
        YOffsetTitle = 1.6;
        break;
    }
    // use plain black on white colors
    gStyle->SetFrameBorderMode(0);
    gStyle->SetCanvasBorderMode(0);
    gStyle->SetPadBorderMode(0);
    gStyle->SetCanvasBorderSize(0);
    gStyle->SetFrameBorderSize(0);
    gStyle->SetDrawBorder(0);
    gStyle->SetTitleBorderSize(0);

    gStyle->SetPadColor(0);
    gStyle->SetCanvasColor(0);
    gStyle->SetStatColor(0);
    gStyle->SetFillColor(0);

    gStyle->SetEndErrorSize(4);
    gStyle->SetStripDecimals(kFALSE);

    //gStyle->SetLegendBorderSize(0); //This option dsables legends borders
    gStyle->SetLegendFont(FontStyle);

    // set the paper & margin sizes
    gStyle->SetPaperSize(20, 26);
    gStyle->SetPadTopMargin(0.1);
    gStyle->SetPadBottomMargin(0.15);
    gStyle->SetPadRightMargin(0.13); // 0.075 -> 0.13 for colz option
    gStyle->SetPadLeftMargin(0.16);//to include both large/small font options

    // Fonts, sizes, offsets
    gStyle->SetTextFont(FontStyle);
    gStyle->SetTextSize(0.08);

    gStyle->SetLabelFont(FontStyle, "x");
    gStyle->SetLabelFont(FontStyle, "y");
    gStyle->SetLabelFont(FontStyle, "z");
    gStyle->SetLabelFont(FontStyle, "t");
    gStyle->SetLabelSize(FontSizeLabel, "x");
    gStyle->SetLabelSize(FontSizeLabel, "y");
    gStyle->SetLabelSize(FontSizeLabel, "z");
    gStyle->SetLabelOffset(0.015, "x");
    gStyle->SetLabelOffset(0.015, "y");
    gStyle->SetLabelOffset(0.015, "z");

    gStyle->SetTitleFont(FontStyle, "x");
    gStyle->SetTitleFont(FontStyle, "y");
    gStyle->SetTitleFont(FontStyle, "z");
    gStyle->SetTitleFont(FontStyle, "t");
    gStyle->SetTitleSize(FontSizeTitle, "y");
    gStyle->SetTitleSize(FontSizeTitle, "x");
    gStyle->SetTitleSize(FontSizeTitle, "z");
    gStyle->SetTitleOffset(1.14, "x");
    gStyle->SetTitleOffset(YOffsetTitle, "y");
    gStyle->SetTitleOffset(1.2, "z");

    gStyle->SetTitleStyle(0);
    gStyle->SetTitleFontSize(0.06);//0.08
    gStyle->SetTitleFont(FontStyle, "pad");
    gStyle->SetTitleBorderSize(0);
    gStyle->SetTitleX(0.1f);
    gStyle->SetTitleW(0.8f);

    // use bold lines and markers
    gStyle->SetMarkerStyle(20);
    gStyle->SetHistLineWidth( Width_t(2.5) );
    gStyle->SetLineStyleString(2, "[12 12]"); // postscript dashes

    // get rid of X error bars and y error bar caps
    gStyle->SetErrorX(0.001);

    // do not display any of the standard histogram decorations
    //gStyle->SetOptTitle(0); //Set 0 to disable histogram tittle
    gStyle->SetOptStat(0); //Set 0 to disable statystic box
    gStyle->SetOptFit(0);

    // put tick marks on top and RHS of plots
    gStyle->SetPadTickX(0);
    gStyle->SetPadTickY(0);

    // -- color --
    // functions blue
    //gStyle->SetFuncColor(600-4);
    gStyle->SetFuncColor(2);
    gStyle->SetFuncWidth(2);

    gStyle->SetFillColor(1); // make color fillings (not white)
    // - color setup for 2D -
    // - "cold"/ blue-ish -
    Double_t red[]   = { 0.00, 0.00, 0.00 };
    Double_t green[] = { 1.00, 0.00, 0.00 };
    Double_t blue[]  = { 1.00, 1.00, 0.25 };
    // - "warm" red-ish colors -
    //  Double_t red[]   = {1.00, 1.00, 0.25 };
    //  Double_t green[] = {1.00, 0.00, 0.00 };
    //  Double_t blue[]  = {0.00, 0.00, 0.00 };

    Double_t stops[] = { 0.25, 0.75, 1.00 };
    const Int_t NRGBs = 3;
    const Int_t NCont = 500;

    TColor::CreateGradientColorTable(NRGBs, stops, red, green, blue, NCont);
    gStyle->SetNumberContours(NCont);

    // - Rainbow -
    gStyle->SetPalette(1);  // use the rainbow color set

    // -- axis --
    gStyle->SetStripDecimals(kFALSE); // don't do 1.0 -> 1
    //  TGaxis::SetMaxDigits(3); // doesn't have an effect
    // no supressed zeroes!
    gStyle->SetHistMinimumZero(kTRUE);    
/////////////////////////////////////////////////////////////////////  
/////////////////////////////////////////////////////////////////////     
/////////////////////////////////////////////////////////////////////  
    const int SelectionNumber = 5;
    const int ReacTypeNum = 5;
    bool CIS = true;
    
    TString Directory="/Users/kolos/Desktop/sFGD/Output/";
    TString DirectoryPlots="/Users/kolos/Desktop/sFGD/Plots/GENIE/";
    TString DirectorySelePlots="/Users/kolos/Desktop/sFGD/Plots/GENIE/Selections/";
    TString DirectoryReacPlots="/Users/kolos/Desktop/sFGD/PlotsGENIE/GENIE/Reactions/";
    TString DirectorySplitSelectionsPlots="/Users/kolos/Desktop/sFGD/Plots/GENIE/SplitSelections/";
    
    TString FileName="VAout";
    TString VetrexString[5]={"1x1x1" , "3x3x3" , "5x5x5", "7x7x7", "9x9x9"};        
    TString SelectionsName[SelectionNumber]={"1mu1p", "1mu", "1muNp", "CC1Pi", "CCOther"};
    TString ReactionName[ReacTypeNum]={"CCQE", "2p2h", "RES", "DIS", "COH"};
    
    if(CIS)
    {
        Directory="/mnt/home/kskwarczynski/T2K2/kamilScripts/";
        DirectorySplitSelectionsPlots="mnt/home/kskwarczynski/T2K2/kamilScripts/PlotOutput/VertexActivity/GENIE/SplitSelections/";
    }
    TFile *file;

    TH1F *hVASplitSelection[SelectionNumber][ReacTypeNum][5];

    file = new TFile(Form("%s%s.root", Directory.Data() , FileName.Data()),"READ");
    if (file->IsOpen() )
    {
        printf("File opened successfully\n");
    }  

    TDirectory *FolderSplitedSelection[SelectionNumber];
    for(int ic=0; ic<SelectionNumber; ic++) 
    {
       FolderSplitedSelection[ic]= (TDirectory*)file->Get( Form( "FolderSplited%s", SelectionsName[ic].Data() ) );
    }
    file->cd();
    
    for(int ik=0; ik<5; ik++)
    {
        for(int ic=0; ic<SelectionNumber; ic++)
        {
            for(int ir=0; ir<ReacTypeNum; ir++) 
            {
                hVASplitSelection[ic][ir][ik] = (TH1F*) FolderSplitedSelection[ic]->Get( Form("VA%s_%s_%s", VetrexString[ik].Data(), SelectionsName[ic].Data(), ReactionName[ir].Data() ) );
            }
        }
    }
    
    TCanvas *Canvas[300];
    TLegend *legend[300];
    int canvasCounter=0;
    
///////////////////////////////// DRAWING PART STARTS HERE/////////////////////////////   
    THStack *VAstackSplit[SelectionNumber][5];
    for(int ik=0; ik<5; ik++)
    {
        for(int ic=0; ic<SelectionNumber; ic++)
        {
            Canvas[canvasCounter] = new TCanvas( Form("Canvas%i",canvasCounter), Form("Canvas%i",canvasCounter), 1400, 1000);
            //CCQE 2p2h RES DIS COH NC
            hVASplitSelection[ic][0][ik]->SetFillColor(kRed);
            hVASplitSelection[ic][0][ik]->SetMarkerStyle(21);
            hVASplitSelection[ic][0][ik]->SetMarkerColor(kRed);
            
            hVASplitSelection[ic][1][ik]->SetFillColor(kViolet);
            hVASplitSelection[ic][1][ik]->SetMarkerStyle(21);
            hVASplitSelection[ic][1][ik]->SetMarkerColor(kViolet);
            
            hVASplitSelection[ic][2][ik]->SetFillColor(kGreen);
            hVASplitSelection[ic][2][ik]->SetMarkerStyle(21);
            hVASplitSelection[ic][2][ik]->SetMarkerColor(kGreen);
        
            hVASplitSelection[ic][3][ik]->SetFillColor(kBlue);
            hVASplitSelection[ic][3][ik]->SetMarkerStyle(21);
            hVASplitSelection[ic][3][ik]->SetMarkerColor(kBlue);
        
            hVASplitSelection[ic][4][ik]->SetFillColor(kCyan);
            hVASplitSelection[ic][4][ik]->SetMarkerStyle(21);
            hVASplitSelection[ic][4][ik]->SetMarkerColor(kCyan);
        
            VAstackSplit[ic][ik] = new THStack( Form("VAstackSplit%s_%s",  VetrexString[ik].Data(),SelectionsName[ic].Data() ), Form("VAstackSplit%s", VetrexString[ik].Data()) );
            VAstackSplit[ic][ik]->Add( hVASplitSelection[ic][0][ik] );
            VAstackSplit[ic][ik]->Add( hVASplitSelection[ic][1][ik] );
            VAstackSplit[ic][ik]->Add( hVASplitSelection[ic][2][ik] );
            VAstackSplit[ic][ik]->Add( hVASplitSelection[ic][3][ik] );
            VAstackSplit[ic][ik]->Add( hVASplitSelection[ic][4][ik] );
        
            VAstackSplit[ic][ik]->Draw("");
        
            VAstackSplit[ic][ik]->GetXaxis()->SetTitle( Form("Energy deposit in box %s [p.e.]", VetrexString[ik].Data()) );
        
            legend[canvasCounter] = new TLegend(0.60,0.7,0.9,0.9);
            for(int ir=0; ir<ReacTypeNum; ir++)
            {
                legend[canvasCounter]->AddEntry(hVASplitSelection[ic][ir][ik], Form( "VA%s_%s", VetrexString[ik].Data(), ReactionName[ir].Data() ),"f");
            }
            legend[canvasCounter]->SetTextSize(0.04);
            legend[canvasCounter]->Draw();
        
            gPad->Modified();
            Canvas[canvasCounter]->Print( Form("%sVA%s_StackSplit_%s.pdf", DirectorySplitSelectionsPlots.Data(), VetrexString[ik].Data(), SelectionsName[ic].Data()) ); 
            delete Canvas[canvasCounter];
            canvasCounter++;
        }
    }

}
