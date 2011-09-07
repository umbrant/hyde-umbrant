"""
1. Can build a sitemap from a folder
    1.1 Number of nodes  
    1.2 Number of pages in each node  
    1.3 Node Attributes
        1.3.1 Url
        1.3.2 Full Url
        1.3.3 Source Folder
        1.3.4 Temp Folder
        1.3.5 Target Folder
        1.3.6 Listing Page
    1.4 Page Attributes
        1.4.1 Title
        1.4.2 Created
        1.4.3 Updated
        1.4.4 Listing
        1.4.5 Source File
        1.4.6 Temp File
        1.4.6 Target File
        1.4.7 Url
        1.4.8 Full Url
        1.4.9 Absolute modification time
    1.5 Media
        1.5.1 Media Source Path
        1.5.2 Media Temp Path
        1.5.3 Media Target Path
        1.5.4 Media Absolute modification time
        
2. Can Persist sitemap for future use
    2.1 Save reload and equality
    
3. Change Identification
    3.1 Identify changes in media
    3.2 Identify changes in content and layout
    
Notes:

1. Full Regeneration:
    1.1 Layout changes
    1.2 "_"(incude) file changes
    1.3 Folder move / renames
2. Excerpts => Regenerated when dependent page changes
3  Listing Files => When there are pages added / removed, or when dependent changes
4. Three threads for monitoring:
    4.1 Content
    4.2 Media
    4.3 Layout
5. Two threads for regeneration:
    5.1 Content
    5.2 Media
6. 

"""