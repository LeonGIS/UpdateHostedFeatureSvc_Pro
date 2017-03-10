import arcpy
from arcgis.gis import GIS
import logging
import os
import getopt
import sys
import configparser
import contextlib


if __name__ == "__main__":
      # Set up logging
    LOG_FILENAME = '.\AGOL_UpdateFeatLyr.log'
    logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename=LOG_FILENAME,
                    filemode='w')
    logging.info("**************************")
    logging.info("")

    # Read command line options
    argv = sys.argv[1:]
    if argv:
        try:
          opts, args = getopt.getopt(argv,"i:",['inputfile='])
        except getopt.GetoptError:
          logging.info("Invalid option(s). Syntax: update.py -i <inputfile>")
          sys.exit(2)
    
        for o, a in opts:
            if o in ("-i", "--inputfile"):
                settingsFile = a
            else:
                assert False, "unhandled option"

    else:
        logging.info("No options found. Syntax: update.py -i <inputfile>")
        sys.exit(2)

    # Get ini settings file
    if not os.path.isfile(settingsFile): 
        logging.info("Input file not found. \nMake sure a valid settings file exists.")
        sys.exit()

    
    with open(settingsFile) as fp:
        config = configparser.ConfigParser()
        config.readfp(fp)        
         
        # AGOL Credentials
        inputUsername = config.get('AGOL', 'USER')
        inputPswd = config.get('AGOL', 'PASS')
        inputURL = config.get('AGOL', 'URL')

        # FS values
        APRX_FILE = config.get('FS_INFO', 'APRX')
        MAP_NAME = config.get('FS_INFO', 'MAPNAME')
        serviceName = config.get('FS_INFO', 'SERVICENAME')
        folderName = config.get('FS_INFO', 'FOLDERNAME')
        inediting = config.get('FS_INFO', 'EDITING')
        inexport = config.get('FS_INFO', 'EXPORT')
        inthumbnail = config.get('FS_INFO', 'THUMBNAIL')

        insummary = config.get('FS_INFO', 'SUMMARY')
        intags = config.get('FS_INFO', 'TAGS')
        indescription = config.get('FS_INFO', 'DESCRIPTION')
        incredits = config.get('FS_INFO', 'CREDITS')
        inuselimit = config.get('FS_INFO', 'USELIMITS')

        # Convert boolean inputs from string
        blnediting = True
        if inediting == "false":
            blnediting = False
   
        blnexport = True
        if inexport == "false":
            blnexport = False

        # Share FS to: everyone, org, groups
        shared = config.get('FS_SHARE', 'SHARE')
        shareeveryone = config.get('FS_SHARE', 'EVERYONE')
        shareorgs = config.get('FS_SHARE', 'ORG')
        sharegroups = config.get('FS_SHARE', 'GROUPS')  # Groups are by ID. Multiple groups comma separated
        if sharegroups is None:
            sharegroups = ''
        fp.close()

    #get ArcPro project & map
    if not os.path.isfile(APRX_FILE): 
        logging.info("ArcGIS project file not found. \nMake sure a valid file exists.")
        sys.exit()
    aprx = arcpy.mp.ArcGISProject(APRX_FILE)
    
    maplist = aprx.listMaps(MAP_NAME)
    if not maplist:
        logging.info("Map not found in ArcGIS project file. \nMake sure a valid map exists.")
        sys.exit()           
    m = maplist[0]
   
    # Get current path
    localPath = sys.path[0]

    # create a temp directory under the script
    tempDir = os.path.join(localPath, "tempDir")
    if not os.path.isdir(tempDir):
        os.mkdir(tempDir)
    draftSD = os.path.join(tempDir, serviceName + ".sddraft")
    finalSD = os.path.join(tempDir, serviceName + ".sd")

    # delete existing sd file
    with contextlib.suppress(FileNotFoundError):
        os.remove(finalSD)

    # create sd file   
    arcpy.mp.CreateWebLayerSDDraft(m, draftSD, serviceName, 'MY_HOSTED_SERVICES', 'FEATURE_ACCESS', folderName, enable_editing = blnediting, allow_exporting = blnexport, summary=insummary, tags = intags, description = indescription, credits = incredits, use_limitations = inuselimit)
    arcpy.StageService_server(draftSD, finalSD)
  
    # add sd file to AGOL
    gis = GIS(inputURL, inputUsername, inputPswd)

    #Find SD file, then update or add, then publish
    sd_items = gis.content.search("title:'" + serviceName +"' AND owner:" + inputUsername, item_type="Service Definition")
    item_properties = {"snippet": insummary,
                       "description": indescription,
                       "accessInformation": incredits,
                       "licenseInfo": inuselimit,
                       "tags": intags
        }
   
    if sd_items:
        sd_item = sd_items[0]
        updatesuccess = sd_item.update({},finalSD)
        if updatesuccess:
            sd_item.publish(overwrite="true")           
    else:    
        new_sd_item = gis.content.add({}, finalSD)
        new_sd_item.publish(overwrite="true")
       
    #Find new feature service and set sharing
    fs_items = gis.content.search("title:'" + serviceName +"' AND owner:" + inputUsername, item_type="Feature Service")
    if fs_items:
        fs_item = fs_items[0]
        if os.path.isfile(inthumbnail):
            fs_item.update(item_properties, thumbnail = inthumbnail)
        else:
             fs_item.update(item_properties)
        if shared:
            fs_item.share(everyone = shareeveryone, org = shareorgs, groups = sharegroups)
  