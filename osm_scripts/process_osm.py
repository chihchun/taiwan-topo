# -*- coding: utf-8 -*-
import json
import sys

import osmium

hknetworks = {}

def round_float(value):
    try:
        return str(int(round(float(value))))
    except ValueError:
        return None


class HknetworkLoader(osmium.SimpleHandler):
    def relation(self, r):
        if not r.members:
            return
        network = dict(name=r.tags['name'], network=r.tags['network'], ref=r.tags.get('ref',''))
        for m in r.members:
            if not hknetworks.get(m.ref):
                hknetworks[m.ref] = []
            hknetworks[m.ref].append(network)


class PeakHandler(osmium.SimpleHandler):
    def __init__(self, writer):
        super(PeakHandler, self).__init__()
        self.writer = writer


    def node(self, n):
        if 'natural' in n.tags and n.tags['natural'] == 'peak':
            self.add_peak_node(n)
        if n.id in hknetworks:
            self.add_hike_node(n)
        self.writer.add_node(n)


    def add_hike_node(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        for network in hknetworks[n.id]:
            if network.get('ref','') == 'twn:taipei_grand_hike':
                tags['highlight'] = 'yes'
            tags['hike_node'] = network['network']

        n = n.replace(tags=tags)
        self.writer.add_node(n)


    def add_peak_node(self, n):
        tags = dict((tag.k, tag.v) for tag in n.tags)

        ref = tags.get('ref')
        name = tags.get('name')
        if ref is not None:
            if name is None or '百岳#' not in ref:
                del tags['ref']
            else:
                if '小百岳#' in ref:
                    tags['zl'] = '2'
                else:
                    if name in ['玉山', '北大武山', '雪山']:
                        tags['zl'] = '0'
                    else:
                        tags['zl'] = '1'

                tags['ref'] = '(%s)' % ref

        ele = tags.get('ele')
        if ele is not None and name is not None:
            ele = round_float(ele)
            if ele is not None:
              tags['name'] = '%s, %sm' % (name, ele)

        n = n.replace(tags=tags)
        self.writer.add_node(n)

    def way(self, w):
        if w.id not in hknetworks:
            self.writer.add_way(w)
            return

        networks = hknetworks[w.id]

        tags = dict((tag.k, tag.v) for tag in w.tags)

        for network in networks:
            if network.get('ref','') == 'twn:taipei_grand_hike':
                tags['highlight'] = 'yes'
                if not tags.get('hknetwork'):
                    tags['ref'] = network['name']
            else:
                tags['hknetwork'] = network['network']
                tags['ref'] = network['name']

        w = w.replace(tags=tags)
        self.writer.add_way(w)

    def relation(self, r):
        self.writer.add_relation(r)


def main():
    if len(sys.argv) != 3:
        print("Usage: python %s <infile> <outfile>" % sys.argv[0])
        sys.exit(-1)
    infile = sys.argv[1]
    outfile = sys.argv[2]

    HknetworkLoader().apply_file('hknetworks.osm')

    writer = osmium.SimpleWriter(outfile)
    handler = PeakHandler(writer)
    handler.apply_file(infile)
    writer.close()


if __name__ == '__main__':
    main()
