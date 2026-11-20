"""Pydantic core-schema -> OWL/RDFS + SHACL compiler.

RDF instance encoding contract (necessary for deterministic SHACL validation):
- Model = RDF node with rdf:type <the generated class IRI>.
- Model field = one declaration-scoped RDF predicate per field.
- RootModel = a model node with a single ``root`` RDF property.
- Tuple = RDF Collection, using rdf:first/rdf:rest and terminating at rdf:nil.
- Numeric values = strictly typed RDF literals (xsd:integer / xsd:decimal).
- timedelta = xsd:dayTimeDuration lexical value.
- Python object payloads allowed by ``core_schema.type == 'any'`` are unconstrained;
  domain specializations must close those parameters to get a useful TBox.

A translation is FAILED on an unhandled core-schema kind/constraint. Do not
silently treat an unknown rule as unconstrained. The generated OWL is the TBox;
SHACL is the closed-world instance-structure contract. The same source also
carries the original class hierarchy, generic bindings, and Pydantic settings
as RDF metadata for audit, not as additional executable validators.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import quote

from pydantic import BaseModel, RootModel
from rdflib import BNode, Graph, Literal, Namespace, OWL, RDF, RDFS, SH, XSD
from rdflib.collection import Collection
from rdflib.term import Node, URIRef

ORG = Namespace('https://example.org/organizational-ontology#')
PYD = Namespace('https://example.org/pydantic-semantics#')


def uri(value: str) -> URIRef:
    return ORG[quote(value, safe='_-.')]


def qname(value: type[Any]) -> str:
    return f'{value.__module__}.{value.__qualname__}'


def models_in(modules: list[str]) -> list[type[BaseModel]]:
    found: dict[str,type[BaseModel]] = {}
    for mod in modules:
        module = importlib.import_module(mod)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (issubclass(cls, BaseModel) and cls.__module__ == mod
                    and cls not in {BaseModel,RootModel}):
                found[qname(cls)] = cls
    return list(found.values())


def declaring_class(cls: type[Any], field: str) -> str:
    """Find the earliest semantic declaration of an inherited field."""
    for parent in reversed(cls.__mro__):
        if isinstance(parent,type) and issubclass(parent,BaseModel) and field in parent.__dict__.get('__annotations__',{}):
            if parent not in {BaseModel,RootModel}: return qname(parent)
    return qname(cls)


class OntologyCompiler:
    def __init__(self) -> None:
        self.owl = Graph()
        self.shacl = Graph()
        self.meta = Graph()
        for g in (self.owl,self.shacl,self.meta):
            for prefix,ns in [('org',ORG),('pyd',PYD),('owl',OWL),('sh',SH),('rdf',RDF)]:
                g.bind(prefix,ns)
        self.seen: set[str] = set()
        self.root_models: dict[str,type[BaseModel]] = {}
        self.definitions: dict[str,dict[str,Any]] = {}
        self.encountered: set[str] = set()
        self.class_by_name: dict[str,type[BaseModel]] = {}
        self.field_prop_map: dict[str,set[URIRef]] = {}

    def rdf_list(self, graph: Graph, items: list[Node]) -> Node:
        if not items:return RDF.nil
        head=BNode()
        Collection(graph,head,items)
        return head

    def shape(self, key: str) -> URIRef:
        return uri(f'shape/{key}')

    def clazz(self, key: str) -> URIRef:
        return uri(f'class/{key}')

    def literal(self, value: Any) -> Node:
        if isinstance(value,bool):return Literal(value,datatype=XSD.boolean)
        if isinstance(value,int):return Literal(value,datatype=XSD.integer)
        if isinstance(value,Decimal):return Literal(value,datatype=XSD.decimal)
        if isinstance(value,timedelta):
            total=value.total_seconds()
            return Literal(f'PT{total:g}S',datatype=XSD.dayTimeDuration)
        if isinstance(value,str):return Literal(value,datatype=XSD.string)
        raise TypeError(f'Cannot preserve semantic literal {value!r} ({type(value)})')

    def collect_definitions(self, core: dict[str,Any]) -> None:
        def scan(value: Any):
            if isinstance(value,dict):
                if value.get('type')=='definitions':
                    for definition in value['definitions']:
                        if 'ref' not in definition:raise ValueError('Unreferenced definition')
                        self.definitions[definition['ref']]=definition
                for nested in value.values():scan(nested)
            elif isinstance(value,(list,tuple)):
                for nested in value:scan(nested)
        scan(core)

    def named(self, name: str, schema: dict[str,Any]) -> URIRef:
        """Declare a SHACL node shape corresponding to a complete Pydantic type."""
        kind=schema.get('type')
        if kind is None:raise ValueError(f'Core schema missing type at {name}')
        # Model identity belongs to the Pydantic class, not to whichever field
        # happens to reference it. Otherwise repeated constituents would get
        # different OWL classes and properties for the same semantic type.
        if kind == 'model':
            name = qname(schema['cls'])
        self.encountered.add(kind)
        shape=self.shape(name)
        if name in self.seen:return shape
        self.seen.add(name)
        g=self.shacl
        g.add((shape,RDF.type,SH.NodeShape))
        if kind=='definitions':
            for entry in schema['definitions']:
                if 'ref' not in entry:raise ValueError('Definition without reference')
                self.definitions[entry['ref']]=entry
            return self._alias(shape,name,schema['schema'])
        if kind=='definition-ref':
            ref=schema['schema_ref']
            if ref not in self.definitions:raise ValueError(f'Unknown Pydantic definition {ref}')
            ref_shape=self.named('definition/'+ref,self.definitions[ref])
            g.add((shape,SH.node,ref_shape))
            return shape
        if kind=='default':
            # Default applicability is handled by the parent property cardinality.
            self._alias(shape,name,schema['schema'])
            g.add((shape,PYD.defaultValue,self.literal(schema['default'])))
            return shape
        if kind=='model':
            cls=schema['cls']
            self.class_by_name[name] = cls
            if not inspect.isclass(cls):raise ValueError(f'Unexpected model class {cls!r}')
            self.owl.add((self.clazz(name),RDF.type,OWL.Class))
            self.owl.add((self.clazz(name),RDFS.label,Literal(cls.__name__)))
            self.owl.add((self.clazz(name),RDFS.comment,Literal(inspect.getdoc(cls) or '')))
            # Do not demand RDF instance has Python cls's exact type in contexts
            # where subclasses are accepted: OWL subclass inference is meaningful.
            g.add((shape,SH['class'],self.clazz(name)))
            self._fields(shape,name,schema)
            self.meta.add((self.clazz(name),PYD.pythonClass,Literal(qname(cls))))
            self.meta.add((self.clazz(name),PYD.rootModel,Literal(bool(schema.get('root_model')))))
            generic=getattr(cls,'__pydantic_generic_metadata__',{}) or {}
            self.meta.add((self.clazz(name),PYD.genericArguments,Literal(json.dumps([str(v) for v in generic.get('args',())]))))
            self.meta.add((self.clazz(name),PYD.configuration,Literal(json.dumps(schema.get('config',{}),default=str,sort_keys=True))))
            # Parent class hierarchy is an actual ontological specialization.
            self._lineage(cls)
            return shape
        if kind=='model-fields':
            # Normally enclosed by 'model', but can arise through references.
            self._model_fields(shape,name,schema,extra='forbid')
            return shape
        if kind in {'union','tagged-union'}:
            if kind=='tagged-union':
                choices=list(schema['choices'].values())
                # Same branch may be listed under several discriminator values.
                unique=[]
                seen=[]
                for c in choices:
                    marker=c.get('ref',repr(c)) if isinstance(c,dict) else repr(c)
                    if marker not in seen:seen.append(marker);unique.append(c)
                choices=unique
                relation=SH.xone
                self.meta.add((shape,PYD.discriminator,Literal(str(schema['discriminator']))))
            else:
                choices=[c[0] if isinstance(c,tuple) else c for c in schema['choices']]
                relation=SH['or']
            parts=[self.named(f'{name}/choice/{i}',c) for i,c in enumerate(choices)]
            g.add((shape,relation,self.rdf_list(g,parts)))
            # Logical union exists independently of SHACL's stronger closed-world
            # rule for discriminated cases.
            ontology_parts=[]
            for i,c in enumerate(choices):
                if c.get('type')=='model':ontology_parts.append(self.clazz(f'{name}/choice/{i}'))
            if len(ontology_parts)==len(parts):
                expr=BNode();self.owl.add((expr,RDF.type,OWL.Class))
                self.owl.add((expr,OWL.unionOf,self.rdf_list(self.owl,ontology_parts)))
                self.owl.add((self.clazz(name),OWL.equivalentClass,expr))
            return shape
        if kind=='literal':
            expected=schema.get('expected')
            if not isinstance(expected,list):raise ValueError(f'Invalid Literal at {name}')
            g.add((shape,SH['in'],self.rdf_list(g,[self.literal(v) for v in expected])))
            return shape
        if kind=='any':
            # Unconstrained on purpose, identical to the source generic template.
            return shape
        if kind=='tuple':
            self._tuple(shape,name,schema)
            return shape
        if kind in ('str','int','decimal','timedelta'):
            self._scalar(shape,name,schema)
            return shape
        raise ValueError(f'Unsupported Pydantic core-schema node {kind!r} at {name}')

    def _lineage(self,cls:type[BaseModel],visited:set[type[BaseModel]]|None=None)->None:
        visited = set() if visited is None else visited
        if cls in visited:return
        visited.add(cls)
        self.owl.add((self.clazz(qname(cls)),RDF.type,OWL.Class))
        for base in cls.__bases__:
            if isinstance(base,type) and issubclass(base,BaseModel) and base not in {BaseModel,RootModel}:
                self.owl.add((self.clazz(qname(base)),RDF.type,OWL.Class))
                self.owl.add((self.clazz(qname(cls)),RDFS.subClassOf,self.clazz(qname(base))))
                self._lineage(base,visited)

    def _alias(self,shape:URIRef,name:str,target:dict[str,Any]) -> URIRef:
        self.shacl.add((shape,SH.node,self.named(name+'/target',target)))
        return shape

    def _fields(self,shape:URIRef,name:str,schema:dict[str,Any]) -> None:
        config=schema.get('config',{})
        if schema.get('root_model'):
            self._property(shape,name,'root',schema['schema'],required=True)
            self._closed(shape,True)
        else:
            inner=schema['schema']
            if inner['type']!='model-fields':raise ValueError(f'Unexpected model body {inner["type"]} at {name}')
            self._model_fields(shape,name,inner,extra=config.get('extra_fields_behavior','ignore'))

    def _model_fields(self,shape:URIRef,name:str,fields:dict[str,Any],extra:str) -> None:
        if extra not in {'forbid','ignore','allow'}:raise ValueError(f'Unsupported extra policy {extra}')
        for field,wrapper in fields['fields'].items():
            if wrapper['type']!='model-field':raise ValueError('Unhandled field declaration')
            declared=wrapper['schema']
            self._property(shape,name,field,declared,required=(declared.get('type')!='default'))
        if extra=='forbid':self._closed(shape,True)
        elif extra=='allow':
            # An arbitrary additional-property map is not interchangeable with
            # arbitrary RDF predicates; require a domain mapping, not guess.
            raise ValueError(f'Unbounded extra fields are not supported at {name}')
        self.meta.add((shape,PYD.extraPolicy,Literal(extra)))

    def _closed(self,shape:URIRef,closed:bool) -> None:
        g=self.shacl
        g.add((shape,SH.closed,Literal(closed)))
        g.add((shape,SH.ignoredProperties,self.rdf_list(g,[RDF.type])))

    def _property(self,shape:URIRef,name:str,field:str,schema:dict[str,Any],required:bool):
        g=self.shacl
        declaring=declaring_class(self.class_by_name[name],field)
        prop=uri('property/'+declaring+'/'+field)
        self.field_prop_map.setdefault(name,set()).add(prop)
        universal=uri('property/'+field)
        p=BNode();g.add((shape,SH.property,p));g.add((p,SH.path,prop))
        g.add((p,SH.minCount,Literal(1 if required else 0)))
        g.add((p,SH.maxCount,Literal(1)))
        g.add((p,SH.node,self.named(name+'/field/'+field,schema)))
        self.owl.add((prop,RDF.type,RDF.Property))
        self.owl.add((universal,RDF.type,RDF.Property))
        self.owl.add((prop,RDFS.subPropertyOf,universal))
        self.owl.add((prop,RDFS.label,Literal(field)))
        restriction=BNode()
        self.owl.add((restriction,RDF.type,OWL.Restriction))
        self.owl.add((restriction,OWL.onProperty,prop))
        self.owl.add((restriction,OWL.minCardinality,Literal(1 if required else 0,datatype=XSD.nonNegativeInteger)))
        self.owl.add((restriction,OWL.maxCardinality,Literal(1,datatype=XSD.nonNegativeInteger)))
        # OWL gets genuine object/data ranges when the constituent is simple;
        # richer sums and positional tuples are preserved in SHACL.
        unwrapped=schema['schema'] if schema.get('type')=='default' else schema
        if unwrapped['type']=='model':
            self.owl.add((restriction,OWL.allValuesFrom,self.clazz(qname(unwrapped['cls']))))
        elif unwrapped['type'] in {'str','int','decimal','timedelta'}:
            typ={'str':XSD.string,'int':XSD.integer,'decimal':XSD.decimal,'timedelta':XSD.dayTimeDuration}[unwrapped['type']]
            self.owl.add((restriction,OWL.allValuesFrom,typ))
        self.owl.add((self.clazz(name),RDFS.subClassOf,restriction))
        if schema.get('type')=='default':
            self.shacl.add((p,SH.defaultValue,self.literal(schema['default'])))

    def _tuple(self,shape:URIRef,name:str,schema:dict[str,Any]) -> None:
        g=self.shacl
        g.add((shape,SH.nodeKind,SH.BlankNodeOrIRI))
        self._list_wellformed(shape)
        members=schema['items_schema']
        variation=schema.get('variadic_item_index')
        if variation is not None and (variation!=0 or len(members)!=1):
            raise ValueError(f'Variable tuple at other than initial homogeneous position: {name}')
        if variation is None:
            n=len(members)
            for i,t in enumerate(members):
                p=BNode();g.add((shape,SH.property,p))
                g.add((p,SH.path,self.rdf_list(g,[RDF.rest]*i+[RDF.first])))
                g.add((p,SH.minCount,Literal(1)));g.add((p,SH.maxCount,Literal(1)))
                g.add((p,SH.node,self.named(name+'/position/'+str(i),t)))
            if n == 0:
                g.add((shape,SH['in'],self.rdf_list(g,[RDF.nil])))
            else:
                term=BNode();g.add((shape,SH.property,term))
                g.add((term,SH.path,self.rdf_list(g,[RDF.rest]*n)))
                g.add((term,SH.hasValue,RDF.nil))
                g.add((term,SH.minCount,Literal(1)))
                g.add((term,SH.maxCount,Literal(1)))
        else:
            p=BNode();g.add((shape,SH.property,p))
            path=self.rdf_list(g,[BNode(),RDF.first]);first=g.value(path,RDF.first)
            g.add((first,SH.zeroOrMorePath,RDF.rest))
            g.add((p,SH.path,path))
            g.add((p,SH.node,self.named(name+'/item',members[0])))
            for limit,predicate in [('min_length',SH.minCount),('max_length',SH.maxCount)]:
                if limit in schema:g.add((p,predicate,Literal(schema[limit])))
        if variation is None:
            for key,expected in (('min_length',len(members)),('max_length',len(members))):
                if key in schema and schema[key]!=expected:
                    raise ValueError(f'Tuple cardinality conflicts with its items at {name}')

    def _list_wellformed(self,shape:URIRef) -> None:
        g=self.shacl;p=BNode();g.add((shape,SH.sparql,p))
        g.add((p,SH.message,Literal('RDF collection must terminate at rdf:nil, have one item and next per cell, and contain no cycles.')))
        g.add((p,SH.select,Literal('''PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT $this WHERE {
 FILTER (
  NOT EXISTS { $this rdf:rest* rdf:nil }
  || EXISTS { $this rdf:rest+ $this }
  || EXISTS { $this rdf:rest* ?c . FILTER(?c != rdf:nil)
              FILTER NOT EXISTS { ?c rdf:first ?item ; rdf:rest ?tail } }
  || EXISTS { $this rdf:rest* ?c . ?c rdf:first ?x, ?y . FILTER(?x != ?y) }
  || EXISTS { $this rdf:rest* ?c . ?c rdf:rest ?x, ?y . FILTER(?x != ?y) }
 )
}''')))

    def _scalar(self,shape:URIRef,name:str,schema:dict[str,Any]) -> None:
        kind=schema['type'];g=self.shacl
        dtype={'str':XSD.string,'int':XSD.integer,'decimal':XSD.decimal,'timedelta':XSD.dayTimeDuration}[kind]
        g.add((shape,SH.datatype,dtype))
        for p,term in [('ge',SH.minInclusive),('gt',SH.minExclusive),('le',SH.maxInclusive),('lt',SH.maxExclusive),('min_length',SH.minLength),('max_length',SH.maxLength),('pattern',SH.pattern)]:
            if p in schema:g.add((shape,term,self.literal(schema[p])))
        if kind=='str' and schema.get('strip_whitespace',False):
            # Pydantic strips before validating, but RDF is canonicalized at
            # serialization: explicit SHACL check enforces normalized values.
            self.meta.add((shape,PYD.normalization,Literal('strip_whitespace')))
        if schema.get('allow_inf_nan',False):
            raise ValueError(f'Decimal infinity/NaN not representable in xsd:decimal: {name}')
        if 'multiple_of' in schema:
            raise ValueError(f'multiple_of requires custom SHACL constraint: {name}')
        # Metadata does not relax the underlying lexical/RDF datatype.
        self.meta.add((shape,PYD.strict,Literal(bool(schema.get('strict')))))

    def compile(self, classes: list[type[BaseModel]]) -> OntologyCompiler:
        # First register definitions from all roots (forward refs supported).
        for cls in classes:self.collect_definitions(cls.__pydantic_core_schema__)
        for cls in classes:
            core=cls.__pydantic_core_schema__
            k=qname(cls)
            target=self.named(k,core)
            self.shacl.add((target,SH.targetClass,self.clazz(k)))
            self.owl.add((self.clazz(k),RDF.type,OWL.Class))
            self.owl.add((self.clazz(k),RDFS.seeAlso,target))
            self.root_models[k]=cls
            # Each specialization retains the source declaration as evidence.
            self.meta.add((self.clazz(k),PYD.declaredType,Literal(k)))
        # A parent shape's closed list cannot reject extra *declared* fields
        # introduced by a subtype. Instead, direct parent instances get a
        # conditional closure constraint, while subclass leaf shapes remain
        # closed on their full inherited fields.
        classes=list(self.class_by_name.items())
        for name, cls in classes:
            descendants=[(child_name,child) for child_name,child in classes
                         if child is not cls and issubclass(child,cls)]
            if not descendants:continue
            shape=self.shape(name)
            if (shape,SH.closed,Literal(True)) not in self.shacl:continue
            self.shacl.remove((shape,SH.closed,Literal(True)))
            self.shacl.remove((shape,SH.ignoredProperties,None))
            props=self.field_prop_map.get(name,set())
            permitted=','.join(f'<{x}>' for x in sorted(props,key=str))
            allowed=', '.join(x for x in [f'<{RDF.type}>',permitted] if x)
            query=f'''PREFIX rdf: <{RDF}>
PREFIX rdfs: <{RDFS}>
SELECT $this WHERE {{
  $this rdf:type <{self.clazz(name)}> ; ?predicate ?value .
  FILTER (?predicate NOT IN ({allowed}))
  FILTER NOT EXISTS {{
    $this rdf:type ?moreSpecific .
    ?moreSpecific rdfs:subClassOf+ <{self.clazz(name)}> .
    FILTER (?moreSpecific != <{self.clazz(name)}>)
  }}
}}'''
            constraint=BNode()
            self.shacl.add((shape,SH.sparql,constraint))
            self.shacl.add((constraint,SH.message,Literal('Unexpected field on a directly typed instance.')))
            self.shacl.add((constraint,SH.select,Literal(query)))
        return self

    def write(self, output:Path)->None:
        output.mkdir(parents=True,exist_ok=True)
        for g,name in ((self.owl,'ontology.ttl'),(self.shacl,'shapes.ttl'),(self.meta,'typing.ttl')):
            g.serialize(destination=output/name,format='turtle')
        report={'root_models':len(self.root_models),'core_schema_kinds':sorted(self.encountered),
                'ontology_statements':len(self.owl),'shape_statements':len(self.shacl),
                'metadata_statements':len(self.meta),
                'warning':'RDF requires canonical literal typing and the documented collection encoding; semantic equivalence requires instance-level validation parity tests.'}
        (output/'coverage.json').write_text(json.dumps(report,indent=2))


def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',type=Path,default=Path('rdf-schema'))
    ap.add_argument('--modules',nargs='+',default=['ontok.scalars','ontok.work','ontok.value','ontok.examples'])
    args=ap.parse_args()
    types=models_in(args.modules)
    compiler=OntologyCompiler().compile(types)
    compiler.write(args.output)
    print(f'Compiled {len(types)} types, {len(compiler.owl)} OWL triples, {len(compiler.shacl)} SHACL triples.')

if __name__=='__main__':main()
