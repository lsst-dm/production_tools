import numpy as np

def mk_table_value(t, metric_defs, val_col_name, sig_col_name, n):
    if val_col_name in t.columns and sig_col_name in t.columns:
        val = t[val_col_name][n]
        val_str = f"{val:.3g}"
        sig = t[sig_col_name][n]
        sig_str = f"{sig:.3g}"
    elif val_col_name in t.columns and sig_col_name not in t.columns:
        val = t[val_col_name][n]
        val_str = f"{val:.3g}"
        sig_str = "-"
    elif val_col_name not in t.columns and sig_col_name in t.columns:
        val_str = "_"
        sig = t[sig_col_name][n]
        sig_str = f"{sig:.3g}"
    else:
        return None, None

    if np.isnan(val):
        val_str = f"<FONT CLASS=nanValue>{val:.3g} </FONT>"
    if np.isnan(sig):
        sig_str = f"<FONT CLASS=nanValue>{sig:.3g}</FONT>\n"
    if val_col_name in metric_defs:
        high_val = metric_defs[val_col_name]["highThreshold"]
        low_val = metric_defs[val_col_name]["lowThreshold"]
        link = metric_defs[val_col_name]["debugGroup"] + "ReportPage.html"
        if val < low_val or val > high_val:
            #valStr = "<FONT CLASS=badValue><A HREF = " + link + f">{val:.3g}</A></FONT> "
            val_str = f"<FONT CLASS=badValue>{val:.3g}</FONT>"
    if sig_col_name in metric_defs:
        high_sig = metric_defs[sig_col_name]["highThreshold"]
        low_sig = metric_defs[sig_col_name]["lowThreshold"]
        if sig < low_sig or sig > high_sig:
            #sigStr = "<FONT CLASS=badValue><A HREF = " + link + f">{sig:.3g}</A></FONT>\n"
            sig_str = f"<FONT CLASS=badValue>{sig:.3g}</FONT>\n"

    return val_str, sig_str


def mk_table_headers(t, col_dict):

    col_first = []
    bands = []
    for col in t.columns:
        col_sections = col.split("_")
        for section in col_sections:
            if len(section) == 1:
                bands.append(section)
            col_first.append(col.split("_")[0])

    bands = list(set(bands))

    table_headers = col_dict["table_cols"]
    for shape_col in col_dict["shape_cols"]:
        table_headers.append(shape_col + "<BR>High SN Stars")
        table_headers.append(shape_col + "<BR>Low SN Stars")
    for col in col_dict["stellar_locus_cols"]:
        table_headers.append(col)

    header_list = []
    link_list = []
    header_dict = {}
    for header in table_headers:
        if header == "failed metrics":
            # Needs to link to metric fail page
            header_dict[header] = "metrics.index"
        elif header == "corners":
            # Needs to link to metric summary page
            header_dict[header] = "metrics.index"
        else:
            # Needs to link to the correct point on the histogram page
            #headerList.append("<A HREF = histPage.html#" + header.split("<BR>")[0] + f">{header}</A>")
            header_dict[header] = "metrics.index"

    return header_dict, bands


def mk_tract_cell(tract):
    #tractStr = "<a href='summary" + str(tract) + ".html' class=tract>"
    #tractStr += str(tract) + "</a>"
    tract_str = str(tract)

    return tract_str


def mk_summary_plot_cell(tract):
    plot_str = "<IMG SRC='static/summaryCalexp_" + str(tract) + "_i.png' CLASS=thumbnail>"
    return plot_str


def mk_patch_num_cell(t, n, bands):
    patch_str = ""
    for band in ["g", "r", "i", "z", "y"]:
        if band in bands:
            patch_col = "coaddPatchCount_" + band + "_patchCount"
            patch_str += "<B>" + band + "</B>: " + str(int(t[patch_col][n])) + "<BR>\n"

    return patch_str


def mk_shape_cols(t, metric_defs, n, bands, col_dict):
    shape_strs = []
    for col in col_dict["shape_cols"]:
        for sn in ["highSNStars", "lowSNStars"]:
            shape_str = ""
            for band in ["g", "r", "i", "z", "y"]:
                if band in bands:
                    val_col_name = col + "_" + band + "_" + sn + "_median"
                    sig_col_name = col + "_" + band + "_" + sn + "_sigmaMad"
                    val_str, sig_str = mk_table_value(t, metric_defs, val_col_name, sig_col_name, n)
                    shape_str += "<B>" + band + f"</B>: " + val_str + "  <B>&sigma;</B>: "
                    shape_str += sig_str + "<BR>\n"
            shape_strs.append(shape_str)
    return shape_strs


def mk_stellar_locus_cols(t, metric_defs, n, col_dict):
    row_strs = []
    for col in col_dict["stellar_locus_cols"]:
        for (flux, flux1) in zip(["psfFlux", "CModel"], ["PSF", "CModel"]):
            if col[0] == "w" or col[0] == "x":
                flux1 += "P"
            val_col_name = col + flux1 + "_" + col + "_" + flux + "_median"
            sig_col_name = col + flux1 + "_" + col + "_" + flux + "_sigmaMAD"
            val_str, sig_str = mk_table_value(t, metric_defs, val_col_name, sig_col_name, n)
            if val_str is None:
                continue
            row_str = "<B>Med</B>: " + val_str + "  <B>&sigma;</B>: " + sig_str + "<BR>\n"
        row_strs.append(row_str)

    return row_strs



