import argparse
from typing import Tuple

import pandas as pd

def parse_args() -> Tuple[str, str, str]:
    parser = argparse.ArgumentParser(description="The program calculates the time difference between two events")
    parser.add_argument('fname1', type=str, help='blkparse output file1 (first event)')
    parser.add_argument('fname2', type=str, help='blkparse output file2 (later event)')
    parser.add_argument('-o', '--output', type=str, default='output.csv', help='output file name')

    args = parser.parse_args()

    return args.fname1, args.fname2, args.output

def diff_events(event_data1: pd.DataFrame, event_data2: pd.DataFrame) -> Tuple[bool, pd.DataFrame]:
    i = 0
    j = 0
    found_event_data1 = pd.DataFrame()
    result_data = pd.DataFrame()
    while i < event_data1.shape[0] and j < event_data2.shape[0]:
        curr_event_data1 = event_data1.iloc[i]
        curr_event_data2 = event_data2.iloc[j]

        if curr_event_data1[0] < curr_event_data2[0]:
            found_event_data1 = pd.concat([found_event_data1, pd.DataFrame(curr_event_data1).T], ignore_index=True)
            i += 1
        else:
            for _, rows in found_event_data1[::-1].iterrows():
                if rows[1] == curr_event_data2[1] and rows[2] == curr_event_data2[2]:
                    merge_data = pd.merge(pd.DataFrame(rows).T, pd.DataFrame(curr_event_data2).T, left_on=[1,2], right_on=[1,2], how='inner')

                    result_data = pd.concat([result_data, merge_data], ignore_index = True)
                    break
            j += 1

    if result_data.shape[0] > 0:
        new_columns = ['event1_time', 'event1_sector', 'event1_byte', 'event1_command', 'event2_time', 'event2_command']
        result_data.columns = new_columns
        result_data['diff'] = result_data['event2_time'] - result_data['event1_time']
        return True, result_data
    else:
        return False, pd.DataFrame()

if __name__ == "__main__":
    fname1, fname2, out_fname = parse_args()

    data1 = pd.read_csv(fname1, header=None)
    data2 = pd.read_csv(fname2, header=None)

    rv, result = diff_events(data1, data2)
    if not rv:
        print('There was no data.')
    else:
        result.to_csv(out_fname, index=False)

