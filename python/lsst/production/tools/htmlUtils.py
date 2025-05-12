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


def make_table_value(row, metric_defs, val_col_name, sig_col_name):
    """Turn the values from the given columns into
    formatted cell contents.

    Parameters
    ----------
    row : `astropy.table.row.Row`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    val_col_name : `str`
        The name of the metric column
    sig_col_name : `str`
        The associated sigma column

    Returns
    -------
    cell : `cell_entry`
        Contains the attributes:
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
    if sig is None:
        cell.sig_str = ""
    elif np.isnan(sig):
        cell.sig_str = f"<FONT CLASS=nanValue>{sig:.3g}</FONT>\n"
    if val is None:
        cell.val_str = ""
    elif np.isnan(val):
        cell.val_str = f"<FONT CLASS=nanValue>{val:.3g} </FONT>"
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


def make_table_headers(t, table_headers):
    """Make column headers

    Parameters
    ----------
    t : `astropy.table.Table`
        Table of metrics
    table_headers : `list`
        A list of the column headers

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


def make_id_val_cell(id_val):
    """Make the content of the tract cell

    Parameters
    ----------
    id_val : `float`
        The id number of the tract/visit

    Returns
    -------
    cell : `cell_contents`
        cell.text is the link that the tract should go to
    """
    cell = cell_contents()
    cell.text = "metrics.single_tract"

    return cell


def make_general_cell(row, col):
    """Make the content of the tract cell

    Parameters
    ----------
    row : `astropy.table.row.Row`
        The row of the metrics table to make the cell from

    col : `str`
        The column name to make the cell from

    Returns
    -------
    cell : `cell_contents`
        cell.text is the link that the tract should go to
    """
    cell = cell_contents()
    cell.text = str(row[col])

    return cell


def make_summary_plot_cell(tract):
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
    # This is not currently used but is being kept
    # so that when we have the needed infrastructure
    # it is ready
    # plot_str = "<IMG SRC='static/summaryCalexp_" + str(tract) + "_i.png' CLASS=thumbnail>"
    cell = cell_contents()
    cell.text = "nav link needed"
    return cell


def make_patch_num_cell(row, bands):
    """Make patch number cell content

    Parameters
    ----------
    row : `astropy.table.row.Row`
        A row from the table of metrics
    bands : `list`
        A list of the bands the metrics are in

    Returns
    -------
    cell : `cell_contents`
        cell.text is the string for the patch cell
    """
    cell = cell_contents()
    patch_str = ""
    for band in ["u", "g", "r", "i", "z", "y"]:
        if band in bands:
            patch_col = "coaddPatchCount_" + band + "_patchCount"
            if patch_col not in row.columns:
                patch_str += "<B>" + band + "</B>: - <BR>\n"
            else:
                patch_str += "<B>" + band + "</B>: " + str(int(row[patch_col])) + "<BR>\n"

    cell.text = patch_str
    return cell


def make_shape_cols(row, metric_defs, bands, cols):
    """Make shape column cell contents

    Parameters
    ----------
    row : `astropy.table.row.Row`
        A row of the metrics table
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    bands : `list`
        A list of the bands the metrics are in
    cols : `list`
        A list of columns to format

    Returns
    -------
    shape_cells : `list` of `cell_contents`
        A list of cells that contain the shape information
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
                    cell_entry = make_table_value(
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


def make_stellar_locus_cols(row, metric_defs, cols):
    """Make stellar locus column cell contents

    Parameters
    ----------
    row : `astropy.table.row.Row`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
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
            cell_entry = make_table_value(row, metric_defs, val_col_name, sig_col_name)
            if cell_entry.val_str is None:
                continue
            full_cell.text += f"<B>{flux}</B><BR><B>Med</B>: {cell_entry.val_str}"
            full_cell.text += f"  <B>&sigma;</B>: {cell_entry.sig_str}<BR><BR>\n"
            full_cell.num_fails += cell_entry.num_bad
            if cell_entry.debug_group is not None:
                full_cell.debug_group = cell_entry.debug_group
            full_cell.link = cell_entry.link
        row_cells.append(full_cell)

    return row_cells


def make_num_inputs_cell(row, metric_defs, bands):
    """Format the number of inputs cell

    Parameters
    ----------
    row : `astropy.table.row.Row`
        A row of the table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    bands : `list`
        A list of the bands the metrics are in

    Returns
    -------
    full_cell : `cell_contents`
        A string of the formatted cell contents
    """

    row_str = ""
    full_cell = cell_contents()
    for band in ["u", "g", "r", "i", "z", "y"]:
        if band in bands:
            val_col_name = "coaddInputCount_" + band + "_inputCount_median"
            sig_col_name = "coaddInputCount_" + band + "_inputCount_sigmaMad"

            cell_entry = make_table_value(row, metric_defs, val_col_name, sig_col_name)
            full_cell.text += f"<B>{band}</B>: {cell_entry.val_str} <B>&sigma;</B> "
            full_cell.text += cell_entry.sig_str + "<BR>\n"
            if cell_entry.debug_group is not None:
                full_cell.debug_group = cell_entry.debug_group

    return full_cell


def make_photom_cols(row, metric_defs, bands, cols):
    """Make photometry column cell contents

    Parameters
    ----------
    row : `astropy.table.row.Row`
        Table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    bands : `list`
        A list of the bands the metrics are in
    cols : `list`
        A list of the columns to format

    Returns
    -------
    row_cells : `list` of `cell_contents`
        A list of the cells for the photometry columns
    """
    row_cells = []
    for col in cols:
        full_cell = cell_contents()
        for band in ["u", "g", "r", "i", "z", "y"]:
            if band in bands:
                for part in ["psf_cModel_diff"]:
                    val_col_name = col + "_" + band + "_" + part + "_median"
                    sig_col_name = col + "_" + band + "_" + part + "_sigmaMad"
                    cell_entry = make_table_value(
                        row, metric_defs, val_col_name, sig_col_name
                    )

                    full_cell.text += f"<B>{band}</B>: {cell_entry.val_str}  "
                    full_cell.text += f"<B>&sigma;</B>: {cell_entry.sig_str}<BR>\n"
                    full_cell.num_fails += cell_entry.num_bad
                    full_cell.debug_group = cell_entry.debug_group
                    full_cell.link = cell_entry.link
        row_cells.append(full_cell)

    return row_cells


def make_sky_cols(row, metric_defs, bands, cols):
    """Make sky column cell content

    Parameters
    ----------
    row : `astropy.table.row.Row`
        A row from the table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    bands : `list`
        A list of the bands the metrics are in
    cols : `list`
        A list of the columns to format

    Returns
    -------
    row_cells : `tuple` of `str`
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
                    cell_entry = make_table_value(
                        row, metric_defs, val_col_name, sig_col_name
                    )
                    full_cell.text += f"<B>{band}</B>: {cell_entry.val_str} "
                    full_cell.text += f"<B>&sigma;</B>: {cell_entry.sig_str}<BR>\n"
                    full_cell.num_fails += cell_entry.num_bad
                    if full_cell.debug_group is not None:
                        full_cell.debug_group = cell_entry.debug_group
            row_cells.append(full_cell)

    return row_cells


def make_footprint_cols(row, metric_defs, cols, prefix):
    """Make sky column cell content

    Parameters
    ----------
    row : `astropy.table.Table`
        A row from the table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    cols : `list`
        A list of the columns to format
    prefix : `string`
        The prefix at the start of the column name

    Returns
    -------
    row_cells : list of `cell_contents`
    """
    row_cells = []
    full_cell = cell_contents()
    for col in cols:
        val_col_name = prefix + "_" + col + "_footprint_count"
        cell_entry = make_table_value(row, metric_defs, val_col_name, None)
        full_cell.text += f"<B>{col}</B>: {cell_entry.val_str} "
        full_cell.text += "<BR>"
        full_cell.num_fails += cell_entry.num_bad
        if full_cell.debug_group is not None:
            full_cell.debug_group = cell_entry.debug_group

    return full_cell


def make_source_cols(row, metric_defs, cols, prefix):
    """Make sky column cell content

    Parameters
    ----------
    row : `astropy.table.Table`
        A row from the table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    cols : `list`
        A list of the columns to format

    Returns
    -------
    row_cells : list of `cell_contents`
    """
    row_cells = []
    full_cell = cell_contents()
    for col in cols:
        val_col_name = prefix + "_" + col + "_source_count"
        if col == "":
            val_col_name = prefix + "_source_count"
            col = "sources"
        cell_entry = make_table_value(row, metric_defs, val_col_name, None)
        full_cell.text += f"<B>{col}</B>: {cell_entry.val_str}<BR>"
        full_cell.num_fails += cell_entry.num_bad
        if full_cell.debug_group is not None:
            full_cell.debug_group = cell_entry.debug_group

    return full_cell


def make_mask_cols(row, metric_defs, cols, prefix):
    """Make sky column cell content

    Parameters
    ----------
    row : `astropy.table.Table`
        A row from the table of metrics
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    cols : `list`
        A list of the columns to format
    prefix : `string`
        The prefix that goes at the start of the colunm name

    Returns
    -------
    row_cells : list of `cell_contents`
    """
    row_cells = []
    full_cell = cell_contents()
    for col in cols:
        val_col_name = prefix + "_" + col + "_mask_fraction"
        cell_entry = make_table_value(row, metric_defs, val_col_name, None)
        full_cell.text += f"<B>{col}</B>: {cell_entry.val_str}<BR>"
        full_cell.num_fails += cell_entry.num_bad
        if full_cell.debug_group is not None:
            full_cell.debug_group = cell_entry.debug_group

    return full_cell


def worst(t, metric_list, id_col):
    """Select the worst rows in a table for the 
    given metrics.

    Parameters
    ----------
    t : `astropy.table.Table`
        The table to choose the rows from
    metric_list : `list`
        The list of metrics to judge from
    id_col : `string`
        The name of the datatype id column
        e.g. tract or visit number

    Returns
    -------
    worst : `list`
        A list of tuples containing the metric name,
        a string of the metric value and the tract/visit number
        for the value
    bad_table : `astropy.table.Table`
        The shortened table corresponding to the
        bad rows from the original
    """

    worst = []
    bad_ids = []
    for metric in metric_list:
        med = np.nanmedian(t[metric])
        dist_med = np.fabs(med - t[metric])
        bad_id = np.nanargmax(dist_med)
        bad_ids.append(bad_id)
        worst.append((metric, f"{t[metric][bad_id]:.3g}", t[id_col][bad_id]))

    bad_table = t[bad_ids]

    return worst, bad_table


def make_stellar_ast_self_rep_cols(row, metric_defs, bands, cols):
    """Make stellar ast repeatability column cell contents

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
    sasr_cells : `list`
        A list of `cell_contents` that contains the
        information for the given columns.
    """
    sasr_cells = []
    prefix = "stellarAstrometricSelfRepeatability"
    for col in cols:
        full_cell = cell_contents()
        debug_group_all = None
        full_cell.text += f"<B>{col}</B><BR>"
        for band in ["u", "g", "r", "i", "z", "y"]:
            full_cell.text += f"<B>{band}</B>: "
            if band in bands:
                for coord in ["RA", "Dec"]:
                    val_col_name = prefix + coord + "_" + band + "_" + col + "_" + coord
                    cell_entry = make_table_value(
                        row, metric_defs, val_col_name, None
                    )
                    full_cell.num_fails += cell_entry.num_bad
                    full_cell.text += f"<B>{coord}:</B>{cell_entry.val_str} "
                    if cell_entry.debug_group is not None:
                        full_cell.debug_group = cell_entry.debug_group
                    full_cell.link = cell_entry.link
            full_cell.text += "<BR>"
        sasr_cells.append(full_cell)
    return sasr_cells


def make_var1_band_var2_cols(row, metric_defs, bands, cols):
    """Make stellar ast repeatability column cell contents

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
    cells : `list`
        A list of `cell_contents` that contains the
        information for the given columns.
    """
    cells = []
    for (var1, var2) in cols:
        full_cell = cell_contents()
        debug_group_all = None
        for band in ["u", "g", "r", "i", "z", "y"]:
            full_cell.text += f"<B>{band}</B>: "
            if band in bands:
                val_col_name = var1 + "_" + band + "_" + var2
                cell_entry = make_table_value(row, metric_defs, val_col_name, None)
                full_cell.num_fails += cell_entry.num_bad
                full_cell.text += f"</B>{cell_entry.val_str} "
                if cell_entry.debug_group is not None:
                    full_cell.debug_group = cell_entry.debug_group
                full_cell.link = cell_entry.link
            full_cell.text += "<BR>"
        cells.append(full_cell)
    return cells




def make_table_cells(t, col_dict, bands, metric_defs, prefix):
    """
    Make the cells for the HTML tables

    Parameters
    ----------
    t : `astropy.table.Table`
        The table to make the table from
    col_dict : `dict`
        A dict of the columns
    bands : `list`
        A list of the bands
    metric_defs : `dict`
        A dictionary of metrics and their thresholds
    prefix : `string`
        The prefix that goes at the start of the colunm name

    Returns
    -------
    content_dict : `dict`
        A dict of table rows keyed by the id column
    """
    content_dict = {}
    for n, id_val in enumerate(t[col_dict["id_col"]]):
        row_list = []

        row_list.append(make_id_val_cell(id_val))
        for col in col_dict["table_cols"]:

            if col == "failed metrics":
                continue
            elif col == "nPatches":
                row_list.append(make_patch_num_cell(t[n], bands))
            elif col == "nInputs":
                row_list.append(make_num_inputs_cell(t[n], metric_defs, bands))
            else:
                row_list.append(make_general_cell(t[n], col))

        num_bad = 0
        cell_vals = []
        # Get the number of failed values and prep cell contents
        if "footprint_cols" in col_dict.keys():
            footprint_cell = make_footprint_cols(t[n], metric_defs, col_dict["footprint_cols"], prefix)
            cell_vals.append(footprint_cell)
            if footprint_cell.num_fails is not None:
                num_bad += footprint_cell.num_fails

        if "source_cols" in col_dict.keys():
            source_cell = make_source_cols(t[n], metric_defs, col_dict["source_cols"], prefix)
            cell_vals.append(source_cell)
            if source_cell.num_fails is not None:
                num_bad += source_cell.num_fails

        if "mask_cols" in col_dict.keys():
            mask_cell = make_mask_cols(t[n], metric_defs, col_dict["mask_cols"], prefix)
            cell_vals.append(mask_cell)
            if mask_cell.num_fails is not None:
                num_bad += mask_cell.num_fails

        if "shape_cols" in col_dict.keys():
            for shape_cell in make_shape_cols(
                t[n], metric_defs, bands, col_dict["shape_cols"]):
                cell_vals.append(shape_cell)
                if shape_cell.num_fails is not None:
                    num_bad += shape_cell.num_fails

        if "stellar_locus_cols" in col_dict.keys():
            # Make the cell details for the stellar locus columns
            for sl_cell in make_stellar_locus_cols(
                t[n], metric_defs, col_dict["stellar_locus_cols"]):
                cell_vals.append(sl_cell)
                if sl_cell.num_fails is not None:
                    num_bad += sl_cell.num_fails

        if "photom_cols" in col_dict.keys():
            # Make the cell contents for the photometry columns
            for photom_cell in make_photom_cols(
                t[n], metric_defs, bands, col_dict["photom_cols"]):
                cell_vals.append(photom_cell)
                if photom_cell.num_fails is not None:
                    num_bad += photom_cell.num_fails

        if "sky_cols" in col_dict.keys():
            # Make the cell contents for the sky columns
            for sky_cell in make_sky_cols(t[n], metric_defs, bands, col_dict["sky_cols"]):
                cell_vals.append(sky_cell)
                if sky_cell.num_fails is not None:
                    num_bad += sky_cell.num_fails

        if "sasr_cols" in col_dict.keys():
            # Make the cell contents for the sky columns
            for sasr_cell in make_stellar_ast_self_rep_cols(t[n], metric_defs, bands, col_dict["sasr_cols"]):
                cell_vals.append(sasr_cell)
                if sasr_cell.num_fails is not None:
                    num_bad += sasr_cell.num_fails

        if "var1_band_var2" in col_dict.keys():
            for cell in make_var1_band_var2_cols(t[n], metric_defs, bands, col_dict["var1_band_var2"]):
                cell_vals.append(cell)
                if cell.num_fails is not None:
                    num_bad += cell.num_fails

        # Add a nan/bad summary cell next but need to calculate these numbers first
        bad_cell = cell_contents()
        bad_cell.text = str(num_bad)
        row_list.append(bad_cell)
        for val in cell_vals:
            row_list.append(val)

        content_dict[str(id_val)] = row_list

    return content_dict
