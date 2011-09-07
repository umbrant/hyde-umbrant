function getHydeSet(saveFunction){
    return {	
    	markupSet:  [ 	
    		{
    		    name:'Save', 
    		    key:'S', 
    		    className:'saveButton',
    		    beforeInsert: function(button){
    		        saveFunction();
    		    }
    		 },
    	]
    } 
}
