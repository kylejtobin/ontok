"""Static coverage checks; NOT a SHACL engine or a parity proof."""
from pathlib import Path
from rdflib import Graph, SH, RDFS, OWL, RDF, XSD
from rdflib.plugins.sparql.parser import parseQuery
from core_to_rdf import uri

root=Path(__file__).parent
if not (root/'ontology.ttl').exists():root=root/'core-rdf'
O=Graph().parse(root/'ontology.ttl')
S=Graph().parse(root/'shapes.ttl')
T=Graph().parse(root/'typing.ttl')
work='Purpose Activity Process Role Authority Rule Decision Event Interaction Outcome'.split()
concepts=[('organization_model.work',n) for n in work]
concepts += [('organization_model.value',n) for n in 'Value Economic Time Quality Risk Capability HumanWelfare Relationships Resources'.split()]
for mod,name in concepts:
    x=uri('class/'+mod+'.'+name)
    assert (x,RDF.type,OWL.Class) in O,(mod,name,'class missing')
    shape=uri('shape/'+mod+'.'+name)
    assert (shape,SH.targetClass,x) in S,(mod,name,'target shape missing')
print('Named concepts:',len(concepts),'verified')
for cls,parent in [('organization_model.work.Process','organization_model.work.Activity'),('organization_model.value.Economic','organization_model.value.Value'),('organization_model.examples.RefundPurpose','organization_model.work.Purpose')]:
    goal=uri('class/'+parent);todo=[uri('class/'+cls)];seen=set();found=False
    while todo:
        node=todo.pop()
        if node in seen:continue
        seen.add(node)
        if node==goal:found=True;break
        todo.extend(x for x in O.objects(node,RDFS.subClassOf) if x.startswith('https://'))
    assert found,('inheritance missing',cls,parent)
print('Inheritance chains verified')
xone=list(S.triples((None,SH.xone,None)))
assert len(xone)>=1
print('SHACL exclusive alternatives',len(xone))
qs=list(S.objects(None,SH.select))
for q in qs:parseQuery(str(q))
print('SHACL-SPARQL queries parsed',len(qs))
print('Triples OWL/SHACL/meta:',len(O),len(S),len(T))
print('STATIC COVERAGE ONLY: no SHACL engine and no instance equivalence testing')
