from __future__ import print_function, division

import os
import pandas as pd
import numpy as np

positions = ['President', 'U.S. Senate', 'U.S. House',
            'State Senate','State House', 'Governor']

one_off_names = {
'Holdaway, Truno N. L':'Truno Holdaway',
'Faye-Brazel, Patrici':'Patrici Faye-Brazel',
'Sullivan-Leonard, Co':'Co Sullivan-Leonard',
'Von Imhof, Natasha A':'Natasha Von Imhof',
'Crawford, Harry T. J':'Harry Crawford',
'Myers, J. R.':'JR Myers',
'De La Fuente, Roque':'Roque De La Fuente',
'Kreiss-Tomkins, Jona':'Jona Kreiss-Tomkins'
}


def parse_2016():
    '''Parse the AK 2016 General Election results into the OpenElections
    format.
    '''

    df = pd.read_csv('./2016/20161108__ak__general__precinct.csv', encoding='cp1252')

    # clean up the overseas ballots to be in House District 99
    df['precinct'] = df['precinct'].str.strip()
    df['state_legislative_district'] = np.where(
        df.precinct == 'HD99 Fed Overseas Absentee',
        99, df.state_legislative_district)
    df['state_legislative_district'] = df[
        'state_legislative_district'].astype('int')

    # clean up the office listings, remove unnecessary local races
    df['office'] = df['office'].str.strip()
    df = df[df['office'].isin(positions)].copy()

    # clean up the candidate names
    # swap order from last, first to first last
    df['candidate'] = df['candidate'].str.strip()
    df = df.replace({"candidate": one_off_names})

    df['candidate'] = df['candidate'].str.replace('.', "").astype('str')
    df.candidate = df.candidate.str.replace(
        r'([A-Za-z]+),\s+([A-Za-z]+)\s+([A-Za-z]+)', "\\2 \\1").astype('str')
    df['candidate'] = df['candidate'].str.replace(
        r'(\w+),\s(\w+)', "\\2 \\1").astype('str')
    # assert len(df.candidate.unique()) == 116

    # remove trailing integers from write-ins, which appear
    # to have no informational puprose
    df['candidate'] = df['candidate'].str.replace(" \d+", "").astype('str')
    df['candidate'] = np.where(
        df.candidate == 'Write-in', 'Write-ins', df.candidate)
    df['party'] = np.where(df.candidate == 'Write-ins', np.nan, df.party)

    # split up the precincts
    df['precinct_2'], _ = df['precinct'].str.split(' ', 1).str
    _, df['precinct_3'] = df['precinct'].str.split('-', 1).str
    # set the pseudo-precincts for absentee, etc
    df.precinct_2 = np.where(df.precinct_2 == 'District',
                             df.precinct_3, df.precinct_2)
    # remove intermediate values
    df = df.drop(['precinct', 'district', 'precinct_3'], axis=1)

    # constent column labels
    df.columns = ['district', 'office', 'party',
                  'candidate', 'votes', 'precinct']

    # clean up the precinct whitespace
    df.precinct = df.precinct.str.strip()

    # check totals against reported results
    # http://elections.alaska.gov/results/16GENR/data/results.pdf
    dft = df.groupby(['office', 'candidate']).agg({'votes': 'sum'})
    assert dft.loc['President'].votes.sum() == 318608
    assert dft.loc['U.S. Senate'].votes.sum() == 311441
    assert dft.loc['U.S. House'].votes.sum() == 308198

    # export to CSV
    df.to_csv('./2016/20161108__ak__general.csv', index=False)
    # create files for each district
    # dfg = df.groupby(['district'])
    # for name, group in dfg:
    #     group.to_csv('./2016/20161108_ak_general_'+str(name)+'.csv')

if __name__ == '__main__':
    parse_2016()
