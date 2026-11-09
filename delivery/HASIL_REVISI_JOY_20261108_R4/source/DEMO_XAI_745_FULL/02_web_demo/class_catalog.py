"""Dataset labels and newly authored operational definitions with provenance."""
import json
from pathlib import Path
from label_display import nama_task, tampil
QUESTIONS = {"task1_issue":"Isu atau topik apa yang dibahas sampul?", "task2_domain_sumber":"Ranah konsep apa yang menjadi perumpamaan?", "task3_primary_entity_type":"Jenis pihak atau entitas apa yang disorot?"}
def catalog(engine, definitions):
    operational=json.loads((Path(__file__).parent/'codebook_operasional.json').read_text(encoding='utf-8'))
    out=[]
    for task,classes in engine.maps.items():
        rows=[]
        for label in classes:
            examples=engine.df[engine.df[task].astype(str)==label].head(2)
            entry=operational[label]
            rows.append({"id":label,"name":tampil(label),"definition":entry['definition'],
                         "criteria":entry['criteria'],"boundary":entry['boundary'],"verification":"Draft definisi operasional baru; tidak mengubah anotasi historis",
                         "source":entry['source'],
                         "examples":entry['examples']})
        out.append({"id":task,"name":nama_task(task),"question":QUESTIONS[task],"classes":rows})
    return out
