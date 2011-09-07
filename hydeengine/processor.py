import sys
import logging
import fnmatch
from media_processors import TemplateProcessor

def load_processor(name):
    (module_name, _ , processor) = name.rpartition(".")
    __import__(module_name)
    module = sys.modules[module_name]
    return getattr(module, processor)

class Processor(object):
    def __init__(self, settings):
        self.settings = settings 
        self.processor_cache = {}
        self._logger = None
        
    @property
    def logger(self):
        if self._logger:
            return self._logger
            
        if hasattr(self.settings, "logger"):
            return self.settings.logger
            
        loglevel = logging.INFO    
        if hasattr(self.settings, "LOG_LEVEL"):
            loglevel = self.settings.LOG_LEVEL
            
        logger = logging.getLogger("hyde_processor")
        logger.setLevel(loglevel)
        ch = logging.StreamHandler()
        ch.setLevel(loglevel)
        formatter = logging.Formatter("%(levelname)s:%(message)s[%(asctime)s]")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        self._logger = logger
        return logger
        
    def get_node_processors(self, node):
        if node.fragment in self.processor_cache:
            return self.processor_cache[node.fragment]
        
        processors = {}
        if node.type == "media":
            processors = self.settings.MEDIA_PROCESSORS
        elif node.type == "content":
            processors = self.settings.CONTENT_PROCESSORS
        else:
            return []
        return self.extract_processors(node, processors, self.processor_cache)

        
    def extract_processors(self, node, processors, cache):
        current_processors = []
        this_node = node
        while this_node:
            fragment = this_node.fragment          
            self.logger.debug("Getting processors for: %s" % fragment) 
            if fragment in processors:
                current_processors.append(processors[fragment])
            this_node = this_node.parent
        # Add the default processors to the list
        if "*" in processors:
            current_processors.append(processors["*"])
        cache[node.fragment] = current_processors
        current_processors.reverse()
        return current_processors

    def remove(self, item):
        if hasattr(item, "resources"):
            self.logger.info("Removing Node %s" % item.url)
            item.target_folder.delete()
            item.temp_folder.delete()
        else:
            self.logger.info("Removing Resource %s" % item.url)
            item.target_file.delete()
            item.temp_file.delete()
        
    def process(self, resource):
        if (resource.node.type not in ("content", "media") or
            resource.is_layout):
            self.logger.debug("Skipping resource: %s" % str(resource.file))
            return False
        self.logger.info("Processing %s" % resource.url)
        processor_config = self.get_node_processors(resource.node)
        processors = []
        for processer_map in processor_config:
            if resource.file.extension in processer_map:
                processors.extend(processer_map[resource.file.extension])
            else:
                self.logger.debug("Extension %s" % resource.file.extension)                    
                #
                # Wildcard matching: 
                # This should be the default matcher going forward
                # The above branch needs to be kept around until everyone
                # has had the chance to upgrade their settings file.
                #
                for wildcard, processor_list in processer_map.iteritems():
                    self.logger.debug(wildcard)                    
                    if fnmatch.fnmatch(resource.file.name, wildcard):
                        processors.extend(processor_list)                        
                    
        resource.temp_file.parent.make()        
        resource.source_file.copy_to(resource.temp_file)  
        (original_source, resource.source_file) = (
                               resource.source_file, resource.temp_file)
        for processor_name in processors:
            processor = load_processor(processor_name)
            self.logger.debug("       Executing %s" % processor_name)
            processor.process(resource)
        
        if resource.node.type == "content" and not resource.prerendered:
            self.settings.CONTEXT['page'] = resource
            self.logger.debug("       Rendering Page")
            TemplateProcessor.process(resource)
            self.settings.CONTEXT['page'] = None
            
        resource.source_file = original_source
        self.logger.debug("        Processing Complete")
        return True

    def pre_process(self, node):
        self.logger.info("Pre processing %s" % str(node.folder))
        self.__around_process__(node, self.settings.SITE_PRE_PROCESSORS)
          
    def post_process(self, node):
        self.logger.info("Post processing %s" % str(node.folder))
        self.__around_process__(node, self.settings.SITE_POST_PROCESSORS)
       
    def __around_process__(self, node, processors):
        for child in node.walk():
            if not child.type in ("content", "media"):
                continue
            fragment = child.temp_folder.get_fragment(node.site.temp_folder)
            if sys.platform == 'win32':
                fragment = fragment.rstrip("\\")
            else:
                fragment = fragment.rstrip("/")
            if not fragment:
                if sys.platform == 'win32':
                    fragment = "\\"
                else:
                    fragment = "/"
            if fragment in processors:           
                processor_config = processors[fragment]
                for processor_name, params in processor_config.iteritems():
                    self.logger.debug("           Executing %s" % processor_name)
                    processor = load_processor(processor_name) 
                    if not params:
                        params = {}
                    params.update( {'node': child})
                    processor.process(child.temp_folder, params)

