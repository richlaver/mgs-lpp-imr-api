# Function for handling portable document formats
# ===============================================
from PyPDF2 import PdfFileMerger
from numpy import unique
from pathlib import Path
from operator import itemgetter
from re import compile, match, IGNORECASE
from os.path import exists
from src.output.template import outputFilepath
# Conversion of the MSWord document to PDF is currently frustrated by an unresolvable error.
from docx2pdf import convert


def collatePdf(appendixtitlesheets_path: Path, images_path: Path, plots_data: dict, gui_data: dict) -> None:
    """
    **collatePdf** Collate the appendices with plots into a portable document format (PDF) document.

    :param appendixtitlesheets_path: Path to the directory containing the appendix title sheets in PDF.
    :param appendixtitlesheets_path: Path
    :param images_path: Path to the directory containing the images to include in the appendices. The names of the images must correspond to the figure names.
    :param images_path: Path
    :param plots_data: Dictionary containing data on each plot. The dictionary must contain the keys 'appendix_figure' and 'appendix_insertion' for each element of plot data within of the list in the field 'plots'.
    :param plots_data: dict
    :param gui_data: Dictionary containing data from the graphical user interface.
    :param gui_data: dict
    """
    # Generate regular expression to identify whether the value of the 'appendix_insertion' field correctly refers to an
    # appendix letter.
    yield 'Collating PDF...', 0, 1, 0
    appendix_pattern = compile('appendix', IGNORECASE)
    # Generate collated appendices in the same directory as the appendix title sheets, with the filename comprising the
    # name of the generated MSWord document appended by ' appendices'.
    output_filepath = outputFilepath(gui_data=gui_data)
    appendix_path = str(output_filepath.with_name(output_filepath.stem + ' appendices.pdf'))
    merger = PdfFileMerger()
    merger.addMetadata(infos={
        'Author': 'Rich Laver',
        'Title': 'I&M Weekly Monitoring Report 16HK12026 - '
                 + gui_data['reportprefix']
                 + '{:0>3d}'.format(gui_data['reportnumber'])
                 + ' Rev' + '{:1d}'.format(gui_data['reportrevision']),
        'Company': 'WSP',
        'Hope': 'Jesus',
        'Words': 'I came that they may have life and have it abundantly./n John 10:10'
    })
    # Generate a list of tuples for each plot with the first element as the field 'appendix_insertion' and the second
    # element as the field 'appendix_figure'. Only plots with valid appendix references are included.
    plot_insertions = [(insertion, plot_data['appendix_figure']) for plot_data in plots_data['plots'] for insertion in plot_data['appendix_insertion'] if match(appendix_pattern, insertion)]
    plot_insertions = [(plot_data['appendix_insertion'][-1], plot_data['appendix_figure']) for plot_data in plots_data['plots'] if match(appendix_pattern, plot_data['appendix_insertion'] )]
    # The plots are sorted according to appendix entry: first by appendix letter, then by figure name.
    plot_insertions.sort(key=itemgetter(0, 1))
    # The number of plots is needed to define the maximum scale of the progress bar of the progress dialog.
    num_plots = len(plot_insertions)
    # Initialise a count of plots.
    plot_count = 0
    # Generate a unique list of appendix letters e.g. ['e', 'f', 'g' ,'h'].
    appendix_letters = unique([plot_insertion[0] for plot_insertion in plot_insertions])
    for appendix_letter in appendix_letters:
        appendixtitlesheet_path = str(appendixtitlesheets_path.joinpath('appendix_' + appendix_letter + '.pdf'))
        if not exists(appendixtitlesheet_path):
            continue
        # Queue an appendix title sheet for collation.
        merger.append(fileobj=appendixtitlesheet_path)
        # Identify figures in a particular appendix.
        for figure in [plot_insertion[1] for plot_insertion in plot_insertions if plot_insertion[0] == appendix_letter]:
            plot_count += 1
            yield 'Collating PDF...', 0, num_plots, plot_count
            appendixfigure_path = str(images_path.joinpath(figure + '.pdf'))
            if not exists(appendixfigure_path):
                continue
            # Queue an appendix figure for collation.
            merger.append(fileobj=appendixfigure_path)
    merger.write(fileobj=appendix_path)
    yield 'Collating PDF...', 0, 1, 1
    merger.close()