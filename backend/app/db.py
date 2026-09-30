import json, os, sqlite3
from contextlib import closing
from pathlib import Path

DEFAULT_DB_PATH = '/tmp/ps120.db' if os.getenv('VERCEL') else 'data/ps120.db'
DB_PATH=os.getenv('PS120_DB_PATH', DEFAULT_DB_PATH)
Path(DB_PATH).parent.mkdir(parents=True,exist_ok=True)
def connect():
    db=sqlite3.connect(DB_PATH); db.execute('CREATE TABLE IF NOT EXISTS scenarios (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'); db.execute('CREATE TABLE IF NOT EXISTS nwis_events (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'); db.execute('CREATE TABLE IF NOT EXISTS nwis_wells (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)'); db.commit(); return db
def list_scenarios():
    with closing(connect()) as db:
        return [{**json.loads(payload),'id':i,'name':name} for i,name,payload in db.execute('SELECT id,name,payload FROM scenarios ORDER BY id DESC')]
def add_scenario(item):
    with closing(connect()) as db:
        cur=db.execute('INSERT INTO scenarios(name,payload) VALUES (?,?)',(item['name'],json.dumps({k:v for k,v in item.items() if k not in ('id','name')})));db.commit();item['id']=cur.lastrowid
    return item
def list_nwis_events():
    with closing(connect()) as db:
        return [{**json.loads(payload),'id':i,'created_at':created} for i,payload,created in db.execute('SELECT id,payload,created_at FROM nwis_events ORDER BY id DESC')]
def add_nwis_events(items):
    with closing(connect()) as db:
        ids=[]
        for item in items:
            cur=db.execute('INSERT INTO nwis_events(payload) VALUES (?)',(json.dumps(item,ensure_ascii=False),));ids.append(cur.lastrowid)
        db.commit()
    return ids
def list_nwis_wells():
    with closing(connect()) as db:
        markers=[(i,json.loads(payload)) for i,payload in db.execute('SELECT id,payload FROM nwis_wells ORDER BY id DESC') if json.loads(payload).get('dataset_marker')]
        if not markers: return []
        dataset_id=markers[0][0]
        return [json.loads(payload) for (payload,) in db.execute('SELECT payload FROM nwis_wells WHERE id>? ORDER BY id',(dataset_id,))]
def replace_nwis_wells(items):
    # Keep prior survey uploads recoverable in SQLite while switching the active map dataset.
    with closing(connect()) as db:
        cur=db.execute('INSERT INTO nwis_wells(payload) VALUES (?)', (json.dumps({'dataset_marker':True,'active':False},ensure_ascii=False),))
        dataset_id=cur.lastrowid
        for item in items:
            db.execute('INSERT INTO nwis_wells(payload) VALUES (?)',(json.dumps({**item,'dataset_id':dataset_id},ensure_ascii=False),))
        db.commit()
    return dataset_id
