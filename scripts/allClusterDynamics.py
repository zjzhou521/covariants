# Run this script from within an 'ncov' directory ()
# which is a sister directory to 'covariants'
# See the 'WHERE FILES WRITE OUT' below to see options on modifying file paths
# Importantly, ensure you create a real or fake 'ncov_cluster' output directory - or change it!

# TLDR: make sure 'ncov' and 'covariants' repos are in same directory
# 'ncov_cluster' should also be there - or create empty folder to match paths below

######### INPUT FILES
# This requires two files that cannot be distributed publicly:
# ncov/data/meatdata.tsv (can be downloaded from GISAID as 'nextmeta')
# ncov/results/sequence-diagnostics.tsv
#    this file unfortunately isn't available but can be generated by running the 'ncov' pipeline.

# For Nextstrain members only:
#       You can get these by downloading the most recent run from AWS
#       (see slack #ncov-gisaid-updates for the command)
#       Or by running an `ncov`` build locally/on cluster until sequence-diagnostics.tsv is generated

######### WHERE FILES WRITE OUT
# If you want to output files to run in `ncov_cluster` to make cluster-focused builds,
# clone this repo so it sits 'next' to ncov: https://github.com/emmahodcroft/ncov_cluster
# and use these paths:
cluster_path = "../ncov_cluster/cluster_profile/"

# Things that write out to cluster_scripts repo (images mostly), use this path:
figure_path = "../covariants/overall_trends_figures/"
tables_path = "../covariants/cluster_tables/"
overall_tables_file = "../covariants/cluster_tables/all_tables.tsv"
acknowledgement_folder = "../covariants/acknowledgements/"
# This assumes that `covariants` sites next to `ncov`
# Otherwise, modify the paths above to put the files wherever you like.
# (Alternatively just create a folder structure to mirror the above)

fmt = "png"  # "pdf"

import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from shutil import copyfile
from collections import defaultdict
from matplotlib.patches import Rectangle
import json
from colors_and_countries import *
from travel_data import *
from helpers import *
from paths import *
from clusters import *
from bad_sequences import *

# run ../cluster_scripts/helpers.py
# run ../cluster_scripts/colors_and_countries.py
# run ../cluster_scripts/travel_data.py
# run ../cluster_scripts/paths.py
# run ../cluster_scripts/paths.py

# Get diagnostics file - used to get list of SNPs of all sequences, to pick out seqs that have right SNPS
diag_file = "results/sequence-diagnostics.tsv"
diag = pd.read_csv(diag_file, sep="\t", index_col=False)
# Read metadata file
input_meta = "data/metadata.tsv"
meta = pd.read_csv(input_meta, sep="\t", index_col=False)
meta = meta.fillna("")

########

# Define SNPs that will determine what's in our cluster
# Originally I used all 6 SNPs to define - but better to use 4 and grab 'nearby' seqs

# need to subtract 1 for 0-based numbering in diagnositcs script
# real mutations are : 445, 6286, 22227, 26801, 28932, 29645
# snps = [444, 6285, 22226, 26800, 28931, 29644]
# snps = [22226, 28931, 29644] #now excludes 6285

# Other clusters I wanted to compare against:
# snps = [9129, 28867] # another cluster - but mostly swiss, no pattern
# snps = [3098, 4959] # another cluster = the diverged C->T one, no pattern <- potentially most interesting tho
# snps = [15971, 28758] # mixed serbian latvian swiss cluster, no pattern
# snps = [22991] #4542] #26875] #S 477N - filer Europe only, below
# snps = [22991, 7539] #australia version


# ask user if they want to write-out files or not:
print_files = False
print_answer = input("\nWrite out files?(y/n) (Enter is no): ")
if print_answer in ["y", "Y", "yes", "YES", "Yes"]:
    print_files = True
print_files2 = True

# default is 222, but ask user what they want - or run all.

clus_to_run = ["S222"]
reask = True

while reask:
    clus_answer = input(
        "\nWhat cluster to run? (Enter for S222) Type 'all' for all, type 'all mink' for all+mink: "
    )
    if len(clus_answer) != 0:
        if clus_answer in clusters.keys():
            print(f"Using {clus_answer}\n")
            clus_to_run = [clus_answer]
            reask = False
        elif "all" in clus_answer:
            clus_to_run = list(clusters.keys())
            if "mink" in clus_answer or "Mink" in clus_answer:
                clus_to_run.append("mink")
            reask = False
        elif clus_answer == "mink" or clus_answer == "Mink":
            clus_to_run = ["mink"]
        else:
            print(f"Not found. Options are: {clusters.keys()}")
    else:
        print("Using default of S222\n")
        reask = False
print("These clusters will be run: ", clus_to_run)

# if running all clusters, clear file so can write again.
if print_files and "all" in clus_answer:
    # clean these files so don't append to last run.
    with open(f"{tables_path}all_tables.md", "w") as fh:
        fh.write("\n")
        fh.write(
            "# Overview of Clusters/Mutations in Europe\n"
            "[Overview of proportion of clusters in selected countries](country_overview.md)\n\n"
            "In the graphs below, countries are displayed in the chart if the country has at least 20 sequences present in the cluster.\n\n"
            "# Mutation Tables and Graphs\n"
            "- [20A.EU1](#20aeu1) _(S:A222V)_ \n"
            "- [20A.EU2](#20aeu2) _(S:S477N)_ \n"
            "- [S:N501](#sn501) \n"
            "- [S:H69-](#sh69-) \n"
            "- [S:N439K](#sn439k) \n"
            "- [S:Y453F](#sy453f) \n"
            "- [S:S98F](#ss98f) \n"
            "- [S:E484](#se484) \n"
            "- [S:D80Y](#sd80y) \n"
            "- [S:A626S](#sa626s) \n"
            "- [S:V1122L](#sv1122l) \n\n"
        )
    with open(overall_tables_file, "w") as fh:
        fh.write("\n")

json_output = {}


for clus in clus_to_run:
    print(f"\nRunning cluster {clus}\n")

    if clus == "mink":
        clus_display = "mink"
        mink_meta = meta[meta["host"].apply(lambda x: x == "Mink")]
        wanted_seqs = list(mink_meta["strain"])

        clusterlist_output = cluster_path + f"/clusters/cluster_mink.txt"
        out_meta_file = cluster_path + f"/cluster_info/cluster_mink_meta.tsv"

    else:
        clus_display = clusters[clus]["build_name"]
        snps = clusters[clus]["snps"]
        if "snps2" in clusters[clus]:
            snps2 = clusters[clus]["snps2"]
        else:
            snps2 = []
        if "gaps" in clusters[clus]:
            gaps = clusters[clus]["gaps"]
        else:
            gaps = []
        if "exclude_snps" in clusters[clus]:
            exclude_snps = clusters[clus]["exclude_snps"]
        else:
            exclude_snps = []

        clusterlist_output = (
            cluster_path + f'/clusters/cluster_{clusters[clus]["build_name"]}.txt'
        )
        out_meta_file = (
            cluster_path
            + f'/cluster_info/cluster_{clusters[clus]["build_name"]}_meta.tsv'
        )

        # get the sequences that we want - which are 'part of the cluster:
        wanted_seqs = []

        for index, row in diag.iterrows():
            strain = row["strain"]
            snplist = row["all_snps"]
            gaplist = row["gap_list"]

            # look for occurance of snp(s) *without* some other snp(s) (to exclude a certain group)
            if (
                snps
                and not pd.isna(snplist)
                and exclude_snps
                and not pd.isna(exclude_snps)
            ):
                intsnp = [int(x) for x in snplist.split(",")]
                if all(x in intsnp for x in snps) and all(
                    x not in intsnp for x in exclude_snps
                ):
                    wanted_seqs.append(row["strain"])

            elif snps and not pd.isna(snplist):
                intsnp = [int(x) for x in snplist.split(",")]
                # this looks for all SNPs in 'snps' OR all in 'snps2' (two nucs that affect same AA, for example)
                if all(x in intsnp for x in snps) or (
                    all(x in intsnp for x in snps2) and len(snps2) != 0
                ):
                    # if meta.loc[meta['strain'] == strain].region.values[0] == "Europe":
                    wanted_seqs.append(row["strain"])
            # look for all locations in gap list
            elif gaps and not pd.isna(gaplist):
                intgap = [int(x) for x in gaplist.split(",")]
                if all(x in intgap for x in gaps):
                    wanted_seqs.append(row["strain"])

    # If seq there and date bad - exclude!
    #    bad_seqs = {
    #        'Spain/VC-IBV-98006466/2020' : "2020-03-07", # There's one spanish seq with date of 7 March - we think this is wrong.
    #        # There are five sequences from UK with suspected bad dates: exclude
    #        'England/LIVE-1DD7AC/2020' : "2020-03-10",
    #        'England/PORT-2D2111/2020' : "2020-03-21",
    #        'England/CAMB-1BA110/2020' : "2020-06-11", # suspected that these ones have reversed dd-mm (are actually 5 and 6 Nov)
    #        'England/CAMB-1BA0F5/2020' : "2020-05-11", # suspected that these ones have reversed dd-mm (are actually 5 and 6 Nov)
    #        'England/CAMB-1BA0B9/2020' : "2020-05-11", # suspected that these ones have reversed dd-mm (are actually 5 and 6 Nov)
    #        'Denmark/DCGC-12020/2020'  : "2020-03-30", # this sequence is identical to other Danish seqs with sample date of Oct/Nov..
    #        'Netherlands/NB-EMC-279/2020'   : "2020-05-08", # seems to be date reversal of day/month
    #        'Italy/APU-IZSPB_321PT/2020'    : "2020-04-11", # seems to be date reversal of day/month
    #        'Tunisia/4107/2020' : "2020-03-18", # date seems to be wrong based on divergence
    #        'Tunisia/3942/2020' : "2020-03-16", # date seems to be wrong based on divergence
    #        'Australia/QLD1278/2020'    : "2020-03-21", #seems to be wrong date - far too diverged
    #        'Australia/QLD1276/2020'    : "2020-03-21", # seems to be wrong date - far too diverged
    #        'Sweden/20-08979/2020'  : "2020-04-06", # too divergent compared to date (seems to be day/month reversed)
    #
    #        'Spain/IB-IBV-99010753/2020'    : "2020-04-21", # temporarily excluded as early date doesn't match divergence - EU1
    #        'Spain/IB-IBV-99010754/2020'    : "2020-04-22", # temporarily excluded as early date doesn't match divergence - EU1
    #        'Spain/IB-IBV-99010756/2020'    : "2020-05-11", # temporarily excluded as early date doesn't match divergence - EU1
    #        'Spain/IB-IBV-99010769/2020'    : "2020-06-18", # temporarily excluded as early date doesn't match divergence - EU2
    #        'Spain/IB-IBV-99010761/2020'    : "2020-05-29", # temporarily excluded as early date doesn't match divergence - EU2
    #        'Italy/LAZ-INMI-92/2020' : "2010-10-26", # year given as 2010
    #        'Italy/LAZ-INMI-93/2020' : "2010-10-26", # year given as 2010
    #        'Italy/LAZ-INMI-94/2020' : "2010-10-27", # year given as 2010
    #        'Italy/LAZ-INMI-95/2020' : "2010-10-27", # year given as 2010
    #        'England/LIVE-DCA612/2020' : "2020-03-07",  # far too diverged compared to sample date
    #        'Netherlands/ZE-EMC-74/2020'    : "2020-06-11", # too diverged compared to date. Suspect is 6 Nov - date reversed
    #        'Spain/RI-IBV-99010966/2009'    : "2009-09-30", # date typed wrong
    #        'Denmark/DCGC-16747/2020'   : "2020-04-20", #overdiverged compared to date
    #        'Tunisia/19695/2020'    : "2020-07-12", #overdivrged compared to date
    #        'Canada/ON-S1598/2020'  : "2020-04-09", #confirmed day-month reversal
    #        'SouthKorea/KDCA0367/2020'  : "2020-04-04" # too divergent given date (11)
    #
    #        #'bat/Yunnan/RaTG13/2013'    : "2013-07-24" #this is RatG13 - legit, but looks weird in table
    #        #'bat/Yunnan/RmYN02/2019'    : "2019-06-25" # bat sequence - legit but looks weird
    #    }

    for key, value in bad_seqs.items():
        bad_seq = meta[meta["strain"].isin([key])]
        if not bad_seq.empty and bad_seq.date.values[0] == value and key in wanted_seqs:
            wanted_seqs.remove(key)

    json_output[clus_display] = {}

    # get metadata for these sequences
    cluster_meta = meta[meta["strain"].isin(wanted_seqs)]

    # remove those with bad dates
    cluster_meta = cluster_meta[cluster_meta["date"].apply(lambda x: len(x) == 10)]
    cluster_meta = cluster_meta[cluster_meta["date"].apply(lambda x: "XX" not in x)]

    bad_dates = 0
    if len(wanted_seqs) != len(cluster_meta):
        bad_dates = len(wanted_seqs) - len(cluster_meta)

    # re-set wanted_seqs
    wanted_seqs = list(cluster_meta["strain"])

    # JAPAN
    # hacky fix to include japan sequences which don't have days
    # manually add in sequences from Japan - just to write out.
    if clus == "S484":
        wanted_seqs.append("Japan/IC-0561/2021")
        wanted_seqs.append("Japan/IC-0562/2021")
        wanted_seqs.append("Japan/IC-0563/2021")
        wanted_seqs.append("Japan/IC-0564/2021")
        # reset metadata
        cluster_meta = cluster_meta[cluster_meta["strain"].isin(wanted_seqs)]

    print("Sequences found: ")
    print(len(wanted_seqs))  # how many are there?
    print("\n")

    if bad_dates:
        print("Sequences with bad dates (excluded): ", bad_dates)
        print("\n")

    # Write out a file of the names of those 'in the cluster' - this is used by ncov_cluster
    # to make a ncov run where the 'focal' set is this cluster.
    if print_files:
        with open(clusterlist_output, "w") as f:
            for item in wanted_seqs:
                f.write("%s\n" % item)

        # Copy file with date, so we can compare to prev dates if we want...
        if clus in clusters:
            build_nam = clusters[clus]["build_name"]
        else:
            build_nam = "mink"
        copypath = clusterlist_output.replace(
            f"{build_nam}",
            "{}-{}".format(build_nam, datetime.date.today().strftime("%Y-%m-%d")),
        )
        copyfile(clusterlist_output, copypath)

    # get metadata for these sequences
    #    cluster_meta = meta[meta['strain'].isin(wanted_seqs)]
    #    observed_countries = [x for x in cluster_meta['country'].unique()]

    # Make a version of N501 which does not have as much UK sequences for increased viewability
    if clus == "S501":
        nouk_501_meta = cluster_meta[
            cluster_meta["country"].apply(lambda x: x != "United Kingdom")
        ]
        # re-set wanted_seqs
        extra501_wanted_seqs = list(nouk_501_meta["strain"])

        noUK_clusterlist_output = (
            cluster_path + f'/clusters/cluster_{clusters[clus]["build_name"]}-noUK.txt'
        )
        noUK_out_meta_file = (
            cluster_path
            + f'/cluster_info/cluster_{clusters[clus]["build_name"]}-noUK_meta.tsv'
        )

        if print_files:
            with open(noUK_clusterlist_output, "w") as f:
                for item in extra501_wanted_seqs:
                    f.write("%s\n" % item)
            build_nam = clusters[clus]["build_name"]
            copypath = noUK_clusterlist_output.replace(
                f"{build_nam}-noUK",
                "{}-noUK-{}".format(
                    build_nam, datetime.date.today().strftime("%Y-%m-%d")
                ),
            )
            copyfile(noUK_clusterlist_output, copypath)
            nouk_501_meta.to_csv(noUK_out_meta_file, sep="\t", index=False)

    # Just so we have the data, write out the metadata for these sequences
    if print_files:
        cluster_meta.to_csv(out_meta_file, sep="\t", index=False)

    observed_countries = [x for x in cluster_meta["country"].unique()]
    # What countries do sequences in the cluster come from?
    print(f"The cluster is found in: {observed_countries}\n")
    if clus != "S222":
        print("Remember, countries are not set for clusters other than S222")

    if len(observed_countries) > len(country_list) and clus == "S222":
        print("\nWARNING!! Appears a new country has come into the cluster!")
        print([x for x in observed_countries if x not in country_list])

    # JAPAN
    # must exclude again or graphing & etc will break
    # manually add in sequences from Japan - just to write out.
    if clus == "S484":
        wanted_seqs.remove("Japan/IC-0561/2021")
        wanted_seqs.remove("Japan/IC-0562/2021")
        wanted_seqs.remove("Japan/IC-0563/2021")
        wanted_seqs.remove("Japan/IC-0564/2021")
        # reset metadata
        cluster_meta = cluster_meta[cluster_meta["strain"].isin(wanted_seqs)]

    # Let's get some summary stats on number of sequences, first, and last, for each country.
    country_info = pd.DataFrame(
        index=observed_countries,
        columns=["first_seq", "num_seqs", "last_seq", "sept_oct_freq"],
    )
    country_dates = {}
    cutoffDate = datetime.datetime.strptime("2020-09-01", "%Y-%m-%d")

    for coun in observed_countries:
        if coun in uk_countries:
            temp_meta = cluster_meta[cluster_meta["division"].isin([coun])]
        else:
            temp_meta = cluster_meta[cluster_meta["country"].isin([coun])]
        country_info.loc[coun].first_seq = temp_meta["date"].min()
        country_info.loc[coun].last_seq = temp_meta["date"].max()
        country_info.loc[coun].num_seqs = len(temp_meta)

        country_dates[coun] = [
            datetime.datetime.strptime(dat, "%Y-%m-%d") for dat in temp_meta["date"]
        ]

        herbst_dates = [x for x in country_dates[coun] if x >= cutoffDate]
        if coun in uk_countries:
            temp_meta = meta[meta["division"].isin([coun])]
        else:
            temp_meta = meta[meta["country"].isin([coun])]
        all_dates = [
            datetime.datetime.strptime(x, "%Y-%m-%d")
            for x in temp_meta["date"]
            if len(x) == 10
            and "-XX" not in x
            and datetime.datetime.strptime(x, "%Y-%m-%d") >= cutoffDate
        ]
        if len(all_dates) == 0:
            country_info.loc[coun].sept_oct_freq = 0
        else:
            country_info.loc[coun].sept_oct_freq = round(
                len(herbst_dates) / len(all_dates), 2
            )

    print(country_info)
    print("\n")

    country_info_df = pd.DataFrame(data=country_info)

    print("\nOrdered list by first_seq date:")
    print(country_info_df.sort_values(by="first_seq"))
    print("\n")

    #######
    # print out the table
    table_file = f"{tables_path}{clus_display}_table.tsv"
    ordered_country = country_info_df.sort_values(by="first_seq")
    ordered_country = ordered_country.drop("sept_oct_freq", axis=1)

    if print_files:
        ordered_country.to_csv(table_file, sep="\t")
        # only write if doing all clusters
        if "all" in clus_answer:
            with open(overall_tables_file, "a") as fh:
                fh.write(f"\n\n## {clus_display}\n")

            ordered_country.to_csv(overall_tables_file, sep="\t", mode="a")

        mrk_tbl = ordered_country.to_markdown()

        url_params = "f_region=Europe"
        if "url_params" in clusters[clus]:
            url_params = clusters[clus]["url_params"]

        #        if clus is "S501":
        #        #    col = "c=gt-S_501&"
        #            filt = ""
        #        if clus is "S69":
        #            col = "c=gt-S_69,501,453&"
        #            filt = ""
        #        if clus is "S453":
        #            col = "c=gt-S_453&"

        # don't print DanishCluster in 'all tables'
        # only print 'all tables' if running 'all clusters'
        if "all" in clus_answer and clus != "DanishCluster":
            with open(f"{tables_path}all_tables.md", "a") as fh:
                fh.write(f"\n\n## {clus_display}\n")
                fh.write(
                    f"[Focal Build](https://nextstrain.org/groups/neherlab/ncov/{clus_display}?{url_params})\n\n"
                )
                if clus == "S501":
                    fh.write(
                        f"Note any pre-2020 Chinese sequences are from SARS-like viruses in bats (not SARS-CoV-2).\n"
                    )
                    fh.write(
                        f"Note that this mutation has multiple amino-acid mutants - these numbers "
                        "refer to _all_ these mutations (Y, S, T).\n"
                    )
                fh.write(mrk_tbl)
                fh.write("\n\n")
                fh.write(
                    f"![Overall trends {clus_display}](/overall_trends_figures/overall_trends_{clus_display}.png)"
                )

        with open(f"{tables_path}{clus_display}_table.md", "w") as fh:
            fh.write(f"\n\n## {clus_display}\n")
            fh.write(
                f"[Focal Build](https://nextstrain.org/groups/neherlab/ncov/{clus_display}?{url_params})\n\n"
            )
            if clus == "S501":
                fh.write(
                    f"Note any pre-2020 Chinese sequences are from SARS-like viruses in bats (not SARS-CoV-2).\n"
                )
                fh.write(
                    f"Note that this mutation has multiple amino-acid mutants - these numbers "
                    "refer to _all_ these mutations (Y, S, T).\n"
                )
            fh.write(mrk_tbl)
            fh.write("\n\n")
            fh.write(
                f"![Overall trends {clus_display}](/overall_trends_figures/overall_trends_{clus_display}.png)"
            )

    # ordered_country.to_markdown(f"{tables_path}all_tables.md", mode='a')

    #######
    # BEGINNING OF PLOTTING

    # We want to look at % of samples from a country that are in this cluster
    # To avoid the up-and-down of dates, bin samples into weeks
    countries_to_plot = country_list
    acknowledgement_table = []
    # Get counts per week for sequences in the cluster
    clus_week_counts = {}
    for coun in observed_countries:
        counts_by_week = defaultdict(int)
        for dat in country_dates[coun]:
            # counts_by_week[dat.timetuple().tm_yday//7]+=1 # old method
            counts_by_week[dat.isocalendar()[1]] += 1  # returns ISO calendar week
        clus_week_counts[coun] = counts_by_week

    # Get counts per week for sequences regardless of whether in the cluster or not - from week 20 only.
    total_week_counts = {}
    for coun in observed_countries:
        counts_by_week = defaultdict(int)
        if coun in uk_countries:
            temp_meta = meta[meta["division"].isin([coun])]
        else:
            temp_meta = meta[meta["country"].isin([coun])]
        # week 20
        for ri, row in temp_meta.iterrows():
            dat = row.date
            if (
                len(dat) == 10 and "-XX" not in dat
            ):  # only take those that have real dates
                dt = datetime.datetime.strptime(dat, "%Y-%m-%d")
                # exclude sequences with identical dates & underdiverged
                if coun == "Ireland" and dat == "2020-09-22":
                    continue

                # wk = dt.timetuple().tm_yday//7  # old method
                wk = dt.isocalendar()[1]  # returns ISO calendar week
                if wk >= 20:
                    counts_by_week[wk] += 1
                    acknowledgement_table.append(
                        [
                            row.strain,
                            row.gisaid_epi_isl,
                            row.originating_lab,
                            row.submitting_lab,
                            row.authors,
                        ]
                    )
        total_week_counts[coun] = counts_by_week

    if print_files:
        with open(
            f"{acknowledgement_folder}{clus}_acknowledgement_table.tsv", "w"
        ) as fh:
            fh.write(
                "#strain\tEPI_ISOLATE_ID\tOriginating lab\tsubmitting lab\tauthors\n"
            )
            for d in acknowledgement_table:
                fh.write("\t".join(d) + "\n")

    # Convert into dataframe
    cluster_data = pd.DataFrame(data=clus_week_counts)
    total_data = pd.DataFrame(data=total_week_counts)

    # sort
    total_data = total_data.sort_index()
    cluster_data = cluster_data.sort_index()

    def marker_size(n):
        if n > 100:
            return 150
        elif n > 30:
            return 100
        elif n > 10:
            return 70
        elif n > 3:
            return 50
        elif n > 1:
            return 20
        else:
            return 5

    # Only plot countries with >= X seqs
    min_to_plot = 20
    # if clus == "S222":
    #    min_to_plot = 200

    countries_to_plot = country_info_df[country_info_df.num_seqs > min_to_plot].index

    if len(countries_to_plot) > len(colors):
        print("\nWARNING!! NOT ENOUGH COLORS FOR PLOTTING!")

    if clus == "S222":
        country_styles_custom = country_styles
    else:
        unused_countries = [x for x in country_list if x not in countries_to_plot]
        country_styles_custom = {}
        for x in countries_to_plot:
            if x in country_styles.keys():
                country_styles_custom[x] = country_styles[x]
            else:
                country_styles_custom[x] = country_styles[unused_countries.pop(0)]

    # Make a plot
    repeat = 1
    if clus == "S222":
        repeat = 2

    while repeat > 0:

        # fig = plt.figure(figsize=(10,5))
        # fig, axs=plt.subplots(1,1, figsize=(10,5))
        fs = 14
        # fig, (ax1, ax2, ax3) = plt.subplots(nrows=3, sharex=True,figsize=(10,7),
        #                                    gridspec_kw={'height_ratios':[1,1,3]})
        # Change to just show Travel to spain only. see above for old 3 panel version
        if repeat == 2:
            fig, (ax1, ax3) = plt.subplots(
                nrows=2,
                sharex=True,
                figsize=(10, 6),
                gridspec_kw={"height_ratios": [1, 3]},
            )
        else:
            fig, ax3 = plt.subplots(1, 1, figsize=(10, 5), dpi=72)

        if repeat == 2:
            i = 0
            for coun in travel_order:
                if coun in q_free_to_spain:
                    q_times = q_free_to_spain[coun]
                    strt = datetime.datetime.strptime(q_times["start"], "%Y-%m-%d")
                    end = datetime.datetime.strptime(q_times["end"], "%Y-%m-%d")
                    y_start = i * 0.022
                    height = 0.02
                    ax1.add_patch(
                        Rectangle(
                            (strt, y_start),
                            end - strt,
                            height,
                            ec=country_styles_custom[coun]["c"],
                            fc=country_styles_custom[coun]["c"],
                        )
                    )

                    ax1.text(strt, y_start + 0.003, q_times["msg"], fontsize=fs * 0.8)
                    if coun == "Denmark":
                        strt = datetime.datetime.strptime(
                            q_free_to_spain["Denmark2"]["start"], "%Y-%m-%d"
                        )
                        end = datetime.datetime.strptime(
                            q_free_to_spain["Denmark2"]["end"], "%Y-%m-%d"
                        )
                        ax1.add_patch(
                            Rectangle(
                                (strt, y_start),
                                end - strt,
                                height,
                                ec=country_styles_custom[coun]["c"],
                                fc="none",
                                hatch="/",
                            )
                        )
                        ax1.text(
                            strt,
                            y_start + 0.003,
                            q_free_to_spain["Denmark2"]["msg"],
                            fontsize=fs * 0.8,
                        )
                i = i + 1
            ax1.set_ylim([0, y_start + height])
            ax1.text(
                datetime.datetime.strptime("2020-05-03", "%Y-%m-%d"),
                y_start,
                "Quarantine-free",
                fontsize=fs,
            )
            ax1.text(
                datetime.datetime.strptime("2020-05-03", "%Y-%m-%d"),
                y_start - height - 0.005,
                "Travel to/from Spain",
                fontsize=fs,
            )
            ax1.text(
                datetime.datetime.strptime("2020-05-03", "%Y-%m-%d"),
                y_start - height - height - 0.01,
                "(on return)",
                fontsize=fs,
            )
            ax1.get_yaxis().set_visible(False)

        # for a simpler plot of most interesting countries use this:
        for coun in [x for x in countries_to_plot]:
            week_as_date, cluster_count, total_count = non_zero_counts(
                cluster_data, total_data, coun
            )
            # remove last data point if that point as less than frac sequences compared to the previous count
            week_as_date, cluster_count, total_count = trim_last_data_point(
                week_as_date, cluster_count, total_count, frac=0.1, keep_count=10
            )

            json_output[clus_display][coun] = {}
            json_output[clus_display][coun]["week"] = [
                datetime.datetime.strftime(x, "%Y-%m-%d") for x in week_as_date
            ]
            json_output[clus_display][coun]["total_sequences"] = [
                int(x) for x in total_count
            ]
            json_output[clus_display][coun]["cluster_sequences"] = [
                int(x) for x in cluster_count
            ]

            ax3.plot(
                week_as_date,
                cluster_count / total_count,
                color=country_styles_custom[coun]["c"],
                linestyle=country_styles_custom[coun]["ls"],
                label=coun,
            )
            ax3.scatter(
                week_as_date,
                cluster_count / total_count,
                s=[marker_size(n) for n in total_count],
                color=country_styles_custom[coun]["c"],
                linestyle=country_styles_custom[coun]["ls"],
            )

        for ni, n in enumerate([0, 1, 3, 10, 30, 100]):
            ax3.scatter(
                [week_as_date[0]],
                [0.08 + ni * 0.07],
                s=marker_size(n + 0.1),
                edgecolor="k",
                facecolor="w",
            )
            ax3.text(week_as_date[1], 0.06 + ni * 0.07, f"n>{n}" if n else "n=1")
            #          color=country_styles[coun]['c'], linestyle=country_styles[coun]['ls'], label=coun)

        ax3.text(datetime.datetime(2020, 10, 1), 0.9, f"{clus_display}", fontsize=fs)
        plt.legend(ncol=1, fontsize=fs * 0.8, loc=2)
        fig.autofmt_xdate(rotation=30)
        ax3.tick_params(labelsize=fs * 0.8)
        ax3.set_ylabel("frequency", fontsize=fs)
        max_date = country_info_df["last_seq"].max()
        ax3.set_ylim(0, 1)
        ax3.set_xlim(
            datetime.datetime(2020, 5, 1),
            datetime.datetime.strptime(max_date, "%Y-%m-%d"),
        )
        plt.show()
        plt.tight_layout()

        # spain opens borders
        if clus == "S222":
            ax3.text(
                datetime.datetime.strptime("2020-06-21", "%Y-%m-%d"),
                0.05,
                "Spain opens borders",
                rotation="vertical",
                fontsize=fs * 0.8,
            )

        travel = ""
        if repeat == 2:
            travel = "Travel"
        if print_files:
            plt.savefig(figure_path + f"overall_trends_{clus_display}{travel}.{fmt}")
            trends_path = figure_path + f"overall_trends_{clus_display}{travel}.{fmt}"
            copypath = trends_path.replace(
                f"trends_{clus_display}{travel}",
                "trends-{}".format(datetime.date.today().strftime("%Y-%m-%d")),
            )
            copyfile(trends_path, copypath)

        repeat = repeat - 1

        if print_files:
            with open(tables_path + f"{clus_display}_data.json", "w") as fh:
                json.dump(json_output[clus_display], fh)
