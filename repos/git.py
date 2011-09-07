from dvcs import DVCS
from subprocess import Popen, PIPE

class Git(DVCS):
  
    def save_draft(self, message=None): 
        self.commit(message or "Saved via clyde.")
        self.push(self.draft_branch)
     
    def add_file(self, path, message=None):
         cmd = Popen('git add "%s"' % path, 
                        cwd=self.path, stdout=PIPE, shell=True)    
         cmdresult = cmd.communicate()[0]
         if cmd.returncode:
            raise Exception(cmdresult)   
            
         self.commit(message or "Added file %s" % path)   
         self.push(self.draft_branch)
            
    def publish(self):
        self.switch(self.prod_branch) 
        self.merge(self.draft_branch)
        self.push(self.prod_branch)
        self.switch(self.draft_branch)         
    
    def pull(self):                            
        self.switch(self.draft_branch)                   
        cmd = Popen("git pull", cwd=self.path, stdout=PIPE, shell=True)    
        cmdresult = cmd.communicate()[0]
        if cmd.returncode:
            raise Exception(cmdresult)
    
    def push(self, branch): 
        cmd = Popen("git push origin %s" % branch, cwd=self.path, stdout=PIPE, shell=True)    
        cmdresult = cmd.communicate()[0]
        if cmd.returncode:
            raise Exception(cmdresult)                                                       
    
    
    def commit(self, message): 
        cmd = Popen('git commit -a -m"%s"' % message, 
                    cwd=self.path, stdout=PIPE, shell=True)    
        cmdresult = cmd.communicate()[0]
        if cmd.returncode:
            raise Exception(cmdresult)

    def switch(self, branch): 
        cmd = Popen('git checkout %s' % branch, 
                    cwd=self.path, stdout=PIPE, shell=True)    
        cmdresult = cmd.communicate()[0]
        if cmd.returncode:
            raise Exception(cmdresult)
    
    def merge(self, branch): 
        cmd = Popen('git merge %s' % branch, 
                    cwd=self.path, stdout=PIPE, shell=True)    
        cmdresult = cmd.communicate()[0]
        if cmd.returncode:
            raise Exception(cmdresult)