
import sys, argparse, re, unicodedata, numpy as np
import spacy
from sklearn.cluster import KMeans
nlp = spacy.load("en_core_web_md")

def activities_vec(activities):
    act_vec=[]
    for activity in activities:
        doc=nlp(activity)
        act_vec.append(np.ndarray(doc.vector))
    return act_vec

def activites_cluster(act_vec):
    Kmeans=KMeans(n_clusters = 5, random_state=42)
    return Kmeans.fit(act_vec)
