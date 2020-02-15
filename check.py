#%%
import json

alpha = list('abcdefghijklmnopqrstuvwxyz')
alpha = [i+j for i in alpha for j in alpha]

with open('alpha.json', 'r') as w:
    with open('alpha_drugscom.json', 'r') as d:
        webmd = json.load(w)
        drugscom = json.load(d)
        for key in alpha:
            in_drugs = key in drugscom
            in_webmd = key in webmd
            if in_drugs and in_webmd:
                    for drug in [i[0] for i in webmd[key]]:
                        if drug in [i[0]for i in drugscom[key]]:
                            with open('similar.csv', 'a') as f:
                                f.write(drug + '\n')
                        else:
                            with open('only_in_webmd.csv', 'a') as f:
                                f.write(drug + '\n')
            if in_drugs and not in_webmd:
                for drug in [i[0] for i in drugscom[key]]:
                    with open('only_in_drugsdotcom.csv', 'a') as f:
                        f.write(drug + '\n')
            if in_webmd and not in_drugs:
                for drug in [i[0] for i in webmd[key]]:
                    with open('only_in_webmd.csv', 'a') as f:
                        f.write(drug + '\n')






# %%
