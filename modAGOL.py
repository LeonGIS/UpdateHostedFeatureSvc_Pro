# ---------------------------------------------------------------------------
# modAGOL.py
# Created on: 1/11/2017
# Leon Scott, Town of Easton, MA

# Description: 
# Shared functions related to publishing and updating items in ArcGIS Online
#---------------------------------------------------------------------------

import arcpy
from arcgis.gis import GIS
import xml.etree.ElementTree as ET
import base64
import os
import logging



# Function: metadata_to_list
# Description: Read metadata XML extracted from ArcCatalog
def metadata_to_list(metadatafile, thumbpath):
    insummary = ""
    incredits = ""
    #intags = ""
   # inuselimit = ""
    intitle = ""

    logging.info("Start metadata_to_list") 

    #Get metadata from xml file
    xmlparser = ET.XMLParser(encoding="UTF-8")
    tree = ET.parse(metadatafile, parser=xmlparser)
    root = tree.getroot()
    dataIdInfo = root.find('dataIdInfo')

    #Get name of dataset
    try:
        metacitation = dataIdInfo.find('idCitation')
        metatitle = metacitation.find('resTitle')
        intitle = metatitle.text
    except:
        metatitle = 'There is not title for this item.'
        logging.info("Metadata missing title")   
         
    logging.info("Metadata - Title")  

    try:
        metasummary = dataIdInfo.find('idPurp')
        insummary = metasummary.text
    except:
        metasummary = 'There is no summary for this item.' 
        logging.info("Metadata missing purpose")     
    
    logging.info("Metadata - Purpose")  
    
    try:
        metacredits = dataIdInfo.find('idCredit')
        incredits = metacredits.text
    except:
        metacredits = 'There is not credit information for this item.' 
        logging.info("Metadata missing purpose")    
        
    logging.info("Metadata - credits") 

    # Create tags
    intags = ''
    try:
        metaTags = dataIdInfo.find('searchKeys')
        for keyword in metaTags.findall('keyword'):
            if intags == '':
                intags = keyword.text
            else:
                intags = intags + "," + keyword.text
    except:
        logging.info("Metadata missing tags") 
    logging.info("Metadata - tags") 

    inuselimit = ''
    # Create constraints from Use and then Legal
    try:
        for resconst in dataIdInfo.findall('resConst'):
            for const in resconst.findall('Consts'):
                UseConst = const.find('useLimit')
                if inuselimit == '':
                    inuselimit = UseConst.text
                else:
                    inuselimit = inuselimit + "\n" + UseConst.text
    except:
        logging.info("Metadata missing use limits") 

    try:
        for resconst in dataIdInfo.findall('resConst'):
            for const in resconst.findall('LegConsts'):
                LegalConst = const.find('othConsts')
                if inuselimit == '':
                    inuselimit = LegalConst.text
                else:
                    inuselimit = inuselimit + "\n" + LegalConst.text
    except:
        logging.info("Metadata missing legal constraints") 
         
    if inuselimit == '':
        inuselimit = 'There are not access and use constraints for this item.'  
    
    logging.info("Metadata - use limits") 

    thumbdata = root.findall("Binary/Thumbnail/Data")
    if thumbdata:
        metathumbnail = thumbdata[0].text
        with open(thumbpath,"wb") as f:
            f.write(base64.b64decode(metathumbnail))

    logging.info("Metadata - thumbnail") 
        
                   
    metadatalist = [intitle, insummary,incredits,intags,inuselimit]
    return metadatalist


# Function: update_featureservice
# Description: Update feature service item information and sharing
def update_featureservice(itemtitle, itemsummary, itemcredits, itemuselimits, itemtags, itemdesc, itemthumb_file, itemid, agol_url, agol_user, agol_pass, shared, share_everyone, share_org, share_groups):
    item_properties = {"title": itemtitle,
                        "snippet": itemsummary,
                       "description": itemdesc,
                       "accessInformation": itemcredits,
                       "licenseInfo": itemuselimits,
                       "tags": itemtags
    }   

    gis = GIS(agol_url, agol_user, agol_pass)
    fs_items = gis.content.search("id:" + itemid + " AND owner:" + agol_user, item_type="Feature Service")
    if fs_items:
        fs_item = fs_items[0]
        if os.path.isfile(itemthumb_file):
            fs_item.update(item_properties, thumbnail = itemthumb_file)
        else:
            fs_item.update(item_properties)
        if shared:
            fs_item.share(everyone = share_everyone, org = share_org, groups = share_groups)

# Function: update_iteminfo
# Description: Update feature service item information
def update_iteminfo(itemsummary, itemcredits, itemuselimits, itemtags, itemdesc, itemthumb_file, itemid, agol_url, agol_user, agol_pass):
    item_properties = {"snippet": itemsummary,
                       "description": itemdesc,
                       "accessInformation": itemcredits,
                       "licenseInfo": itemuselimits,
                       "tags": itemtags
    }   

    gis = GIS(agol_url, agol_user, agol_pass)
    fs_items = gis.content.search("id:" + itemid, item_type="Feature Service")
    if fs_items:
        fs_item = fs_items[0]
        if os.path.isfile(itemthumb_file):
            fs_item.update(item_properties, thumbnail = itemthumb_file)
        else:
            fs_item.update(item_properties)

# Function: createSD_and_overwrite
# Description: Creates a SD file from ArcGIS Pro, then updates an existing SD file in ArcGIS Online.  The new SD file is published.
def createSD_and_overwrite(aprx_file, map_name, draft_sd, service_name, folder_name, edit_enabled, export_enabled, 
                           itemsummary, itemtags, itemcredits, itemuselimits, final_sd, agol_url, agol_user, agol_pass, sd_itemid ):
    logging.info("Start createSD_and_overwrite") 
    aprx = arcpy.mp.ArcGISProject(aprx_file)
    
    maplist = aprx.listMaps(map_name)
    if not maplist:
        logging.info("Map not found in ArcGIS project file. \nMake sure a valid map exists.")
        sys.exit()             
    m = maplist[0]
    logging.info("Map found")

    # create sd file
    try:
        logging.info("SDDraft: " + draft_sd)
        logging.info("Service: " + service_name)
        logging.info("AGOL folder: " + folder_name)
        arcpy.mp.CreateWebLayerSDDraft(m, draft_sd, service_name, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', folder_name, enable_editing = edit_enabled, allow_exporting = export_enabled, summary=itemsummary, tags = itemtags, credits = itemcredits, use_limitations = itemuselimits)
        logging.info("Created draft sd")
        arcpy.StageService_server(draft_sd, final_sd)
        logging.info("Staged service") 
    except:
        logging.info(arcpy.GetMessages())
        sys.exit()

    #Push sd file to AGOL
    gis = GIS(agol_url, agol_user, agol_pass)
   
    #Find SD file, then update or add, then publish
    sd_items = gis.content.search("id:" + sd_itemid +" AND owner:" + agol_user, item_type="Service Definition")

    #Parameters for editor tracking
    pub_params = {"editorTrackingInfo" : {"enableEditorTracking":'true',  "preserveEditUsersAndTimestamps":'true'}}

    if sd_items:
        sd_item = sd_items[0]
        updatesuccess = sd_item.update({},final_sd)
        if updatesuccess:
            sd_item.publish(publish_parameters=pub_params, overwrite="true")
            logging.info("SD file published")           
    else:    
        logging.info("SD item not found. \nMake sure a sd file exists.")
        sys.exit() 
 
def createSDfile(aprx_file, map_name, draft_sd, service_name, folder_name, edit_enabled, export_enabled, 
                           itemsummary, itemtags, itemcredits, itemuselimits, final_sd):
    logging.info("Start createSD_and_overwrite") 
    aprx = arcpy.mp.ArcGISProject(aprx_file)
    
    maplist = aprx.listMaps(map_name)
    if not maplist:
        logging.info("Map not found in ArcGIS project file. \nMake sure a valid map exists.")
        sys.exit()             
    m = maplist[0]
    logging.info("Map found")

    # create sd file
    try:
        logging.info("SDDraft: " + draft_sd)
        logging.info("Service: " + service_name)
        logging.info("AGOL folder: " + folder_name)
        arcpy.mp.CreateWebLayerSDDraft(m, draft_sd, service_name, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', folder_name, enable_editing = edit_enabled, allow_exporting = export_enabled, summary=itemsummary, tags = itemtags, credits = itemcredits, use_limitations = itemuselimits)
        logging.info("Created draft sd")
        arcpy.StageService_server(draft_sd, final_sd)
        logging.info("Staged service") 
    except:
        logging.info(arcpy.GetMessages())
        sys.exit()