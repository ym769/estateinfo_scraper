
#!/usr/bin/env python
# coding: utf-8

from requests_html import HTMLSession
import pandas as pd
import json
import time
import warnings
import os

warnings.simplefilter('ignore')

area1 = input(" Prefecture (tokyo, saitama..., or None) = ")
max_ = 100

if area1 == "None" :
#    page_number = input(" Page number = ")
    file_name = input(" File name (exclude .json) = ")
    base_url = 'https://chintai.infonista.jp/area/:limit,50:page,'
else:
    area2 = input(" Region (chiyodaku, hachiojishi... or None) = ")
    if area2 == "None":
#        page_number = input(" Page number = ")
        file_name = input(" File name (exclude .json) = ")
        base_url = 'https://chintai.infonista.jp/area/'+area1+'/:limit,50:page,'
    else:
#        page_number = input(" Page number = ")
        file_name = input(" File name (exclude .json) = ")
        base_url = 'https://chintai.infonista.jp/area/'+area1+'/'+area2+'/:limit,50:page,'

# directryを作成
new_dir_path = file_name
os.mkdir(new_dir_path)
os.mkdir(new_dir_path+"/archive")

try:
    args = dict(prefecture = area1, region =area2, file_name =file_name)
except:
    area2 = "None"
    args = dict(prefecture = area1, region =area2, file_name =file_name)

with open(file_name+'/'+file_name+'_keys.json', 'w') as f:
    json.dump(args, f)

resps = []

for variable in range(max_):
    print("-- crawling page #"+str(variable+1)+" --")
    variable += 1
    session = HTMLSession()
    resp = session.get(f'{base_url}{variable}',verify=False)
    resps.append(resp)
    full_l = [i.text for i in resp.html.find(".office-floor p")]
    if '現在、この不動産物件で募集している空室はありません。' in full_l:
        break
    time.sleep(3)

keyss = ["Building_ID","prefecture","region","name","adress","最寄り駅","PR","築X年","規模","フロア","坪数（坪）","賃料総額・共益費込み（万円）","坪単価","敷金/保証金","入居可能日","entry#"]

Result_ = pd.DataFrame(columns = keyss)

for resp in resps:
    ################# まずIDを取得

    # office_id
    sel = ".office-code" #物件のID
    elems = resp.html.find(sel)
    ids = [i.text for i in elems]

    ################# IDから物件ごとのDetail（各部屋の詳細）を取得

    Detail = []
    entry_num = []
    for i in range(len(ids)):
        sections = []
        entry_num_small = []
        for num in range(100): # 十分に大きい任意の数字
            try:
                num += 1
                if num<10:
                    resp2 = resp.html.find('#'+ids[i]+' .floor-0'+str(num), first=True)
                    resptext = resp2.text
                    sections.append(resptext)
                    entry_num_small.append("floor-0"+str(num))
                else:
                    resp2 = resp.html.find('#'+ids[i]+' .floor-'+str(num), first=True)
                    resptext = resp2.text
                    sections.append(resptext)
                    entry_num_small.append("floor-"+str(num))
            except:
                break
        details = []
        for i in sections:
            s = i.split("\n")

            # 敷地面積の情報（坪）を成型
            tsubo = s[1].split(" ")
            s[1] = tsubo[0].replace('坪','')
            s[1] = s[1].replace(',','')

            details.append(s)
        Detail.append(details)
        entry_num.append(entry_num_small)

    # 物件価格情報（万円）を成型
    for j in range(len(Detail)):
        for k in range(len(Detail[j])):
            if "確認" in Detail[j][k][2]:
                Detail[j][k][2] = "NaN"
            else:
                Detail[j][k][2] = Detail[j][k][2].split(" ")[1].replace("万円","")

    # DetailにそれぞれIDを付与
    for i in range(len(Detail)):
        for j in Detail[i]:
            j.append(ids[i])

    ## PandasDataFrameにする
    Detail_bag = []
    for i in Detail:
        for j in i:
            Detail_bag.append(j)

    ## PandasDataFrameにする
    entry_num_bag = []
    for i in entry_num:
        for j in i:
            entry_num_bag.append(j)

    detail_keys = ["フロア","坪数（坪）","賃料総額・共益費込み（万円）","敷金/保証金","入居可能日","Building_ID"]
    Detail_pd = pd.DataFrame(Detail_bag, columns = detail_keys)
    Detail_pd["entry#"]=entry_num_bag

    # 坪単価付け足し
    unit = []
    for i in ids:
        sel = "#"+i+" .unit em"
        elems = resp.html.find(sel)
        for j in elems:
            if j.text=="ご相談":
                unit.append("NaN")
            else:
                unit.append(j.text)
    unit_pd = pd.Series(unit, name="坪単価")

    wa= pd.merge(Detail_pd, unit_pd, left_index=True, right_index=True)
    wo_=wa.ix[:,[0,1,2,7,3,4,5,6]] # カラム並び替え

    ################ Detailに対してその物件の大枠の情報を付与

    ids_pd = pd.Series(ids, name = "Building_ID")

    # office_name
    names = []
    for i in ids:
        sel = "#"+i+" .office-name"
        elems = resp.html.find(sel)
        for j in elems:
            names.append(j.text)
    name_pd = pd.Series(names, name = "name")

    # adress
    adress = []
    for i in ids:
        sel = "#"+i+" .office-address"
        elems = resp.html.find(sel)
        for j in elems:
            a = j.text
            b = a.strip("\xa0[ 地図 ]")
            c = b.strip("\xa0[ 地図 ]\xa0[ 周辺の駐車場")
            d = c.strip("住所：")
            adress.append(d)
    adress_pd = pd.Series(adress, name="adress")

    station = []
    for i in ids:
        sel = "#"+i+" .office-station"
        elems = resp.html.find(sel)
        for j in elems:
            a = j.text.split("（")
            b = a[0].replace("最寄駅：","")
            station.append(b)
    station_pd = pd.Series(station, name="最寄り駅")

    # description
    description = []
    for i in ids:
        sel = "#"+i+" .office-description dd"
        elems = resp.html.find(sel)
        for j in elems:
            if j.text == '':
                description.append("NaN")
            else:
                description.append(j.text)
    description_pd = pd.Series(description, name="PR")

    age = []
    for i in ids:
        sel = "#"+i+" .spec-age"
        elems = resp.html.find(sel)
        for j in elems:
            a = j.text.split("（")
            b = a[0].replace("築年数：","").replace("築","").replace("年","")
            age.append(b)
    age_pd = pd.Series(age, name="築X年")

    kibo = []
    for i in ids:
        sel = "#"+i+" .spec-height"
        elems = resp.html.find(sel)
        for j in elems:
            a = j.text.replace("規模：","")
            kibo.append(a)
    kibo_pd = pd.Series(kibo, name="規模")

    ## 都道府県
    prefecture = []
    for i in adress:
        if "東京都" in i:
            area = "東京都"
            prefecture.append(area)
        elif "神奈川県" in i:
            area = "神奈川県"
            prefecture.append(area)
        elif "埼玉県" in i:
            area = "埼玉県"
            prefecture.append(area)
        elif "千葉県" in i:
            area = "千葉県"
            prefecture.append(area)
        else:
            area = "Else"
            prefecture.append(area)
    prefecture_pd = pd.Series(prefecture, name="prefecture")

    ## 市区町村
    region_pre = [] # 下準備
    for i in adress:
        if "都" in i:
            a = i.split("都")
            region_pre.append(a[1])
        elif "県" in i:
            a = i.split("県")
            region_pre.append(a[1])
        else:
            region_pre.append("error")
    region = []
    for i in region_pre:
        if "市" in i:
            idx = i.index('市')
            a = i[:idx+1]
            region.append(a)
        elif "区" in i:
            idx = i.index('区')
            a = i[:idx+1]
            region.append(a)
        elif "村" in i:
            idx = i.index('村')
            a = i[:idx+1]
            region.append(a)
        elif "町" in i:
            idx = i.index('町')
            a = i[:idx+1]
            region.append(a)
        else:
            region.append("Else")
    region_pd = pd.Series(region, name="region")

    concat0 = pd.merge(ids_pd, prefecture_pd, left_index=True, right_index=True)
    concat1 = pd.merge(concat0, region_pd, left_index=True, right_index=True)
    concat2 = pd.merge(concat1, name_pd, left_index=True, right_index=True)
    concat3 = pd.merge(concat2, adress_pd, left_index=True, right_index=True)
    concat4 = pd.merge(concat3, station_pd, left_index=True, right_index=True)
    concat5 = pd.merge(concat4, description_pd, left_index=True, right_index=True)
    concat6 = pd.merge(concat5, age_pd, left_index=True, right_index=True)
    concat7 = pd.merge(concat6, kibo_pd, left_index=True, right_index=True)

    ################ Detailに対してその物件の大枠の情報を付与

    Result = pd.merge(concat7, wo_, on="Building_ID")

    Result_ = Result_.append(Result)

reset = Result_.reset_index()
reset = reset.drop("index",axis=1)
Result_dict = reset.to_dict()

from datetime import datetime
dt = datetime.now()
today = dt.strftime('%Y-%m-%d')

try:
    reset.to_csv(file_name+'/archive/'+file_name+today+'.csv',index=False,encoding="utf-8_sig")
except:
    pass

try:
    reset.to_csv(file_name+'/'+file_name+'.csv',index=False,encoding="utf-8_sig")
except:
    pass


print(file_name+".json and "+file_name+".csv have been seved on directory named "+file_name)
