# ---------------------------------------------------------------------------
# AGOL_UpdateItemInof.py
# Created on: 1/10/2017
# Leon Scott, Town of Easton, MA

# Description: 
# Updates ArcGIS Online item information from item Ids listed in a table
# An xml file extracted from an ArcGIS geodatabase metadata is read to update item information for the feature service.  The XML file can be generate
# using the XSL Transform tool found in ArcToolbox
# An html file is used as to update the item description of the feature service.  The html file can be generated using a the XSL Transform tool 
# found in ArcToolbos with a custom XSL file 

# Command Line Example: 
# AGOL_UpdateItemInfo.py 
# Command Line Arguments
# -t table
# -d input director
#---------------------------------------------------------------------------

import arcpy
import logging
import getopt
import os
import configparser
import contextlib

from sympy import true
import codecs

import modAGOL


# Defines the entry point into the script
def main(argv=None):   
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
          opts, args = getopt.getopt(argv,"i:t:d:",['settingsfile=', 'inputtable=', 'metadatedirectory='])
        except getopt.GetoptError:
          print("Invalid option(s). Syntax: update.py -i <settingsfile>-t <inputtable> -d <metadatadirectory>")
          sys.exit(2)
    
        for o, a in opts:
            if o in ("-i", "--inputfile"):
                settingsFile = a
            elif o in ("-t", "--inputtable"):
                InputTable = a
            elif o in ("-d", "--metadatadirectory"):
                metadir = a
         
            else:
                assert False, "unhandled option"

    #get input directory and table
    if not os.path.exists(metadir): 
        print("Input directory not found. \nMake sure a valid path exists.")
        sys.exit()
     
    # Get ini settings file
    if not os.path.isfile(settingsFile): 
        print("Input file not found. \nMake sure a valid settings file exists.")
        sys.exit()

    with open(settingsFile) as fp:
        config = configparser.ConfigParser()
        config.readfp(fp)        
         
        # AGOL Credentials
        inputUsername = config.get('AGOL', 'USER')
        inputPswd = config.get('AGOL', 'PASS')
        inputURL = config.get('AGOL', 'URL')
        fp.close()
    
    # Make temp directory of thumbnail
    localPath = sys.path[0]
    tempDir = os.path.join(localPath, "tempDir")

    if not os.path.isdir(tempDir):
        os.mkdir(tempDir)

    # Search each metadata page
    fields = ['AGOL_ITEMID', 'FILENAME']
    cursor = arcpy.da.SearchCursor(InputTable, fields)
  
    for row in cursor:
        try:
           
            itemId = row[0]
            fileName = row[1]
            htmlfile = metadir + "\\" + fileName + ".html"
            xmlfile = metadir + "\\" + fileName + ".xml"

            # Get metadata files
            if os.path.isfile(htmlfile) and os.path.isfile(xmlfile): 
                #Make thumbnail path
                inthumbnail = tempDir + "/" + fileName + ".jpg"
                with contextlib.suppress(FileNotFoundError):
                    os.remove(inthumbnail)

                # Read XML file
                metadatalist =  modAGOL.metadata_to_list(xmlfile, inthumbnail)
                        

                # Get description from html file..... open at last possible time
                htmlopen = codecs.open(htmlfile, 'r', 'utf-8')  
                htmldesc = htmlopen.read()
                htmlopen.close()

                #Update item information
                modAGOL.update_featureservice(metadatalist[0], metadatalist[1], metadatalist[3], metadatalist[2], htmldesc, inthumbnail, itemId, inputURL, inputUsername, inputPswd, False,
                        False, False, "None")
                logging.info("moving on")
            else:
                logging.info("Input metadata file not found. \nMake sure a valid settings files exists.")

            logging.info("Updated from " + row[0])
        except:
            success = False
            logging.info("Update failure " + row[0])
            logging.info(arcpy.GetMessages(2))

                
    #Shutdown logging    
    logging.shutdown()    


# Script start
if __name__ == "__main__":
    main(sys.argv[1:])
