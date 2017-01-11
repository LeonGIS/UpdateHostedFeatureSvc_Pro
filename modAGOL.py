import arcpy
from arcgis.gis import GIS
import xml.etree.ElementTree as ET
import base64
import os

def metadata_to_list(metadatafile, thumbpath):
    insummary = ""
    incredits = ""
    intags = ""
    inuselimit = ""

    #Get metadata from xml file
    xmlparser = ET.XMLParser(encoding="UTF-8")
    tree = ET.parse(metadatafile, parser=xmlparser)
    root = tree.getroot()
    dataIdInfo = root.find('dataIdInfo')
    metasummary = dataIdInfo.find('idPurp')
    insummary = metasummary.text
     
    metacredits = dataIdInfo.find('idCredit')
    incredits = metacredits.text
    
    # Create tags
    intags = ''
    metaTags = dataIdInfo.find('searchKeys')
    for keyword in metaTags.findall('keyword'):
        if intags == '':
            intags = keyword.text
        else:
            intags = intags + "," + keyword.text
    
    inuselimit = ''
    # Create constraints from Use and then Legal
    for resconst in dataIdInfo.findall('resConst'):
        for const in resconst.findall('Consts'):
            UseConst = const.find('useLimit')
            if inuselimit == '':
                inuselimit = UseConst.text
            else:
                inuselimit = inuselimit + "\n" + UseConst.text

    for resconst in dataIdInfo.findall('resConst'):
        for const in resconst.findall('LegConsts'):
            LegalConst = const.find('othConsts')
            if inuselimit == '':
                inuselimit = LegalConst.text
            else:
                inuselimit = inuselimit + "\n" + LegalConst.text
     
    if inuselimit == '':
        inuselimit = 'There are not access and use constraints for this item.'  
    
   

    thumbdata = root.findall("Binary/Thumbnail/Data")
    if thumbdata:
        metathumbnail = thumbdata[0].text
        with open(thumbpath,"wb") as f:
            f.write(base64.b64decode(metathumbnail))

    
        
                   
    metadatalist = [insummary,incredits,intags,inuselimit]
    return metadatalist

def update_featureservice(itemsummary, itemcredits, itemuselimits, itemtags, itemdesc, itemthumb_file, itemid, agol_url, agol_user, agol_pass, shared, share_everyone, share_org, share_groups):
    item_properties = {"snippet": itemsummary,
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




def createSD_and_overwrite(aprx_file, map_name, draft_sd, service_name, folder_name, edit_enabled, export_enabled, 
                           itemsummary, itemtags, itemcredits, itemuselimits, final_sd, agol_url, agol_user, agol_pass, sd_itemid ):
    aprx = arcpy.mp.ArcGISProject(aprx_file)
    
    maplist = aprx.listMaps(map_name)
    if not maplist:
        print("Map not found in ArcGIS project file. \nMake sure a valid map exists.")
        sys.exit()           
    m = maplist[0]

    # create sd file   
    arcpy.mp.CreateWebLayerSDDraft(m, draft_sd, service_name, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', folder_name, enable_editing = edit_enabled, allow_exporting = export_enabled, summary=itemsummary, tags = itemtags, credits = itemcredits, use_limitations = itemuselimits)
    arcpy.StageService_server(draft_sd, final_sd)

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
    else:    
        print("SD item not found. \nMake sure a sd file exists.")
        sys.exit() 
 
