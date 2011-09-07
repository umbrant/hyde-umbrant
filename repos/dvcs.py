import sys

class DVCS(object):
    def __init__(self, path, repo):
        self.path = path
        self.url = repo['url']
        self.type = repo['type']        
        self.draft_branch = repo['draft_branch']
        self.prod_branch = repo['production_branch'] 
        self.switch(self.draft_branch)                 

    def save_draft(self, message=None): abstract
    def publish(self): abstract
    def pull(self): abstract
    def push(self, branch): abstract
    def commit(self, message): abstract
    def switch(self, branch): abstract
    def add_file(self, path, message=None): abstract    
    def merge(self, branch): abstract
            
    @staticmethod     
    def load_dvcs(path, repo):
       (module_name, _ , class_name) = repo['type'].rpartition(".")
       __import__(module_name)
       module = sys.modules[module_name]
       repo_class = getattr(module, class_name)     
       return repo_class(path, repo)

        