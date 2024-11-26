# This file is part of production-tools.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import numpy as np


class cell_entry:

    def __init__(self):

        self.num_bad = 0
        self.link = "noInfo"
        self.debug_group = None
        self.val_str = None
        self.sig_str = None


class cell_contents:

    def __init__(self):
        self.num_fails = 0
        self.text = ""
        self.link = "noInfo"
        self.debug_group = None


def mk_table_value(row, metric_defs, val_col_name, sig_col_name):
    """Turn the values from the given columns into
    formatted cell contents.

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    val_col_name : `str`
        The name of the metric column
    sig_col_name : `str`
        The associated sigma column
    n : `n`
        The row number

    Returns
    -------
    val_str : `str`
        The formatted string for the metric value
    sig_str : `str`
        The formatted string for the sigma value
    bad_val : `int`
        Number of metrics outside the threshold
    link : `str`
        The page that the bad value should link to
    debug_group : `str`
        The group of metrics that this metric belongs to

    Notes
    -----
    Returns None for everything if the given metric name
    isn't in the table.
    """

    cell = cell_entry()
    # Make a string of the val and sig columns
    if val_col_name in row.columns and sig_col_name in row.columns:
        val = row[val_col_name]
        cell.val_str = f"{val:.3g}"
        sig = row[sig_col_name]
        cell.sig_str = f"{sig:.3g}"
    elif val_col_name in row.columns and sig_col_name not in row.columns:
        val = row[val_col_name]
        cell.val_str = f"{val:.3g}"
        sig = None
        cell.sig_str = "-"
    elif val_col_name not in row.columns and sig_col_name in row.columns:
        cell.val_str = "-"
        val = None
        sig = row[sig_col_name]
        cell.sig_str = f"{sig:.3g}"
    else:
        return cell

    bad_val = 0

    cell.link = "metrics.report_page"
    if val_col_name in metric_defs:
        cell.debug_group = metric_defs[val_col_name]["debugGroup"]
    else:
        cell.debug_group = None

    # Add formatting to the string if there are thresholds
    # for the metric
    if np.isnan(val):
        cell.val_str = f"<FONT CLASS=nanValue>{val:.3g} </FONT>"
    if np.isnan(sig):
        cell.sig_str = f"<FONT CLASS=nanValue>{sig:.3g}</FONT>\n"
    if val_col_name in metric_defs:
        high_val = metric_defs[val_col_name]["highThreshold"]
        low_val = metric_defs[val_col_name]["lowThreshold"]
        cell.debug_group = metric_defs[val_col_name]["debugGroup"]
        if val < low_val or val > high_val:
            cell.val_str = f"<FONT CLASS=badValue>{val:.3g}</FONT>"
            bad_val += 1
    if sig_col_name in metric_defs:
        high_sig = metric_defs[sig_col_name]["highThreshold"]
        low_sig = metric_defs[sig_col_name]["lowThreshold"]
        if sig < low_sig or sig > high_sig:
            cell.sig_str = f"<FONT CLASS=badValue>{sig:.3g}</FONT>\n"
            bad_val += 1

    cell.num_bad = bad_val
    return cell


def mk_table_headers(t, col_dict):
    """Make column headers

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    col_dict : `dict`
        Dictionary of the grouped column headers

    Returns
    -------
    header_dict : `dict`
        A dictionary of the headers and what pages they should link to
    bands : `list`
        The bands that the metrics cover
    """

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
    for col in col_dict["photom_cols"]:
        table_headers.append(col)
    for col in col_dict["sky_cols"]:
        table_headers.append(col + "<BR>mean, stdev")
        table_headers.append(col + "<BR>median, sigmaMAD")

    header_list = []
    link_list = []
    header_dict = {}
    for header in table_headers:
        if header == "failed metrics":
            # Needs to link to metric fail page
            header_dict[header] = "metrics.histograms"
        elif header == "corners":
            # Needs to link to metric summary page
            header_dict[header] = "metrics.histograms"
        else:
            # Needs to link to the correct point on the histogram page
            # headerList.append("<A HREF = histPage.html#" + header.split("<BR>")[0] + f">{header}</A>")
            header_dict[header] = "metrics.histograms"

    return header_dict, bands


def mk_tract_cell(tract):
    """Make the content of the tract cell

    Parameters
    ----------
    tract : `float`
        The tract number

    Returns
    -------
    tract_str : `str`
        The link that the tract should go to
    """
    cell = cell_contents()
    cell.text = "metrics.single_tract"

    return cell


def mk_summary_plot_cell(tract):
    """Make the contents of the summary plot cell

    Parameters
    ----------
    tract : `float`

    Returns
    -------
    plot_str : `str`

    Notes
    -----
    This needs updating with a plot navigator link
    """
    # plot_str = "<IMG SRC='static/summaryCalexp_" + str(tract) + "_i.png' CLASS=thumbnail>"
    cell = cell_contents()
    cell.text = "nav link needed"
    return cell


def mk_patch_num_cell(t, n, bands):
    """Make patch number cell content

    Parameters
    ----------
     t : `astropy.table.Table`
        Table of metrics
    n : `n`
        The row number
    bands : `list`
        A list of the bands the metrics are in

    Returns
    -------
    patch_str : `str`
        The formatted number of patches in each band
    """
    cell = cell_contents()
    patch_str = ""
    for band in ["u", "g", "r", "i", "z", "y"]:
        if band in bands:
            patch_col = "coaddPatchCount_" + band + "_patchCount"
            patch_str += "<B>" + band + "</B>: " + str(int(t[patch_col][n])) + "<BR>\n"

    cell.text = patch_str
    return cell


def mk_shape_cols(row, metric_defs, bands, cols):
    """Make shape column cell contents

    Parameters
    ----------
    row : `astropy.table.Table`
        A row of the metrics table
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    bands : `list`
        A list of the bands the metrics are in
    cols : `list`
        A list of columns to format

    Returns
    -------
    shape_strs : `tuple` of `str`
        A tuple of the formatted strings for the shape columns
    """
    shape_cells = []
    for col in cols:
        for sn in ["highSNStars", "lowSNStars"]:
            debug_group_all = None
            full_cell = cell_contents()
            for band in ["u", "g", "r", "i", "z", "y"]:
                if band in bands:
                    val_col_name = col + "_" + band + "_" + sn + "_median"
                    sig_col_name = col + "_" + band + "_" + sn + "_sigmaMad"
                    cell_entry = mk_table_value(
                        row, metric_defs, val_col_name, sig_col_name
                    )
                    full_cell.num_fails += cell_entry.num_bad
                    full_cell.text += f"<B>{band}</B>: {cell_entry.val_str} "
                    full_cell.text += f"<B>&sigma;</B>: {cell_entry.sig_str}<BR>\n"
                    if cell_entry.debug_group is not None:
                        full_cell.debug_group = cell_entry.debug_group
                    full_cell.link = cell_entry.link
            shape_cells.append(full_cell)
    return shape_cells


def mk_stellar_locus_cols(t, metric_defs, n, cols):
    """Make stellar locus column cell contents

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    n : `n`
        The row number
    cols : `list`
        A list of the columns to format

    Returns
    -------
    row_strs : `tuple` of `str`
        A tuple of the formatted strings for the stellar locus columns
    """
    row_cells = []
    for col in cols:
        for flux, flux1 in zip(["psfFlux", "cModelFlux"], ["PSF", "CModel"]):
            if (col[0] == "w" or col[0] == "x") and flux1 == "PSF":
                flux1 += "P"
            full_cell = cell_contents()
            val_col_name = col + flux1 + "_" + col + "_" + flux + "_median"
            sig_col_name = col + flux1 + "_" + col + "_" + flux + "_sigmaMAD"
            cell_entry = mk_table_value(t[n], metric_defs, val_col_name, sig_col_name)
            if cell_entry.val_str is None:
                continue
            full_cell.text += (
                "<B>"
                + flux
                + "</B><BR><B>Med</B>: "
                + cell_entry.val_str
                + "  <B>&sigma;</B>: "
                + cell_entry.sig_str
                + "<BR>"
            )
            full_cell.text += "<BR>\n"
            full_cell.num_fails += cell_entry.num_bad
            if cell_entry.debug_group is not None:
                full_cell.debug_group = cell_entry.debug_group
            full_cell.link = cell_entry.link
        row_cells.append(full_cell)

    return row_cells


def mk_num_inputs_cell(t, metric_defs, n, bands):
    """Format the number of inputs cell

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    n : `n`
        The row number
    bands : `list`
        A list of the bands the metrics are in

    Returns
    -------
    row_str : `str`
        A string of the formatted cell contents
    """

    row_str = ""
    full_cell = cell_contents()
    for band in ["u", "g", "r", "i", "z", "y"]:
        if band in bands:
            val_col_name = "coaddInputCount_" + band + "_inputCount_median"
            sig_col_name = "coaddInputCount_" + band + "_inputCount_sigmaMad"

            cell_entry = mk_table_value(t[n], metric_defs, val_col_name, sig_col_name)
            full_cell.text += (
                "<B>" + band + "</B>:" + cell_entry.val_str + " <B>&sigma;</B> "
            )
            full_cell.text += cell_entry.sig_str + "<BR>\n"
            if cell_entry.debug_group is not None:
                full_cell.debug_group = cell_entry.debug_group

    return full_cell


def mk_photom_cols(t, metric_defs, n, bands, cols):
    """Make photometry column cell contents

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    n : `n`
        The row number
    bands : `list`
        A list of the bands the metrics are in
    cols : `list`
        A list of the columns to format

    Returns
    -------
    row_strs : `tuple` of `str`
        A tuple of the formatted strings for the photometry columns
    """
    row_cells = []
    for col in cols:
        full_cell = cell_contents()
        for band in ["u", "g", "r", "i", "z", "y"]:
            if band in bands:
                for part in ["psf_cModel_diff"]:
                    val_col_name = col + "_" + band + "_" + part + "_median"
                    sig_col_name = col + "_" + band + "_" + part + "_sigmaMad"
                    cell_entry = mk_table_value(
                        t[n], metric_defs, val_col_name, sig_col_name
                    )

                    full_cell.text += f"<B>{band}</B>: {cell_entry.val_str}  "
                    full_cell.text += f"<B>&sigma;</B>: {cell_entry.sig_str}<BR>\n"
                    full_cell.num_fails += cell_entry.num_bad
                    full_cell.debug_group = cell_entry.debug_group
                    full_cell.link = cell_entry.link
        row_cells.append(full_cell)

    return row_cells


def mk_sky_cols(t, metric_defs, n, bands, cols):
    """Make sky column cell content

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    n : `n`
        The row number
    bands : `list`
        A list of the bands the metrics are in
    cols : `list`
        A list of the columns to format

    Returns
    -------
    row_strs : `tuple` of `str`
        A tuple of the formatted strings for the sky columns
    """
    row_cells = []
    for col in cols:
        for stat, dev in [("mean", "stdev"), ("median", "sigmaMAD")]:
            full_cell = cell_contents()
            for band in ["u", "g", "r", "i", "z", "y"]:
                if band in bands:
                    val_col_name = col + "_" + band + "_" + stat + "Sky"
                    sig_col_name = col + "_" + band + "_" + dev + "Sky"
                    cell_entry = mk_table_value(
                        t[n], metric_defs, val_col_name, sig_col_name
                    )
                    full_cell.text += f"<B>{band}</B>: {cell_entry.val_str} "
                    full_cell.text += f"<B>&sigma;</B>: {cell_entry.sig_str}<BR>\n"
                    full_cell.num_fails += cell_entry.num_bad
                    if full_cell.debug_group is not None:
                        full_cell.debug_group = cell_entry.debug_group
            row_cells.append(full_cell)

    return row_cells
