import requests as r, time
class sharing_tree:
    def __init__(self, inpt, accuracy=95):
        owner_id, post_id = inpt
        self.tree = {}
        self.closed_groups = 0
        self.accuracy = accuracy
        if accuracy>100:
            print("Accuracy must be not bigger than 100%. Default accuracy (95%) will be used.")
            self.accuracy = 95
        owner_id, post_id = self.find_first_creator(owner_id, post_id)
        if owner_id and post_id:
            #try:
                try: self.target = self.connector('https://api.vk.com/method/wall.getById?posts=%s_%s'%(owner_id,post_id)).json()['response'][0]['reposts']['count']
                except: self.target = self.connector('https://api.vk.com/method/wall.getById?posts=%s_%s'%(owner_id,post_id)).json()['response'][0]['reposts']['count']
                self.collect_tree_data(owner_id, post_id)
                self.create_gml(owner_id, post_id)
            #except: pass

    def all_reposts(self,owner_id,post_id):
        offset, attempts, temp= 0, 0, {}
        try: target = self.connector('https://api.vk.com/method/wall.getById?posts=%s_%s'%(owner_id,post_id)).json()['response'][0]['reposts']['count']
        except: target = self.connector('https://api.vk.com/method/wall.getById?posts=%s_%s'%(owner_id,post_id)).json()['response'][0]['reposts']['count']
        while len(temp)/target*100 < self.accuracy and attempts < 10:
            try: data = self.connector('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000&offset=%s'%(owner_id,post_id, offset)).json()['response']
            except: data = self.connector('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000&offset=%s'%(owner_id,post_id, offset)).json()['response']
            while len(data['items'])>0:
                for node in data['items']:
                    try: temp[node['from_id']]=[owner_id, node['id'], node['reposts']['count']]
                    except:
                        if 'reposts' not in node:
                            temp[node['from_id']]=[owner_id, node['id'], 0]
                            self.closed_groups +=1
                        else: raise KeyError
                offset +=len(data['items'])
                try: data = self.connector('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=2&offset=%s'%(owner_id,post_id, offset)).json()['response']
                except: data = self.connector('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=2&offset=%s'%(owner_id,post_id, offset)).json()['response']
            attempts += 1
            offset = 0
            print('Current accuracy for node %s is %s%%, attempt: %s'%(owner_id, round(len(temp)/target*100, 0), attempts))
        return temp
    #Lookinf for the starting post
    def find_first_creator(self, owner_id, post_id):
        try:
            try: data = self.connector('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000'%(owner_id,post_id)).json()['response']['items'][0]
            except: data = self.connector('https://api.vk.com/method/wall.getReposts?owner_id=%s&post_id=%s&count=1000'%(owner_id,post_id)).json()['response']['items'][0]
            if 'copy_owner_id' not in data: return owner_id, post_id
            elif data['copy_owner_id']==owner_id and data['copy_post_id']==post_id: return owner_id, post_id
            else: return self.find_first_creator(data['copy_owner_id'], data['copy_post_id'])
        except:
            print('Must be at least 1 repost from current OWNER_ID=%s and POST_ID=%s'%(owner_id, post_id))
            return [None, None]
    #Handling connection problems
    def connector(self, url):
        while True:
            try: return r.get(url)
            except r.ConnectionError:
                print('Some connection errors, waiting 3 sec...')
                time.sleep(3)
    #Collect data about repost directions
    def collect_tree_data(self, owner_id, post_id):
        temp = self.all_reposts(owner_id, post_id)
        temp_reposts = {}
        for i in temp:
            if temp[i][2]>0: temp_reposts[i]=temp[i]
        if len(temp_reposts) == 0:
            for i in temp: self.tree[i]=temp[i]
        else:
            print('Node %s has %s subnodes with reposts (%s in total)'%(owner_id, len(temp_reposts), len(temp)))
            [self.collect_tree_data(i, temp_reposts[i][1]) for i in temp_reposts if i not in self.tree]
        for i in temp:
            if i not in self.tree: self.tree[i]=temp[i]
    #Create graph file (.gml) for Gephi
    def create_gml(self, owner_id, post_id):
        nodes = list(self.tree.keys())
        nodes.extend(list(set([i[0] for i in self.tree.values()])))
        file = open('%s_%s_(%sclosed_%s%%accuracy).gml'%(owner_id, post_id, self.closed_groups, round((self.target+1)/len(nodes)*100, 0)), 'w')
        file.write('graph\n[\n\tdirected 1')
        for n in set(nodes):
            if n<0: t='group'
            else: t='user'
            file.write('\n\tnode\n\t[\n\t\tid "%s"\n\t\tlabel "%s"\t\n\t\ttype "%s"\t]'%(n,n,t))
        for edge in self.tree:
            file.write('\n\tedge\n\t[\n\t\tsource "%s"\n'%self.tree[edge][0])
            file.write('\t\ttarget "%s"\t]'%edge)
        file.write('\n]')
        file.close()
