#!/usr/bin/env python3
'''rtx_kg1_neo4j_to_kg_json.py: extract RTX KG1 from Neo4j to a JSON file in KG2 format

   Usage: run "rtx_kg1_neo4j_to_kg_json.py --help" to get usage information
'''

__author__ = 'Stephen Ramsey'
__copyright__ = 'Oregon State University'
__credits__ = ['Stephen Ramsey']
__license__ = 'MIT'
__version__ = '0.1.0'
__maintainer__ = ''
__email__ = ''
__status__ = 'Prototype'

# SAVE: this is an example REST query of Neo4j
#curl -H 'Content-type: application/json' -X POST -d '{"query": "MATCH (n) return count(*)"}' --user neo4j:precisionmedicine http://kg1endpoint.rtx.ai:7474/db/data/cypher

import argparse
import json
import kg2_util
import pprint
import requests
import sys


TIMEOUT_SEC = 120

KG1_PROVIDED_BY_TO_KG2_IRIS = {
    'gene_ontology': "http://purl.obolibrary.org/obo/GO",
    'PC2': 'http://pathwaycommons.org/pc11/',
    'BioLink': 'http://w3id.org/biolink/vocab/',
    'KEGG;UniProtKB': 'https://www.uniprot.org/',
    'OMIM': 'http://purl.bioontology.org/ontology/OMIM/',
    'DisGeNet': 'http://www.disgenet.org',
    'DGIdb;MyCancerGenomeClinicalTrial': 'http://www.dgidb.org',
    'reactome': 'https://identifiers.org/reactome',
    'DGIdb;FDA': 'http://www.dgidb.org',
    'DGIdb;NCI': 'http://www.dgidb.org',
    'DGIdb;TALC': 'http://www.dgidb.org',
    'DGIdb;TTD': 'http://www.dgidb.org',
    'DGIdb;GuideToPharmacologyInteractions': 'http://www.dgidb.org',
    'DGIdb;ChemblInteractions': 'http://www.dgidb.org',
    'DGIdb;TdgClinicalTrial': 'http://www.dgidb.org',
    'ChEMBL': 'https://www.ebi.ac.uk/chembl'
    }


def query_neo4j(neo4j_auth: dict, http_uri: str, cypher_query: str):
    if not http_uri.startswith('http://') and not http_uri.startswith('https://'):
        http_uri = 'http://' + http_uri
    if not http_uri.endswith('/db/data'):
        http_uri = http_uri + '/db/data'
    http_uri = http_uri + "/cypher"
    query_response = requests.post(http_uri,
                                   headers={'Content-type': 'application/json; charset=UTF-8; stream=true',
                                            'Accept': 'application/json'},
                                   data=json.dumps({'query': cypher_query, 'params': {}}),
                                   auth=requests.auth.HTTPBasicAuth(neo4j_auth['user'],
                                                                    neo4j_auth['password']),
                                   timeout=TIMEOUT_SEC)
    status_code = query_response.status_code
    if status_code != 200:
        print('HTTP response status code: ' + str(status_code) + ' for URL: ' + http_uri, file=sys.stderr)
        query_response = None
    return query_response.json()['data']


def make_arg_parser():
    arg_parser = argparse.ArgumentParser(description='rtx_kg1_neo4j_to_kg_json.py: downloads the RTX KG1 from a Neo4j endpoint, as a JSON file')
    arg_parser.add_argument("-c", "--configFile", type=str, help="The RTXConfiguration config.json file", default=None)
    arg_parser.add_argument("-u", "--user", type=str, help="The neo4j username", default=None)
    arg_parser.add_argument("-p", "--password", type=str, help="The neo4j passworl", default=None)
    arg_parser.add_argument("-e", "--endpoint_uri", type=str, help="The neo4j HTTP URI (including port)",
                            default="http://localhost:7474")
    arg_parser.add_argument('--test', dest='test', action='store_true', default=False)
    arg_parser.add_argument('outputFileName', type=str, help="The filename of the output JSON file")
    return arg_parser.parse_args()


if __name__ == '__main__':
    args = make_arg_parser()
    test_mode = args.test
    output_file_name = args.outputFileName
    config_file = args.configFile
    if config_file is not None:
        config_data = json.load(open(config_file, 'r'))
        neo4j_user = config_data['Production']['neo4j']['username']
        neo4j_password = config_data['Production']['neo4j']['password']
        neo4j_endpoint_uri = config_data['Production']['neo4j']['database']
    else:
        neo4j_user = args.user
        neo4j_password = args.password
        neo4j_endpoint_uri = args.endpoint_uri
    query_statement = "MATCH (n) RETURN n"
    if test_mode:
        query_statement += " limit 10000"
    neo4j_auth = {'user': neo4j_user,
                  'password': neo4j_password}
    nodes_result = query_neo4j(neo4j_auth,
                               neo4j_endpoint_uri,
                               query_statement)
    nodes_list = [data_dict[0]['data'] for data_dict in nodes_result]
    for node_dict in nodes_list:
        del node_dict['accession']
        del node_dict['expanded']
        del node_dict['UUID']
        del node_dict['seed_node_uuid']
        del node_dict['rtx_name']
        assert node_dict.get('uri', None) is not None
        iri = node_dict['uri']
        del node_dict['uri']
        assert node_dict.get('id', None) is not None
        category_label = node_dict['category']
        node_dict['category'] = kg2_util.convert_biolink_category_to_iri(category_label)
        node_dict['category label'] = category_label
        node_dict['iri'] = iri
        symbol = node_dict.get('symbol', None)
        synonym_list = []
        if symbol is not None:
            synonym_list.append(symbol)
            del node_dict['symbol']
        node_dict['full name'] = node_dict['name']
        node_dict['description'] = node_dict.get('description', None)
        node_dict['synonym'] = synonym_list
        node_dict['publications'] = []
        node_dict['update date'] = None
        node_dict['deprecated'] = False
        node_dict['replaced by'] = None
        node_dict['provided by'] = None
#    pprint.pprint(nodes_list)
    query_statement = "MATCH (n)-[r]->(m) RETURN n.id, r, m.id"
    if test_mode:
        query_statement += " limit 10000"
    edges_result = query_neo4j(neo4j_auth,
                               neo4j_endpoint_uri,
                               query_statement)
    edges_list = [kg2_util.merge_two_dicts({'subject': result_item_list[0],
                                            'object': result_item_list[2]},
                                           result_item_list[1]['data'])
                  for result_item_list in edges_result]
    for edge_dict in edges_list:
        del edge_dict['is_defined_by']
        del edge_dict['seed_node_uuid']
        del edge_dict['source_node_uuid']
        del edge_dict['target_node_uuid']
        predicate_label = edge_dict['relation']
        edge_dict['edge label'] = predicate_label
        del edge_dict['relation']
        [relation, relation_curie] = kg2_util.biolink_predicate_label_to_iri_and_curie(predicate_label)
        edge_dict['relation'] = relation
        edge_dict['relation curie'] = relation_curie
        edge_dict['negated'] = False
        publications = edge_dict.get('publications', None)
        if publications is not None and publications != '':
            publications = publications.split(',')
        else:
            publications = []
        edge_dict['publications'] = publications
        edge_dict['publications info'] = {}
        edge_dict['update date'] = None
        provided_by = edge_dict['provided_by']
        provided_by_kg2 = KG1_PROVIDED_BY_TO_KG2_IRIS.get(provided_by, None)
        edge_dict['provided by'] = provided_by_kg2
        if provided_by_kg2 is None:
            print("Unable to find a KG2 provided IRI for this KG1 source: " + provided_by,
                  file=sys.stderr)
        del edge_dict['provided_by']
    graph = {'nodes': nodes_list,
             'edges': edges_list}
    kg2_util.save_json(graph, output_file_name, test_mode)