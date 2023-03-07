import pandas as pd
import numpy as np
import openmatrix as omx
import os

timeperiods = ['AM', 'LT', 'PM']

DSTM_dir = os.path.join('C:/Users/nick.fournier/Resource Systems Group, Inc',
                        'Model Development - Dubai RTA ABM Development Project',
                        'Task 3/Skims')

mwcog_skims = omx.open_file('processing_data/templates/skims.omx','r')
model_skims = {k: omx.open_file(os.path.join(DSTM_dir, 'DSTM_skims__%s.omx') % k,'r') for k in timeperiods}

# This checks the configs for skim tables and aggregates into a list of skims used
config_dir = 'C:\\gitclones\\dubai_activitysim\\configs'
csv_list = [os.path.join(config_dir, x) for x in os.listdir(config_dir) if '.csv' in x]


class Process

def check_csv(f):
    df = pd.read_csv(f)

    if 'Expression' in df.columns and df.Expression.str.contains('skim', na=False).any():
        #         print(csv_list.index(f), f, df.columns)

        df['config'] = os.path.basename(f)
        # Find all expression with 'skim'
        df = df[df.Expression.str.contains('skim', na=False)]

        # Find skim tables between square brackets
        df['skim'] = df.Expression.str.findall('\[+(.*?)\]')

        # Explode skims list into separate rows
        df = df.explode('skim')
        df.skim = df.skim.str.findall("'([^']*)'").str.join('__')

        # Drop columns and duplicate rows
        cols = ['config', 'asim variable', 'skim', 'Description', 'Expression']
        if 'Target' in df.columns:
            df.rename(columns={'Target': 'asim variable'}, inplace=True)
        elif 'Label' in df.columns:
            df.rename(columns={'Label': 'asim variable'}, inplace=True)
        else:
            df['asim variable'] = pd.Series(dtype='string')

        df = df[cols].drop_duplicates()

        return df


def create_skim_list():
    skim_list_df = pd.concat([check_csv(f) for f in csv_list], axis=0)

    # Drop duplicates, keep first instance
    skim_list_df = skim_list_df.drop_duplicates('skim').reset_index(drop=True)
    skim_list_df = skim_list_df[~skim_list_df.skim.isna()]
    skim_list_df.to_csv('exdata/skim_list.csv', index=False)


# %%
# Create an default matrix index label map to modify manually
def matrix_map(tod):
    mm = {k: model_skims[tod][k].attrs.CODE for k in model_skims[tod].list_matrices()}
    mm_df = pd.DataFrame.from_dict({'key': mm.keys(), 'name': mm.values()})
    return mm_df


matrix_map = {tod: matrix_map(tod) for tod in timeperiods}

# Check to make sure the matrix mapping is the same for all time periods before we use the same xwalk for all
if all([x.equals(matrix_map[timeperiods[0]]) for x in matrix_map.values()]):
    matrix_map = matrix_map[timeperiods[0]]

# Save matrix map as a template to create a xwalk config file
matrix_map.to_csv('exdata/matrix_map.csv', index=False)
# %%
# Rename skims and extract the ones we need
skim_rename = pd.read_excel('controls/skim_mapping.xlsx', sheet_name='2. model skims')
skim_rename = skim_rename[skim_rename.keep]
skim_rename = skim_rename.set_index('new_name')

# Raw skim extracted and renamed
if not os.path.isdir('processing_data/raw_skims'):
    os.mkdir('processing_data/raw_skims')


# Setup skim dict
def extract_raw_skims(tod):
    skim_path = 'processing_data/raw_skims/raw_skims__{}.omx'.format(tod)
    if os.path.isfile(skim_path):
        skims = omx.open_file(skim_path, 'a')  # use 'a' to append/edit an existing file
    else:
        skims = omx.open_file(skim_path, 'w')
    print('Assigning ' + tod + ' matrices to new skims output with updated names')

    existing = skims.list_matrices()
    for name, k in skim_rename.key.items():
        if name not in existing:
            skims[name] = np.array(model_skims[tod][str(k)])
    print('...done')
    skims.close()

    return skims


raw_skims = {tod: extract_raw_skims(tod) for tod in timeperiods}
# %%
# Now process the skims
skim_config = pd.read_excel('controls/skim_mapping.xlsx', sheet_name='3. asim skims')
skim_config = skim_config[~skim_config.expression.isna()]
skim_config = skim_config.set_index('asim skim')


# Create new skims from the config expressions
def create_skims(tod):
    skim_path = 'processing_data/processed/skims__{}.omx'.format(tod)
    # use 'a' to append/edit an existing file
    if os.path.isfile(skim_path):
        skims = omx.open_file(skim_path, 'a')
    else:
        skims = omx.open_file(skim_path, 'w')

    existing = skims.list_matrices()

    print('Evaluating {} expressions'.format(tod))

    for name, expression in skim_config.expression.items():
        skim_name = '__'.join([name, tod])
        if skim_name not in existing:
            #             print('Evaluating {} to {}'.format(expression, skim_name))
            skims[skim_name] = eval(expression)

    return skims


skims = {tod: create_skims(tod) for tod in timeperiods}
# %%
for tod in timeperiods:
    raw_skims[tod].close()
    skims[tod].close()




if __name__ == "__main__":
    pass