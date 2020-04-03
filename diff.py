import pandas as pd
import os

######### 差分の計算

file_name = input(" folder name: ")
Old_file_name = input(" Old_file name (.csvを除く) : ")
New_file_name = input(" New_file name (.csvを除く) : ")

Old_file = pd.read_csv(file_name+'/archive/'+Old_file_name+'.csv',encoding="utf-8_sig")
New_file = pd.read_csv(file_name+'/archive/'+New_file_name+'.csv',encoding="utf-8_sig")

Old_file["key"] = Old_file["Building_ID"]
New_file["key"] = New_file["Building_ID"]


Old_file_ = Old_file.drop("PR",axis=1) ## PRがよく悪さをするのでgroupbyする前に落としとく
Old_file_ = Old_file_.drop("Building_ID",axis=1)
Old_file_ = Old_file_.drop("築X年",axis=1)
Old_file_ = Old_file_.drop("坪単価",axis=1)
Old_file_ = Old_file_.drop("賃料総額・共益費込み（万円）",axis=1)
grouped_O = Old_file_.groupby('key').sum()
grouped_O_rename = grouped_O.rename(columns={'坪数（坪）': 'past_坪数（坪）'})


New_file_ = New_file.drop("PR",axis=1)
New_file_ = New_file_.drop("Building_ID",axis=1)
New_file_ = New_file_.drop("築X年",axis=1)
New_file_ = New_file_.drop("坪単価",axis=1)

New_file_ = New_file_.drop("賃料総額・共益費込み（万円）",axis=1)
grouped_N = New_file_.groupby('key').sum()
grouped_N_rename = grouped_N.rename(columns={'坪数（坪）': 'present_坪数（坪）'})

grouped_diff = pd.merge(grouped_O_rename,grouped_N_rename,on="key",how="outer").fillna(0)
grouped_diff["差分"] = grouped_diff['present_坪数（坪）']-grouped_diff['past_坪数（坪）']
grouped_diff_=grouped_diff.reset_index()

## grouped_diff_に対して情報を付けるためのDFを作成
whole_file = New_file.append(Old_file).drop_duplicates(["key"]).drop("PR",axis=1).drop("entry#",axis=1).drop("入居可能日",axis=1).drop("敷金/保証金",axis=1).drop("坪数（坪）",axis=1).drop("坪単価",axis=1).drop("賃料総額・共益費込み（万円）",axis=1)

sabun = pd.merge(grouped_diff_, whole_file, on="key")

from datetime import datetime
dt = datetime.now()
today = dt.strftime('%Y-%m-%d')

try:
    os.mkdir(file_name+"/sabun")
except:
    pass

try:
    sabun.to_csv(file_name+'/sabun/'+file_name+'_sabun'+today+'.csv',index=True,encoding="utf-8_sig")
except:
    pass

print(file_name+'_sabun'+today+'.csv have been seved on directory named '+file_name+"/sabun")
