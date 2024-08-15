import pandas as pd

issue_fname = "a"
comp_fname = "b"

out_fname = "c"

issue = pd.read_csv(issue_fname, header=None)
comp = pd.read_csv(comp_fname, header=None)

loop = comp.shape[0]

i = 0
j = 0
found_issues = pd.DataFrame()
result_df = pd.DataFrame()

while i < issue.shape[0] and j < comp.shape[0]:
    curr_issue = issue.iloc[i]
    curr_comp = comp.iloc[j]

    if curr_issue[0] < curr_comp[0]:
        found_issues = pd.concat([found_issues, pd.DataFrame(curr_issue).T],
                                 ignore_index=True)
        i += 1
    else:
        for _, rows in found_issues[::-1].iterrows():
            if rows[i] == curr_comp[1] and rows[2] == curr_comp[2]:
                merge_df = pd.merge(pd.DataFrame(rows).T,
                                    pd.DataFrame(curr_comp).T,
                                    left_on=[1, 2],
                                    right_on=[1, 2], how='inner')

                result_df = pd.concat([result_df, merge_df], ignore_index=True)
                break
            j += 1

result_df['diff'] = result_df['0_y'] - result_df['0_x']
result_df.to_csv(out_fname, index=False, header=False)
