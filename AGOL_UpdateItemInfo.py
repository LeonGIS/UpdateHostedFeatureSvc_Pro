# ---------------------------------------------------------------------------
# AGOL_UpdateFeatLyr_meta.py
# Created on: 1/3/2017
# Leon Scott, Town of Easton, MA

# Description: 
# Creates a standard definition file from a map inside an ArcGIS Pro project and publishes it to ArcGIS Online.
# An .ini file stores the name of the map and project file path, as well as the parameters for the service. (editing and sharing)
# An xml file extracted from an ArcGIS geodatabase metadata is read to update item information for the feature service.  The XML file can be generate
# using the XSL Transform tool found in ArcToolbox
# An html file is used as to update the item description of the feature service.  The html file can be generated using a the XSL Transform tool 
# found in ArcToolbox with a custom XSL file 

# Command Line Example: 
# AGOL_UpdateItemInfo.py -i "C:\test\settings_inputfiles.ini" -d "C:\test\RoadCenterline.html" -x "C:\test\RoadCenterline.xml"
# Command Line Arguments
# -i: settings file
# -d: html file to update item description
# -x: xml file extract from metadata
#---------------------------------------------------------------------------

import modAGOL
import logging
import os
import getopt
import sys
import configparser
import contextlib
import codecs
from sympy import true

if __name__ == "__main__":
     # Set up logging
    LOG_FILENAME = '.\AGOL_UpdateItemInfo.log'
    logging.basicConfig(level=logging.DEBUG,
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
          opts, args = getopt.getopt(argv,"i:d:x:",['inputfile=', 'descfile=', 'xmlfile='])
        except getopt.GetoptError:
          logging.info("Invalid option(s). Syntax: update.py -i <inputfile> -d <descfile>")
          sys.exit(2)
    
        for o, a in opts:
            if o in ("-i", "--inputfile"):
                settingsFile = a
            elif o in ("-d", "--descfile"):
                htmldescFile = a
            elif o in ("-x", "--xmlfile"):
                xmlMetaFile = a
            else:
                assert False, "unhandled option"
    else:
        logging.info("No options found. Syntax: update.py -i <inputfile> -d <descfile> -x <xmlfile>")
        sys.exit(2)
    logging.info("Read options")

    # Get metadata files
    if not os.path.isfile(htmldescFile) or not os.path.isfile(xmlMetaFile): 
        print("Input metadata file not found. \nMake sure a valid settings files exists.")
        sys.exit()
    logging.info("Found metadata files")

    # Get ini settings file
    if not os.path.isfile(settingsFile): 
        logging.info("Input file not found. \nMake sure a valid settings file exists.")
        sys.exit()
    logging.info("Found settings file")

    with open(settingsFile) as fp:
        config = configparser.ConfigParser()
        config.readfp(fp)        
         
        # AGOL Credentials
        inputUsername = config.get('AGOL', 'USER')
        inputPswd = config.get('AGOL', 'PASS')
        inputURL = config.get('AGOL', 'URL')

        # FS values
        serviceName = config.get('FS_INFO', 'SERVICENAME')
        serviceId = config.get('FS_INFO', 'SERVICEID')
       
    
        fp.close()
    logging.info("Read settings file")


    # create a temp directory under the script for SD & image files
    # Get current path
    localPath = sys.path[0]
    tempDir = os.path.join(localPath, "tempDir")
    if not os.path.isdir(tempDir):
        os.mkdir(tempDir)

    #Get thumbnail image from xml
    inthumbnail = tempDir + "/" + serviceName + ".jpg"
    with contextlib.suppress(FileNotFoundError):
        os.remove(inthumbnail)

    # Read XML file
    metadatalist =  modAGOL.metadata_to_list(xmlMetaFile, inthumbnail)
    logging.info("Read metadata file")
     
   # Get description from html file..... open at last possible time
    htmlopen = codecs.open(htmldescFile, 'r', 'utf-8')  
    htmldesc = htmlopen.read()
    htmlopen.close()

    #Update item information
    modAGOL.update_iteminfo(metadatalist[0], metadatalist[1], metadatalist[3], metadatalist[2], htmldesc, inthumbnail, serviceId, inputURL, inputUsername, inputPswd)
   
    logging.info("Updated feature service item information")

   