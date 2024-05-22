import ROOT
import math
from ROOT import TFile, TCanvas, TH2Poly, TLegend, TLine, TH1D, TDirectory
from math import sqrt

def get_neffective(N1, N2):
    nominator = N1 + N2
    denominator = N1 * N2
    N_e = nominator / denominator
    return N_e

def replace(string, old, new):
    return string.replace(old, new)

def fancy_sample(fancy_string):
    fancy_string = fancy_string.replace('_', ' ')
    fancy_string = replace(fancy_string, "pi ", "#pi ")
    fancy_string = replace(fancy_string, "0pi", "0#pi")
    fancy_string = replace(fancy_string, "1pi", "1#pi")
    fancy_string = replace(fancy_string, "no photon", "0#gamma")
    fancy_string = replace(fancy_string, "AntiNu", "#bar{#nu}")
    fancy_string = replace(fancy_string, " numuCC", " #nu_{#mu} CC")
    fancy_string = replace(fancy_string, " anti-numuCC", " #bar{#nu}_{#mu} CC")
    fancy_string = replace(fancy_string, "CC other", "CC Other")
    fancy_string = replace(fancy_string, "CCother", "CC Other")
    return fancy_string

def prepare_nd_samples(infile, samples_name, sample_directory_vector, predictive):
    for key in infile.GetListOfKeys():
        classname = key.GetClassName()
        if not predictive:
            if classname != "TH2Poly":
                continue
            name = key.GetName()
            if "DATA_" in name:
                name = name.replace("DATA_", "")
                samples_name.append(name)
                sample_directory_vector.append(name)
                print(samples_name[-1])
        else:
            if classname != "TDirectoryFile":
                continue
            dirname = key.GetName()
            if dirname in ["BetaParameters", "Correlations"]:
                continue
            sample_directory_vector.append(dirname)
            infile.cd(dirname)
            for subkey in ROOT.gDirectory.GetListOfKeys():
                if subkey.GetClassName() == "TH2Poly":
                    poly = subkey.ReadObj()
                    name = poly.GetName()
                    if "_norm" in name:
                        continue
                    if "_data" in name:
                        name = name[:-5]
                        samples_name.append(name)
                        print(samples_name[-1])
    if len(samples_name) == 0:
        print("Didn't find any sample")
        print("Something went wrong")
        raise Exception("No samples found")
    return

def get_data_histograms(input_file, sample_directory_vector, samples_name, predictive):
    if not predictive:
        sample_data = input_file.Get("DATA_{}".format(samples_name)).Clone()
    else:
        temp_string = "{}/{}_data".format(sample_directory_vector, samples_name)
        sample_data = input_file.Get(temp_string).Clone()
    sample_data.SetDirectory(0)
    fancy_name = sample_data.GetName()
    fancy_name = fancy_sample(fancy_name)
    return sample_data

def get_mc_histograms(input_file, sample_directory_vector, samples_name, predictive):
    if not predictive:
        sample_mc = input_file.Get("MC_{}".format(samples_name)).Clone()
    else:
        temp_string = "{}/{}_mean".format(sample_directory_vector, samples_name)
        sample_mc = input_file.Get(temp_string).Clone()
    sample_mc.SetDirectory(0)
    fancy_name = sample_mc.GetName()
    fancy_name = fancy_sample(fancy_name)
    sample_mc.SetTitle(fancy_name)
    return sample_mc

def kolmogorov_prob(z):
    x = 0
    for i in range(1, 101):
        x += (-1)**(i-1) * math.exp(-2 * i**2 * z**2)
    return 2 * x

def get_critical_value(n, p):
    dn = 1
    delta = 0.5
    res = kolmogorov_prob(dn * math.sqrt(n))
    while res > 1.0001 * p or res < 0.9999 * p:
        if res > 1.0001 * p:
            dn += delta
        if res < 0.9999 * p:
            dn -= delta
        delta /= 2.0
        res = kolmogorov_prob(dn * math.sqrt(n))
    return dn

def kaboth_skwarczynski_test(canvas, fname, input_file, output_file, sample_directory_vector, sample_name_vector):
    print("Performing Kaboth Skwarczynski test")
    right_margin = canvas.GetRightMargin()
    canvas.SetRightMargin(0.03)

    bottom_margin = canvas.GetBottomMargin()
    canvas.SetBottomMargin(0.20)

    debug = True
    for f, file_name in enumerate(fname):
        canvas.Print("{}_KabothSkwarczynski.pdf[".format(file_name), "pdf")
        if debug:
            canvas.Print("{}_KabothSkwarczynskiDebug.pdf[".format(file_name), "pdf")
        output_file[f].cd()
        ks_dir = output_file[f].mkdir("KabothSkwarczynskiDir")

        for i, sample_name in enumerate(sample_name_vector):
            data_poly = get_data_histograms(input_file[f], sample_directory_vector[i], sample_name, True)
            poly_mc = get_mc_histograms(input_file[f], sample_directory_vector[i], sample_name, True)

            temp_string = "{}/{}_mean_x_x".format(sample_directory_vector[i], sample_name)
            print("Attempting to retrieve: %s" % temp_string)
            sample_mc_x = input_file[f].Get(temp_string).Clone()
            temp_string = "{}/{}_mean_y_y".format(sample_directory_vector[i], sample_name)
            print("Attempting to retrieve: %s" % temp_string)
            sample_mc_y = input_file[f].Get(temp_string).Clone()

            number_of_bins = poly_mc.GetNumberOfBins()

            x_bins = sample_mc_x.GetXaxis().GetNbins()
            y_bins = sample_mc_y.GetXaxis().GetNbins()
            if x_bins * y_bins != number_of_bins:
                print("XBins ({}) * YBins({}) is not equal to NumberOfBins({})".format(x_bins, y_bins, number_of_bins))
                print("Can't make Kaboth Skwarczynski test")
                return

            fancy_name = sample_directory_vector[i]
            fancy_name = fancy_sample(fancy_name)
            fancy_name = fancy_name + " Kaboth-Skwarczynski"

            ks_plot = TH1D("{} Kaboth Skwarczynski".format(sample_directory_vector[i]), fancy_name, y_bins, 0, y_bins)
            ks_plot.SetLineColor(ROOT.kBlue)
            ks_plot.SetLineWidth(2)
            ks_plot.GetXaxis().SetLabelSize(0.030)
            ks_plot.GetYaxis().SetTitle("KS Test Stat")
            ks_plot.SetMarkerStyle(20)

            bin_counter = 1
            for iy in range(y_bins):
                data_integral = 0
                mc_integral = 0
                bin_counter_temp = bin_counter
                for ix in range(x_bins):
                    data_integral += data_poly.GetBinContent(bin_counter_temp)
                    mc_integral += poly_mc.GetBinContent(bin_counter_temp)
                    bin_counter_temp += 1
                bin = data_poly.GetBins().At(bin_counter - 1)
                label = " cos#theta_{{#mu}} ({}-{})".format(bin.GetYMin(), bin.GetYMax())
                ks_plot.GetXaxis().SetBinLabel(iy + 1, label)

                cumulative_data = 0
                cumulative_mc = 0
                test_stat_d = 0

                cum_dist_data = TH1D("{} {}".format(sample_directory_vector[i], label), "{} {}".format(sample_directory_vector[i], label), x_bins, 0, x_bins)
                cum_dist_data.SetLineColor(ROOT.kBlue)
                cum_dist_data.SetLineWidth(2)
                cum_dist_data.GetYaxis().SetTitle("Cumulative Probability")
                cum_dist_data.GetXaxis().SetLabelSize(0.02)

                cum_dist_mc = TH1D("{} {} MC".format(sample_directory_vector[i], label), "{} {} MC".format(sample_directory_vector[i], label), x_bins, 0, x_bins)
                cum_dist_mc.SetLineColor(ROOT.kRed)
                cum_dist_mc.SetLineStyle(ROOT.kDotted)

                for ix in range(x_bins):
                    bin = data_poly.GetBins().At(bin_counter - 1)
                    label = "p_{{#mu}} ({}-{})".format(bin.GetXMin(), bin.GetXMax())
                    cum_dist_data.GetXaxis().SetBinLabel(ix + 1, label)

                    cumulative_data += data_poly.GetBinContent(bin_counter) / data_integral
                    cumulative_mc += poly_mc.GetBinContent(bin_counter) / mc_integral

                    cum_dist_data.SetBinContent(ix + 1, cumulative_data)
                    cum_dist_mc.SetBinContent(ix + 1, cumulative_mc)
                    test_stat_d = max(test_stat_d, abs(cumulative_data - cumulative_mc))

                    bin_counter += 1
                ks_plot.SetBinContent(iy + 1, test_stat_d)
                cum_dist_data.GetXaxis().LabelsOption("v")
                cum_dist_data.Draw()
                cum_dist_mc.Draw("SAME")
                if debug:
                    canvas.Print("{}_KabothSkwarczynskiDebug.pdf".format(file_name), "pdf")

            # FIXME!!!!
            alpha = 0.05
            #ks_cv = get_critical_value(int(get_neffective(data_integral, mc_integral)), alpha)
            ks_cv = 0.05
            ks_plot.SetMaximum(ks_cv * 1.05)
            ks_plot.Draw()

            critical = TLine(0, ks_cv, y_bins, ks_cv)
            critical.SetLineStyle(2)
            critical.SetLineColor(ROOT.kRed)
            critical.Draw("SAME")

            # Calculate the mean of the histogram
            mean = 0.
            for ix in range(ks_plot.GetXaxis().GetNbins()):
                mean += ks_plot.GetBinContent(ix + 1)
            mean /= ks_plot.GetXaxis().GetNbins()

            std_dev = 0.
            for ix in range(ks_plot.GetXaxis().GetNbins()):
                bin_content = ks_plot.GetBinContent(ix + 1)
                std_dev += (bin_content - mean) ** 2
            std_dev = sqrt(std_dev / ks_plot.GetXaxis().GetNbins())

            # Create TLine objects
            line = TLine(ks_plot.GetXaxis().GetXmin(), mean, ks_plot.GetXaxis().GetXmax(), mean)
            line.SetLineColor(ROOT.kOrange)
            line.SetLineStyle(2)
            line.SetLineWidth(2)
            line.Draw("same")

            line_down = TLine(ks_plot.GetXaxis().GetXmin(), mean - std_dev, ks_plot.GetXaxis().GetXmax(), mean - std_dev)
            line_down.SetLineColor(ROOT.kGreen)
            line_down.SetLineStyle(2)
            line_down.SetLineWidth(2)
            line_down.Draw("same")

            line_up = TLine(ks_plot.GetXaxis().GetXmin(), mean + std_dev, ks_plot.GetXaxis().GetXmax(), mean + std_dev)
            line_up.SetLineColor(ROOT.kGreen)
            line_up.SetLineStyle(2)
            line_up.SetLineWidth(2)
            line_up.Draw("same")

            line_d = TLine(ks_plot.GetXaxis().GetXmin(), ks_cv, ks_plot.GetXaxis().GetXmax(), ks_cv)
            line_d.SetLineColor(ROOT.kRed)
            line_d.SetLineStyle(2)
            line_d.SetLineWidth(2)
            line_d.Draw("same")

            # Create legend
            leg = TLegend(0.6, 0.7, 0.8, 0.90)
            leg.AddEntry(line, "Mean = {:.2f}".format(mean), "l")
            leg.AddEntry(line_down, "STD = {:.2f}".format(std_dev), "l")
            leg.AddEntry(line_d, "D_Critical = {:.2f}, #alpha = {:.2f}".format(float(ks_cv), float(alpha)), "l")
            leg.Draw("same")

            if debug:
                canvas.Print("{}_KabothSkwarczynskiDebug.pdf".format(file_name), "pdf")
            canvas.Print("{}_KabothSkwarczynski.pdf".format(file_name), "pdf")

            ks_dir.cd()
            ks_plot.Write()
            del data_poly
            del poly_mc
            del ks_plot
        canvas.Print("{}_KabothSkwarczynski.pdf]".format(file_name), "pdf")
        if debug:
            canvas.Print("{}_KabothSkwarczynskiDebug.pdf]".format(file_name), "pdf")
    canvas.SetRightMargin(right_margin)
    canvas.SetBottomMargin(bottom_margin)

if __name__ == "__main__":
    # Initialize input and output files
    input_file_names = ["PostPredND280.root"]
    output_file_names = ["output.root"]

    input_files = [TFile.Open(name, "READ") for name in input_file_names]
    output_files = [TFile.Open(name, "RECREATE") for name in output_file_names]

    # Sample directory and name vectors
    sample_directory_vector = []
    sample_name_vector = []

    # Fill sample names and directories
    for infile in input_files:
        prepare_nd_samples(infile, sample_name_vector, sample_directory_vector, True)

    # Create canvas
    canvas = TCanvas("canvas", "Kaboth-Skwarczynski Test", 800, 600)

    # Perform Kaboth Skwarczynski test
    kaboth_skwarczynski_test(canvas, input_file_names, input_files, output_files, sample_directory_vector, sample_name_vector)

    # Close files
    for file in input_files + output_files:
        file.Close()
