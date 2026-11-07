"""Fixed deployable decoding: only INVALID uses the target fold's training majority."""
from collections import Counter

def training_majority_fallback(raw,truth,fold,classes):
    assert len(raw)==len(truth)==len(fold)>0 and classes==sorted(set(classes)) and len(classes)==7
    assert all(value in classes or value=='INVALID' for value in raw)
    assert all(value in classes for value in truth) and set(fold)=={1,2,3,4,5}
    policies={}
    for k in range(1,6):
        training=[truth[i] for i in range(len(truth)) if fold[i]!=k]
        counts=Counter(training)
        chosen=max(classes,key=lambda label:counts[label])
        policies[str(k)]=dict(label=chosen,counts={label:counts[label] for label in classes},
                              training_samples=len(training),test_samples=sum(value==k for value in fold))
    applied=[value=='INVALID' for value in raw]
    final=[policies[str(fold[i])]['label'] if applied[i] else value for i,value in enumerate(raw)]
    assert all(value in classes for value in final)
    return final,applied,policies
