from pathlib import Path
import hashlib,json,collections,time
import onnx
from onnx import numpy_helper
import argparse
parser=argparse.ArgumentParser(description='Read-only exact Faster graph inspection; no model inference')
parser.add_argument('--model',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
ROOT=args.output
ROOT.mkdir(parents=True,exist_ok=False)
(ROOT/'graph').mkdir()
MODEL=args.model

b=MODEL.read_bytes(); assert hashlib.sha256(b).hexdigest()=='fbf748e6d8b896bed9ee1eb15d5dd1409369de5e32c4746c4173aa4c10e7bebd'
m=onnx.load_model_from_string(b); del b
assert not any(t.external_data for t in m.graph.initializer)
onxxstart=time.monotonic(); onnx.checker.check_model(m)
def tensor(t):
 a=numpy_helper.to_array(t)
 return {'shape':list(a.shape),'dtype':str(a.dtype),'values':a.tolist() if a.size<=30 else None}
def attr(a):
 if a.type==onnx.AttributeProto.TENSOR:return tensor(a.t)
 v=onnx.helper.get_attribute_value(a)
 if isinstance(v,bytes):return v.decode(errors='replace')
 if isinstance(v,(int,float,str,list)):return v
 return str(v)
nodes=[{'index':i,'name':n.name,'op':n.op_type,'domain':n.domain,'inputs':list(n.input),'outputs':list(n.output),'attributes':{a.name:attr(a) for a in n.attribute}} for i,n in enumerate(m.graph.node)]
result={'model_sha256':hashlib.sha256(MODEL.read_bytes()).hexdigest(),'onnx_version':onnx.__version__,'producer_name':m.producer_name,'producer_version':m.producer_version,'ir_version':m.ir_version,'opsets':[{ 'domain':x.domain,'version':x.version}for x in m.opset_import],'metadata':[{ 'key':x.key,'value':x.value}for x in m.metadata_props],'inputs':[str(x)for x in m.graph.input],'outputs':[str(x)for x in m.graph.output],'node_count':len(nodes),'ops':dict(collections.Counter(n.op_type for n in m.graph.node)),'nodes':nodes,'initializers':{x.name:tensor(x) for x in m.graph.initializer},'checker':'pass'}
(ROOT/'graph/GRAPH.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items()if k not in ('nodes','initializers')},indent=2))
