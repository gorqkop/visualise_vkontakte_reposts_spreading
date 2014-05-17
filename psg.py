__author__ = 'Gor'
import requests as r

class sharing_tree:
    def __init__(self, owner_id, post_id):
        self.tree = {}
        owner_id, post_id = self.find_first_creator(owner_id, post_id)
        if owner_id is not None and post_id is not None:
            self.collect_tree_data(owner_id, post_id, 0)
            self.create_gml(owner_id, post_id)
    #Lookinf for the starting post
    def find_first_creator(self, owner_id, post_id):
        try:
            data = r.get('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000'%(owner_id,post_id)).json()['response']['items'][0]
            if 'copy_owner_id' not in data: return owner_id, post_id
            elif data['copy_owner_id']==owner_id and data['copy_post_id']==post_id: return owner_id, post_id
            else: return self.find_first_creator(data['copy_owner_id'], data['copy_post_id'])
        except:
            print('Must be at least 1 repost from current OWNER_ID=%s and POST_ID=%s'%(owner_id, post_id))
            return [None, None]
    #Collect data about repost directions
    def collect_tree_data(self, owner_id, post_id, offset):
        data = r.get('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000&offset=%s'%(owner_id,post_id, offset)).json()['response']
        while len(data['items'])>0:
            for node in data['items']:
                if node['from_id'] not in self.tree:
                    self.collect_tree_data(node['from_id'], node['id'], 0)
                    self.tree[node['from_id']]=[owner_id, node['id']]
                    #self.collect_tree_data(node['from_id'], node['id'], 0)
            offset +=len(data['items'])
            print(offset)
            data = r.get('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=2&offset=%s'%(owner_id,post_id, offset)).json()['response']
    #Create graph file (.gml) for Gephi
    def create_gml(self, owner_id, post_id):
        edges = self.tree
        nodes = list(edges.keys())
        nodes.extend(list(set([i[0] for i in edges.values()])))
        file = open('%s_%s.gml'%(owner_id, post_id), 'w')
        file.write('graph\n[\n\tdirected 1')
        for n in set(nodes):
            file.write('\n\tnode\n\t[\n\t\tid "%s"\n\t\tlabel "%s"\t]'%(n,n))
        for edge in edges:
            file.write('\n\tedge\n\t[\n\t\tsource "%s"\n'%edges[edge][0])
            file.write('\t\ttarget "%s"\t]'%edge)
        file.write('\n]')
        file.close()
