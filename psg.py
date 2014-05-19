__author__ = 'Gor'
import requests as r, time

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
        temp = {}
        data = r.get('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000&offset=%s'%(owner_id,post_id, offset)).json()['response']
        while len(data['items'])>0:
            for node in data['items']:
                try: temp[node['from_id']]=[owner_id, node['id'], node['reposts']['count']]
                except:
                    if 'reposts' not in node: temp[node['from_id']]=[owner_id, node['id'], 0]
                    else: raise KeyError
            offset +=len(data['items'])
            try: data = r.get('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=2&offset=%s'%(owner_id,post_id, offset)).json()['response']
            except r.ConnectionError:
                time.sleep(3)
                data = r.get('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=2&offset=%s'%(owner_id,post_id, offset)).json()['response']
        temp_reposts = {}
        for i in temp:
            if temp[i][2]>0: temp_reposts[i]=temp[i]
        if len(temp_reposts) == 0:
            for i in temp: self.tree[i]=temp[i]
        else:
            print('Node %s has %s subnodes with reposts'%(owner_id, len(temp_reposts)))
            for i in temp_reposts:
                if i not in self.tree: self.collect_tree_data(i, temp_reposts[i][1], 0)
        for i in temp:
            if i not in self.tree:
                self.tree[i]=temp[i]
    #Create graph file (.gml) for Gephi
    def create_gml(self, owner_id, post_id):
        edges = self.tree
        nodes = list(edges.keys())
        nodes.extend(list(set([i[0] for i in edges.values()])))
        file = open('%s_%s.gml'%(owner_id, post_id), 'w')
        file.write('graph\n[\n\tdirected 1')
        for n in set(nodes):
            if n<0: t='group'
            else: t='user'
            file.write('\n\tnode\n\t[\n\t\tid "%s"\n\t\tlabel "%s"\t\n\t\ttype "%s"\t]'%(n,n,t))
        for edge in edges:
            file.write('\n\tedge\n\t[\n\t\tsource "%s"\n'%edges[edge][0])
            file.write('\t\ttarget "%s"\t]'%edge)
        file.write('\n]')
        file.close()
