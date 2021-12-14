from pyecharts.charts import Line
from pyecharts import options as opts
import os
import sys
import json

# unsmoothed_total_sequences # this variant case in this country
# unsmoothed_cluster_sequences # total covid case in this country
# cluster / total

countries = ["USA"]
# variants = ["20A.EU1", "20A.EU2", "20A.S.126A",
#             "20A.S.210T", "20B.S.732A", "20B.S.796H", "20H.Beta.V2", "20I.Alpha.V1", "20J.Gamma.V3", "21A.21B", "21A.Delta.S.K417", 
#             "21A.Delta", "21B.Kappa", "21C.Epsilon", "21D.Eta"]
variants = ['S.Q677H.Mockingbird', 'S.A222', 'DanishCluster', '21A.21B', 'S.H655', 'S.S98F', '20A.S.126A', 'Omicron.Similar', 'S.Q677R.Roadrunner', 'S.A626S', 'S.K417', '20H.Beta.V2', '21F.Iota', 'S.Y453F', '20A.S.210T', '20I.Alpha.V1', 'S.D80Y', 'EUClusters', '21I.Delta', 'S.Q677P.Pelican', 'S.Q677H.Robin1', '21D.Eta', 'Delta.145H', 'Delta.250I', 'S.Q677H.Yellowhammer', '21A.Delta', '20A.EU1', '21B.Kappa', '21C.Epsilon', 'S.P681',
    'S.H69-', 'ORF1a.S3675', 'S.Q677H.Robin2', 'S.Q677H.Heron', '21L', 'S.T572', '20J.Gamma.V3', 'S.Q613', '21K.21L', 'SwissClusters', 'S.N439K', 'Delta.ORF1a3059F', '20B.S.796H', '20A.EU2', '21K.Omicron', 'Delta.N.412R', 'S.E484', 'S.Y145', 'S.Q677H.Quail', 'S.Q677', 'S.V1122L', '21H.Mu', 'S.N501', '21J.Delta', 'USAClusters', 'S.Q677H.Bluebird', 'S.Y144-', 'S.L18', '21G.Lambda', '20B.S.732A', 'Delta.299I', '21A.Delta.S.K417', 'S.S477']
data_x = []

for countryIndex in range(len(countries)):
    country = countries[countryIndex]
    line = Line(init_opts=opts.InitOpts(width="1500px"))
    line.set_global_opts(title_opts=opts.TitleOpts(title=country + " - Variant Display"),
                         legend_opts=opts.LegendOpts(type_="scroll", pos_left="right", orient="vertical"))
    for variantIndex in range(len(variants)):
        # if variantIndex > 3: break
        variant = variants[variantIndex]
        fileName = "./cluster_tables/" + variant + "_data.json"
        f = open(fileName)
        data = json.load(f)
        if countryIndex == 0 and variantIndex == 0: data_x = data[country]["week"]
        if country not in data: continue
        data_y = data[country]["unsmoothed_cluster_sequences"]
        # print(len(data_y))
        # print(len(data_x))
        if (len(data_y) != len(data_x)): continue
        f.close()
        print(variant)
        line.add_xaxis(data_x)
        # line.add_yaxis(variant, data_y, is_smooth=True, is_stack=False, is_label_show=False, is_symbol_show=True,
        #                is_fill=True, line_opacity=0.2, area_opacity=0.2, mark_point=["max"], mark_point_symbolsize=60)
        line.add_yaxis(variant, data_y, is_smooth=True)
        line.set_series_opts(label_opts=opts.LabelOpts(is_show=False), 
                             markpoint_opts=opts.MarkPointOpts(
                                data=[
                                    opts.MarkPointItem(type_='max', name='maximum'),
                                ], symbol_size = 60),
                             areastyle_opts=opts.AreaStyleOpts(opacity=0.2)

        )

    # line.show_config()
    line.render()


