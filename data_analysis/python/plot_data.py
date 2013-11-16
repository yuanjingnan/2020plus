"""
Performs necessary tasks prior to plotting data via the
utils/python/plot.py module. In many cases the plot functions
read the data from file so that data observed in the results
directory is always consistent with the actual plots.
"""

from __future__ import division  # prevents integer division
import pandas as pd
import utils.python
import utils.python.plot as myplt
import utils.python.util as _utils
from matplotlib.mlab import PCA
import logging

logger = logging.getLogger(__name__)  # logger obj for this module

def aa_missense_heatmap(file_path, save_path):
    """Plot a heatmap for missense mutations.

    Rows are normalize in order to sum to 1. Each cell in the heatmap represents
    the mutation transition probability. The y-axis represents the initial amino
    acid and the x-axis represents the mutated amino acid.

    Args:
        file_path (str): file to data containing missense mutation counts
        save_path (str): file name of heatmap figure
    """
    logger.info('reading in %s ...' % file_path)
    df = pd.read_csv(file_path, sep='\t')  # read in data
    logger.info('finished reading.')

    # pivot data to create a mutation count matrix
    ptable = pd.pivot_table(df,
                            values='count',
                            rows='initial',
                            cols='mutated',
                            aggfunc=sum)

    # normalize rows to sum to 1 (transition prob. matrix)
    ptable_norm = (ptable.T / ptable.T.sum()).T
    ptable_norm.fillna(0)  # fill missing with 0 probability

    # reorder rows/columns to be in chemically meaningful order for AA
    order = ['A', 'C', 'G', 'I', 'L', 'M', 'F', 'P', 'W', 'V',  # nonpolar
             'N', 'Q', 'S', 'T', 'Y',  # neutral polar
             'R', 'H', 'K',  # basic polar
             'D', 'E']  # acidic polar
    ptable_norm = ptable_norm.ix[order]
    ptable_norm = ptable_norm[order]

    # plot and save heatmap figure
    logger.info('Plotting missense mutation heatmap (%s) ...' % save_path)
    myplt.heatmap(ptable_norm,
                  file_path=save_path,
                  xlabel='Mutated AA',
                  ylabel='Initial AA')
    logger.info('Finished plotting heatmap.')


def nuc_substitution_heatmap(file_path, save_path, title=''):
    """Plot a heatmap for DNA substiution mutations.

    Rows are normalize in order to sum to 1 (legal probability). Each cell in the
    heatmap represents the mutation transition probability. The y-axis represents the
    initial nucleotide and the x-axis represents the mutated nucleotide.

    Kwargs:
        file_path (str): file to data containing substiution mutation counts
        save_path (str): file name of heatmap figure
    """
    logger.info('reading in %s ...' % file_path)
    df = pd.read_csv(file_path, sep='\t')  # read in data
    logger.info('finished reading.')

    # pivot data to create a mutation count matrix
    ptable = pd.pivot_table(df,
                            values='count',
                            rows='initial',
                            cols='mutated',
                            aggfunc=sum)

    # normalize rows to sum to 1 (transition prob. matrix)
    ptable_norm = (ptable.T / ptable.T.sum()).T
    ptable_norm.fillna(0)  # fill missing with 0 probability

    # plot and save heatmap figure
    logger.info('Plotting substitution mutation heatmap (%s) ...' % save_path)
    myplt.heatmap(ptable_norm,
                  file_path=save_path,
                  title=title,
                  xlabel='Mutated Base',
                  ylabel='Initial Base')
    logger.info('Finished plotting heatmap.')


def aa_property_heatmap(file_path, save_path):
    """Plot a heatmap for mutation changes in chemical properties.

    """
    df = _utils.read_aa_properties(file_path)

    # normalize rows to sum to 1 (transition prob. matrix)
    df_norm = (df.T / df.T.sum()).T
    df_norm.fillna(0)  # fill missing with 0 probability

    # reorder rows/columns to go from non-polar to polar
    order = ['nonpolar', 'polar', 'basic polar', 'acidic polar']
    df_norm = df_norm.ix[order]
    df_norm = df_norm[order]

    # plot and save heatmap figure
    logger.info('Plotting change in chemical property heatmap (%s) ...' % save_path)
    myplt.heatmap(df_norm,
                  file_path=save_path,
                  xlabel='Mutated AA Properties',
                  ylabel='Initial AA Properties')
    logger.info('Finished plotting heatmap of AA chemical properties.')


def aa_property_barplot(file_path, save_path):
    df = _utils.read_aa_properties(file_path)
    logger.info('Plotting change in chemical property barplot (%s) ...' % save_path)
    myplt.barplot(df,
                  file_path=save_path,
                  title='Amino Acid Missense Mutations by Property',
                  ylabel='Counts')
    logger.info('Finished plotting heatmap of AA chemical barplot.')


def nuc_substitution_barplot(file_path, save_path,
                             title='DNA Substitution Mutations'):
    df = pd.read_csv(file_path, sep='\t')

    # pivot data to create a mutation count matrix
    ptable = pd.pivot_table(df,
                            values='count',
                            rows='initial',
                            cols='mutated',
                            aggfunc=sum)

    logger.info('Plotting substitution barplot (%s) ...' % save_path)
    myplt.barplot(ptable,
                  file_path=save_path,
                  title=title,
                  ylabel='Counts',
                  stacked=True)
    logger.info('Finished plotting bar plot.')


def mutation_types_barplot(mutation_cts,
                           save_path=_utils.plot_dir + 'aa_mut_types.barplot.png',
                           title='Mutations by Type'):
    """Create a barplot graphing counts of amino acid/DNA mutation types.

    Currently synonymous, missense, nonsense, frame shift, and indels
    are plotted for amino acids in the bar graph.

    Args:
        mutation_cts (pd.Series): unique counts for mutation types

    Kwargs:
        save_path (str): path to save barplot
        title (str): title for plot
    """
    logger.info('Plotting mutation type counts barplot (%s) . . .' % save_path)
    myplt.barplot(mutation_cts,
                  save_path,
                  title=title,
                  ylabel='Counts')
    logger.info('Finished plotting barplot of mutation types.')


def gene_mutation_histogram(gene_cts,
                            save_path,
                            title='Gene Mutation Histogram'):
    logger.info('Plotting gene mutation histogram (%s) . . .' % save_path)
    myplt.histogram(gene_cts,
                    save_path,
                    bins=range(0, 500, 10),  # not many genes >300
                    log=True,  # log scale y-axis
                    title=title,
                    ylabel='Counts (log)')
    logger.info('Finished plotting gene mutation histogram.')


def cumulative_gene_mutation(gene_cts,
                             save_path,
                             title='Cumulative Gene Mutations'):
    logger.info('Plotting cumulative gene mutations (%s) . . .' % save_path)
    df = pd.DataFrame(gene_cts)
    df['pseudo_count'] = 1  # each gene only counts once
    my_counts = df.groupby('count')['pseudo_count'].sum()  # numr of genes for each mutation count
    cumulative_cts = my_counts.cumsum()
    myplt.line(cumulative_cts,
               save_path,
               logx=True,
               title='Cumulative Gene Mutations',
               ylabel='Number of Genes',
               xlabel='Number of Gene Mutations (log)',
               vlines=[7, 18])  # vogelstein curates at between 7-18 counts
    logger.info('Finished plotting cumulative gene mutations.')


def pca_plot(file_path,
             save_path,
             title='Gene Mutation PCA'):
    logger.info('Plotting PCA of gene mutations (%s) . . .' % save_path)

    # normalize counts
    df = pd.read_csv(file_path,  # path
                     sep='\t',  # tab delim
                     index_col=0)  # index df by gene name

    # plot oncogenes and tumor suppressor genes as different colors
    oncogenes = set(_utils.read_oncogenes())  # get oncogenes
    tsgs = set(_utils.read_tsgs())  # get tumor suppressor genes
    colors = []
    for g in df.index.tolist():
        if g in oncogenes:
            colors.append('red')
        elif g in tsgs:
            colors.append('purple')
        else:
            colors.append('blue')

    # normalize data by row for PCA
    row_sums = df.sum(axis=1)
    df = df.div(row_sums.astype(float), axis=0)

    # old method for dividing by sum of row
    # tmp_total_cts = df.T.sum()
    # df = (df.T / tmp_total_cts).T

    # get marker size for scatter plot
    MAX_SIZE = 300  # some genes take up to much space
    scatter_size = [size if size < MAX_SIZE else MAX_SIZE for size in row_sums]

    # perform PCA
    results = PCA(df)
    first_eigen_value, second_eigen_value = results.fracs[:2]
    xy_data = [[item[0], item[1]] for item in results.Y]  # first two components
    x, y = zip(*xy_data)
    myplt.scatter(x, y,
                  save_path,
                  colors=colors,
                  size=scatter_size,
                  title='Mutation PCA',
                  xlabel='1st component (%f)' % first_eigen_value,
                  ylabel='2nd component (%f)' % second_eigen_value)
    logger.info('Finished PCA plot.')


def all_mut_type_barplot(df,
                         save_path,
                         title='Protein Mutation Types by Gene Label'):
    logger.info('Plotting protein mutation types by gene type (%s) . . .' % save_path)
    myplt.barplot(df,
                  save_path,
                  title='Protein Mutation Type by Gene Type',
                  ylabel='Counts',
                  stacked=True)
    logger.info('Finished plotting protein mutation types by gene type.')
