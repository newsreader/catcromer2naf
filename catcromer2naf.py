#!/usr/bin/env python

# This script reads a CAT XML file and converts it to NAF XML
# This script also takes into account the named entities from the CROMER layer that 
# were already included in the CAT files by FBK.

# It writes the *RAW text layer, *tokens layer, *entities layer and timex layer 

# Date: 15 April 2015
# Author: Marieke van Erp  
# Contact: marieke.van.erp@vu.nl

# Update 20 April
# Now it also writes the SRL layer 

import sys
from KafNafParserPy import *
import re

#infile = open('Data/wikinews_CAT_CROMER_160415/corpus_airbus/1173_Internal_emails_expose_Boeing-Air_Force_contract_discussions.txt.xml',"r")
infile = open(sys.argv[1],"r")
raw = infile.read()    
root = etree.XML(raw)

# maak een lijst van tokens:
token_list = root.findall(".//token")
num_sents = int(token_list[-1].get("sentence"))

# Init KafNafParserobject
my_parser = KafNafParser(None, type='NAF')
my_parser.root.set('{http://www.w3.org/XML/1998/namespace}lang','en')
my_parser.root.set('version','v3')
textlayer = Ctext()
termlayer = Cterms()
timexlayer = CtimeExpressions()

offset = 0
num = 0 
rawtext = '' 

sents = [root.findall(".//token[@sentence='%s']" % str(n)) for n in range(0,num_sents + 1)]
for sent in sents:
	num = num + 1 
	for node in sent:
		wf = Cwf() 
		wf.set_id(node.get("t_id"))
		sentence_no = int(node.get("sentence")) + 1
		wf.set_sent(str(sentence_no))
		wf.set_para("1")
		wf.set_offset(str(offset))
		offset = offset + len(node.text)
		wf.set_length(str(len(node.text)))
		wf.set_text(node.text)
		my_parser.add_wf(wf)
		term = Cterm()
		term.set_id(node.get("t_id"))
		term.set_lemma(node.text)
		term_span = Cspan()
		term_target = Ctarget()
		term_target.set_id(node.get("t_id"))
		term_span.add_target(term_target)
		term.set_span(term_span)
		my_parser.add_term(term)
		rawtext = rawtext + " " + node.text


# get a list of all entities
entities_list = root.findall(".//ENTITY") 
entities_ids = {}
entities_refs = {}

for entity in entities_list:
	entities_ids[entity.get("m_id")] = entity.get("ent_type")
	external_ref = str(entity.get("external_ref"))
	entities_refs[entity.get("m_id")] = external_ref
 #	print entity.get("m_id"), entity.get("ent_type"), external_ref
	
# Get the refers to relations to match the instances to the mentions 
refers_to_relations = root.findall(".//REFERS_TO")
relation_sources = {}
for relation in refers_to_relations:
	target = relation.findall(".//target")
	sources = relation.findall(".//source")
	for source in sources:
		relation_sources[source.get("m_id")] = target[0].get("m_id")
#		print source.get("m_id"), target[0].get("m_id")

# get a list of all entity mentions :
entity_mentions_list = root.findall(".//ENTITY_MENTION")
entity_mention_ids = {} 
for entity in entity_mentions_list:
	entity_mention_ids[entity.get("m_id")] = []
	entity_mention_anchors = entity.findall(".//token_anchor")
	for tokens in entity_mention_anchors:
		entity_mention_ids[entity.get("m_id")].append(tokens.get("t_id"))
		
#print len(entity_mention_ids), len(entities_ids)

# get a list of all entity mentions and create NAF entities for each of them
for mention in entity_mention_ids:
	entity = Centity()
	entity.set_id(mention)
	if mention not in relation_sources:
		continue
	entity.set_type(entities_ids[relation_sources[mention]])
	externalreferenceslayer = CexternalReferences()
	new_ext_reference = CexternalReference()
	new_ext_reference.set_resource('byCROMER')
	new_ext_reference.set_reference(str(entities_refs[relation_sources[mention]]))
	new_ext_reference.set_confidence('1.0')
	entity.add_external_reference(new_ext_reference)
	my_parser.add_entity(entity)
	reference = Creferences()
	reference_span = Cspan()
	span_target = Ctarget()
	reference_span.add_target(span_target)
	span_targets = entity_mention_ids[mention]
	reference.add_span(span_targets)
	entity.add_reference(reference)
#	print mention, entity_mention_ids[mention], relation_sources[mention], entities_ids[relation_sources[mention]], entities_refs[relation_sources[mention]]

# Get a list of the timexes
timexes_list = root.findall(".//TIMEX3")
timex_ids = {}
timex_values = {}
timex_types = {}

for timex in timexes_list:
	timex_ids[timex.get("m_id")] = []
	timex_values[timex.get("m_id")] = timex.get("value")
	timex_types[timex.get("m_id")] = timex.get("type")
	timex_mention_anchors = timex.findall(".//token_anchor")
	for tokens in timex_mention_anchors:
		timex_ids[timex.get("m_id")].append(tokens.get("t_id"))

# and create NAF timex objects for them
for item, targets in timex_ids.items():
	timex = Ctime()
	timex.set_id(item)
	timex.set_type(timex_types[item])
	timex.set_value(timex_values[item])
	timex_span = Cspan()
	timex_span.create_from_ids(targets)
	timex.set_span(timex_span)
	my_parser.add_timex(timex)

# Create the raw text layer 
rawlayer = my_parser.set_raw(rawtext) 

# Initialise the mentions dictionary to capture all the CAT mentions         
mention_ids = {}

# get a list of all entity mentions :
entity_mentions_list = root.findall(".//ENTITY_MENTION")
for entity in entity_mentions_list:
    mention_ids[entity.get("m_id")] = []
    entity_mention_anchors = entity.findall(".//token_anchor")
    for tokens in entity_mention_anchors:
        mention_ids[entity.get("m_id")].append(tokens.get("t_id"))
         
# get a list of all event mentions :
event_mentions_list = root.findall(".//EVENT_MENTION")
for event in event_mentions_list:
    mention_ids[event.get("m_id")] = []
    event_mention_anchors = event.findall(".//token_anchor")
    for tokens in event_mention_anchors:
        mention_ids[event.get("m_id")].append(tokens.get("t_id"))
     
# get a list of all timex mentions :
timex_mentions_list = root.findall(".//TIMEX3")
for timex in timex_mentions_list:
    mention_ids[timex.get("m_id")] = []
    timex_mention_anchors = timex.findall(".//token_anchor")
    for tokens in timex_mention_anchors:
        mention_ids[timex.get("m_id")].append(tokens.get("t_id"))
		
# get a list of all CSIGNAL mentions :
csignal_mentions_list = root.findall(".//C-SIGNAL")
for csignal in csignal_mentions_list:
    mention_ids[csignal.get("m_id")] = []
    csignal_mention_anchors = csignal.findall(".//token_anchor")
    for tokens in csignal_mention_anchors:
        mention_ids[csignal.get("m_id")].append(tokens.get("t_id"))		

# get a list of all CSIGNAL mentions :
signal_mentions_list = root.findall(".//SIGNAL")
for signal in signal_mentions_list:
    mention_ids[signal.get("m_id")] = []
    signal_mention_anchors = signal.findall(".//token_anchor")
    for tokens in signal_mention_anchors:
        mention_ids[signal.get("m_id")].append(tokens.get("t_id"))
      
# Get a list of all the SRL relations
srl_mentions_list = root.findall(".//HAS_PARTICIPANT")
srl_sources = {}
srl_targets = {}
srl_predicates = {}
srl_roles = {}
for srl in srl_mentions_list:
    srl_source_mentions = srl.findall(".//source")
    srl_target_mentions = srl.findall(".//target")
    try:
        srl_targets[srl.get("r_id")] = srl_target_mentions[0].get("m_id")
    except:
        pass
    try:
        srl_sources[srl.get("r_id")] = srl_source_mentions[0].get("m_id")
    except:
        pass 
    srl_roles[srl.get("r_id")] = srl.get("sem_role")
    if srl_source_mentions[0].get("m_id") in srl_predicates:
        srl_predicates[srl_source_mentions[0].get("m_id")].append(srl.get("r_id"))
    else:
        srl_predicates[srl_source_mentions[0].get("m_id")] = []
        srl_predicates[srl_source_mentions[0].get("m_id")].append(srl.get("r_id"))
       
# Create NAF SRL objects
for predicate in srl_predicates:
    new_predicate = Cpredicate()
    new_predicate.set_id('pr'+ str(predicate))
    predicate_span = Cspan()
    for item in mention_ids[predicate]:
        predicate_span.add_target_id(item)
    new_predicate.set_span(predicate_span)
    my_parser.add_predicate(new_predicate)
    for relation in srl_predicates[predicate]:
        role = Crole()
        role.set_id(relation)
        role.set_sem_role(srl_roles[relation])
        role_span = Cspan()
        try:
            for item in mention_ids[srl_targets[relation]]:
                role_span.add_target_id(item) 
            role.set_span(role_span)
            new_predicate.add_role(role)
        except:
            pass

# Print the whole thing 
my_parser.dump()
