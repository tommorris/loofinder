from flask import Flask, Response, request
import requests
import operator
import json
app = Flask(__name__)


RANDOM_MODE = False

@app.route("/")
def index():
    html_page = open('index.html').read()
    return Response(html_page, mimetype="text/html")

@app.route("/search", methods=['GET'])
def find():
    #bbox_q = requests.args.get("bbox", '51.28,-0.489,51.686,0.236') #greater london
    bbox_q = '51.28,-0.489,51.686,0.236'
    q = """[out:json][timeout:25]; (
        node["amenity"="toilets"]({bbox});
        way["amenity"="toilets"]({bbox});
        relation["amenity"="toilets"]({bbox});
        ); out body; >; out skel qt;""".format(bbox=bbox_q)
    resp = requests.post("http://overpass-api.de/api/interpreter", q)
    data = resp.json()
    nodes = [node_to_gj(x) for x in data[u'elements'] if x[u'type'] == u'node' and u'tags' in x.keys() \
             and x[u'tags'].get(u'amenity', '') == u'toilets']
    supporting_nodes = [x for x in data[u'elements'] if x[u'type'] == u'node' and (u'tags' not in x.keys() or \
                        x[u'tags'].get(u'amenity', '') != u'toilets')]
    supporting_nodes_hash = {}
    for x in supporting_nodes:
        supporting_nodes_hash[x[u'id']] = x
    ways = [x for x in data[u'elements'] if x[u'type'] == u'way']
    ways = [{"way": x, "nodes": [supporting_nodes_hash[y] for y in x[u'nodes']]} for x in ways]
    ways = [annotated_way_to_gj(x) for x in ways]
    out = {
        "type": "FeatureCollection",
        "features": []
    }
    for node in nodes: out['features'].append(node)
    for way in ways: out['features'].append(way)
    return Response(response=json.dumps(out), status=200, mimetype="application/json")

def random_choice():
    import random
    return random.choice([True, False, None])

def node_to_gj(node):
    out = { "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [node[u'lon'], node[u'lat']]
            },
            "properties": {}
        }
    out['properties']['tags'] = node[u'tags']
    if u'name' in node[u'tags'].keys():
        out['properties']['name'] = node[u'tags'][u'name']
    if u'unisex' in node[u'tags'].keys():
        if node[u'tags'][u'unisex'] == u'yes':
            out['properties'][u'unisex'] = True
        elif node[u'tags'][u'unisex'] == u'no':
            out['properties'][u'unisex'] = False
    if RANDOM_MODE is True:
        out['properties'][u'unisex'] = random_choice()

    out['osm_node_id'] = node[u'id']
    return out

def annotated_way_to_gj(way):
    out = {"type": "Feature",
           "geometry": {},
           "properties": {}}
    out['properties']['tags'] = way['way']['tags']
    if 'name' in way['way']['tags'].keys():
        out['properties']['name'] = way['way']['tags']['name']
    if 'unisex' in way['way']['tags'].keys() and way['way']['tags']['unisex'] == u'yes':
        out['properties']['unisex'] = True
    elif 'unisex' in way['way']['tags'].keys() and way['way']['tags']['unisex'] == u'no':
        out['properties']['unisex'] = False
    if RANDOM_MODE is True:
        out['properties'][u'unisex'] = random_choice()


    if way['nodes'][0] == way['nodes'][-1]:
        # closed way
        lons = [x['lon'] for x in way['nodes']]
        lats = [x['lat'] for x in way['nodes']]
        lon_avg = float(reduce(operator.add, lons)) / float(len(lons))
        lat_avg = float(reduce(operator.add, lats)) / float(len(lats))
        #list = [[x['lon'], x['lat']] for x in way['nodes']]
        geometry = {"type": "Point",
                    "coordinates": [ lon_avg, lat_avg ]}
        out['geometry'] = geometry
        return out
    else:
        pass
        # open way

if __name__ == "__main__":
    app.run()
