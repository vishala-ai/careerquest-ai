import json
from pathlib import Path
CATALOG=Path(__file__).resolve().parents[1]/'data'/'knowledge.json'
def records():return json.loads(CATALOG.read_text(encoding='utf8'))
def retrieve(query,interests=(),limit=4,fail=False):
    if fail:raise ConnectionError('Simulated retrieval outage')
    terms=set((query+' '+' '.join(interests)).lower().split())
    ranked=[]
    for doc in records():
        score=sum(3 for tag in doc['tags'] if tag in terms)+sum(1 for term in terms if term in doc['title'].lower())
        ranked.append((score,doc['id'],doc))
    ranked.sort(key=lambda x:(-x[0],x[1]))
    return [d for _,_,d in ranked[:limit]]
