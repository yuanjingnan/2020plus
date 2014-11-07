import numpy as np
import pandas as pd
import pandas.io.sql as psql
import src.data_analysis.python.feature_matrix as fmat
import src.data_analysis.python.position_entropy as pentropy
import src.features.python.features as feat
import logging

logger = logging.getLogger(__name__)

class RandomSplit(object):

    def __init__(self, sub_sample,
                 num_iter,
                 db_conn,
                 table_name='mutation',
                 col_name='Tumor_Sample',
                 with_replacement=False):
        self.db_conn = db_conn
        self.set_sub_sample(sub_sample)
        self.set_num_iter(num_iter)
        self.with_replacement = with_replacement
        self.TABLE_NAME = table_name
        self.COLUMN_NAME = col_name
        self.set_df(None)

    def dataframe_generator(self):
        """Generate subsampled data frames according to the sub_sample
        and num_iter arguments. The tumor type composition is respect, i.e.
        the relative amount of each tumor type for a specific sample will
        always reflect the relative amount in aggregate.
        """
        #n = int(self.sub_sample * self.total_count)  # number of counts to sample

        for i in range(self.num_iter):
            logger.info('Feature generation: Sub-sample rate={0}, Iteration={1} . . .'.format(self.sub_sample, i))
            left_samples = []
            right_samples = []

            # randomly split sample names while respecting tumor type
            # composition
            prng = np.random.RandomState()
            for tmp_ttype, tmp_samples in self.sample_names.iteritems():
                tmp_num_samps = len(tmp_samples)
                if not self.with_replacement:
                    # sample without replacement
                    prng.shuffle(tmp_samples)  # shuffle order of samples
                    split_pos = int(tmp_num_samps*self.sub_sample)
                    tmp_left = tmp_samples[:split_pos]
                    tmp_right = tmp_samples[split_pos:]
                else:
                    # sample with replacement
                    tmp_num_samps = int(tmp_num_samps*self.sub_sample)
                    tmp_left = prng.choice(tmp_samples, tmp_num_samps, replace=True)
                    tmp_right = prng.choice(tmp_samples, tmp_num_samps, replace=True)
                left_samples += tmp_left
                right_samples += tmp_right

            # process features with newly defined tumor samples to use
            left_feat_df = self._process_features(left_samples)
            right_feat_df = self._process_features(right_samples)

            logger.info('Finished feature generation: Sub-sample rate={0}, Iteration={1}'.format(self.sub_sample, i))
            yield left_feat_df, right_feat_df

    def _process_features(self, samps_of_interest):
        """Processes features from only the specified tumor samples of interest.

        Parameters
        ----------
        samps_of_interest: list/set
            list/set of tumor sample id's to use for generating features

        Returns
        -------
        proc_feat_df: pd.DataFrame
            dataframe consisting of features for classification
        """
        # make sure samples are a set object to speed up computation
        samps_of_interest = set(samps_of_interest)

        # get data from those sample names
        samp_flag = self.df[self.COLUMN_NAME].apply(lambda x: x in samps_of_interest)
        ixs = samp_flag[samp_flag==True].index
        tmp_df = self.df.ix[ixs].copy()

        # process features
        feat_list = fmat.generate_feature_matrix(tmp_df, 2)
        headers = feat_list.pop(0)  # remove header row
        feat_df = pd.DataFrame(feat_list, columns=headers)  # convert to data frame
        proc_feat_df = feat.process_features(feat_df, 0)
        miss_ent_df = pentropy.missense_position_entropy(tmp_df[['Gene', 'AminoAcid']])
        mut_ent_df = pentropy.mutation_position_entropy(tmp_df[['Gene', 'AminoAcid']])

        # encorporate entropy features
        proc_feat_df['mutation position entropy'] = mut_ent_df['mutation position entropy']
        proc_feat_df['pct of uniform mutation entropy'] = mut_ent_df['pct of uniform mutation entropy']
        proc_feat_df['missense position entropy'] = miss_ent_df['missense position entropy']
        proc_feat_df['pct of uniform missense entropy'] = miss_ent_df['pct of uniform missense entropy']
        return proc_feat_df

    def set_sub_sample(self, sub_sample):
        """Set the fraction of the original total mutations to actually sample.

        Sampling is done without replacement.

        **Parameters**

        sub_sample : float
            0 < sub_sample <= 1.0
        """
        if 0 <= sub_sample <= 1:
            self.sub_sample = sub_sample
        else:
            raise ValueError('Subsample should be between zero and one.')

    def set_num_iter(self, num_iter):
        """Set number of times to sample w/o replacement.

        **Parameters**

        num_iter : int
            do sample w/o replacement, num_iter number of times
        """
        if iter > 0:
            self.num_iter = num_iter
        else:
            raise ValueError('Number of iterations should be positive.')

    def set_df(self, df):
        if df:
            self.df = df
        else:
            sql = ("SELECT Gene, Protein_Change as AminoAcid, "
                   "       DNA_Change as Nucleotide, "
                   "       Variant_Classification, "
                   "       Tumor_Sample, Tumor_Type "
                   "FROM {0}".format(self.TABLE_NAME))
            self.df = psql.frame_query(sql, con=self.db_conn)
        drop_dups = self.df[['Tumor_Sample', 'Tumor_Type']].drop_duplicates()
        self.sample_names = drop_dups.set_index('Tumor_Sample').groupby('Tumor_Type').groups
        # self.sample_names = self.df[self.COLUMN_NAME].unique()

        # check validaty of data
        if not np.max(drop_dups['Tumor_Sample'].value_counts()) > 1:
            # each tumor sample has only one associated tumor type
            self.num_sample_names = len(self.sample_names)
        else:
            # yikes there are more than one tumor type associated with this sample
            # raise ValueError('A tumor sample has more than one tumor type!')
            pass

        self.total_count = len(self.df)
