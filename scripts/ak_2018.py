from __future__ import division

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
'Gray-Jackson, Elvi':'Elvi Gray-Jackson',
'Myers, J. R.':'JR Myers',
'De La Fuente, Roque':'Roque De La Fuente',
'Kreiss-Tomkins, Jona':'Jona Kreiss-Tomkins',
'Begich/Call' : 'Mark Begich',
'Dunleavy/Meyer' : 'Mike Dunleavy',
'Walker/Mallott' : 'Bill Walker',
'Toien/Clift' : 'Billy Toien',
}

office_cleanup = {
    'GOVERNOR/LT. GOVERNOR':'Governor',
}


def parse_2018():
    '''Parse the AK 2016 General Election results into the OpenElections
    format.
    '''

    df = pd.read_csv('../2018/20181106__ak__general__precinct.csv')

    #clean up office names
    df = df.replace({"office": office_cleanup})

    # clean up the overseas ballots to be in House District 99
    df['precinct'] = df['precinct'].str.strip()
    df['district'] = np.where(
        df.precinct == 'HD99 Fed Overseas Absentee',
        99, df['district'])

    # remove the non-vote data
    # df = df[pd.notnull(df['district'])]
    df = df[df['candidate'] != 'Registered Voters']
    df = df[df['candidate'] != 'Times Counted']

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
    # clean up the whitespace
    df.precinct = df.precinct.str.strip()
    df.party = df.party.str.strip()

    # get the actual district
    df['district'] = df['precinct'].str.extract(r'(\d+)', expand=False)
    df['district'] = df['district'].str.lstrip("0")

    # remove intermediate values
    df = df.drop(['precinct',  'precinct_3'], axis=1)

    # constent column labels
    df.columns = ['county',  'office', 'district',  'candidate', 'party',
                  'votes', 'precinct']

    # check totals against reported results
    # http://www.elections.alaska.gov/results/18GENR/data/results18.pdf
    dft = df.groupby(['office', 'candidate']).agg({'votes': 'sum'})
    assert dft.loc['U.S. House'].votes.sum() == 282166
    assert dft.loc['Governor'].votes.sum() == 283134

    # export to CSV
    # create files for each district
    dfg = df.groupby(['district'])
    for name, group in dfg:
        group.to_csv('../2018/20181106__ak__general__'+str(name)+'__precinct.csv', index=False)

    return    

if __name__ == '__main__':
    parse_2018()
