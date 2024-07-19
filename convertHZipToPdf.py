import os 
import sys
import time

import argparse

import zipfile

from pathlib import Path
import shutil
from PIL import Image


class ImageZipToPdfConverter:
     #class variable
     inputDirectoryPath=""
     outputDirectoryPath=""
     debugLoggingOn=False
     verboseInfoLoggingOn=True
     
     #class constants
     TMP_DIR_NAME="tmp"
     SUPPORTED_IMAGE_FILE_TYPES = [".png",".jpg",".jpeg"]
     
     
     def __init__(self,inputDirectory,outputDirectory,debugLogging,verboseLogging) -> None:
          self.inputDirectoryPath = inputDirectory
          self.outputDirectoryPath = outputDirectory
          self.debugLoggingOn=debugLogging
          self.verboseInfoLoggingOn=verboseLogging
          
          self._validateIODirectories()

     def _logAppInfo(self,logMessage,newLineAtStart=False,newLineAtEnd=False,isVerbose=False):
          if isVerbose is False or self.verboseInfoLoggingOn is True:
               newLineAtStart= "\n" if newLineAtStart else ""
               newLineAtEnd= "\n" if newLineAtEnd else ""
               verboseStr = " Verbose" if isVerbose else ""
               print(newLineAtStart+"[APP INFO{}] ".format(verboseStr) + logMessage + newLineAtEnd)
          
     def _logAppError(self,logMessage,newLineAtStart=False,newLineAtEnd=False):
          newLineAtStart= "\n" if newLineAtStart else ""
          newLineAtEnd= "\n" if newLineAtEnd else ""
          print(newLineAtStart+"[APP ERROR] " + logMessage + newLineAtEnd)

     def _logAppDebug(self,logMessage,newLineAtStart=False,newLineAtEnd=False):
          if self.debugLoggingOn:
               newLineAtStart= "\n" if newLineAtStart else ""
               newLineAtEnd= "\n" if newLineAtEnd else ""
               print(newLineAtStart+"[APP DEBUG] " + logMessage + newLineAtEnd)
               
     def _validateIODirectories(self):
          if os.path.exists(self.inputDirectoryPath):
               self._logAppInfo("Input directory path exists: "+ self.inputDirectoryPath)
          else:
               self._logAppInfo("Input directory path does not exist: " + self.inputDirectoryPath)
               absoluteInputPath = os.path.abspath(self.inputDirectoryPath)
               if os.path.exists(absoluteInputPath):
                    self._logAppInfo("Absolute output directory does exist: " + absoluteInputPath)
                    self.inputDirectoryPath=absoluteInputPath #update w/ absolute path
               else:
                    self._logAppError("Bad input directory. Stopping app.")
                    sys.exit()
          
          if os.path.exists(self.outputDirectoryPath):
               self._logAppInfo("Output directory exists: " + self.outputDirectoryPath)
          else:
               self._logAppInfo("Output directory does not exist: " + self.outputDirectoryPath)
               absoluteOutputPath = os.path.abspath(self.outputDirectoryPath)
               if os.path.exists(absoluteOutputPath):
                    self._logAppInfo("Absolute output directory does exist: " + absoluteOutputPath)
                    self.outputDirectoryPath=absoluteOutputPath #update w/ absolute path
               else: #try creating path
                    self._logAppInfo("Attempting to create directory: " + self.outputDirectoryPath)
                    Path(self.outputDirectoryPath).mkdir(parents=True)


     def processAllImageZipFiles(self):
          self._logAppInfo("Starting image zip file processing...",newLineAtStart=True)
          self.listInputDirectoryFiles()
          
          zipFilePaths = self.getListOfImageZipFiles()
          absoluteZipFilePaths = self.getAbsoluteFilePathsForFiles(zipFilePaths)
          
          self.convertImageZipFilesToPdfs(absoluteZipFilePaths)
          
          self._logAppInfo("Finished image zip file processing.",newLineAtStart=True)

     def listInputDirectoryFiles(self):
          assert os.path.exists(self.inputDirectoryPath)
          onlyFiles = [
               file for file in
               os.listdir(self.inputDirectoryPath) 
               if os.path.isfile(os.path.join(self.inputDirectoryPath,file))
          ]
          
          self._logAppDebug("Listing files in directory [" +  self.inputDirectoryPath+ "] :",newLineAtStart=True)
          for file in onlyFiles: 
               self._logAppDebug("File: "+ file)
          self._logAppInfo("Found " + str(len(onlyFiles)) + " files in input directory")
               
     def getListOfImageZipFiles(self):
          assert os.path.exists(self.inputDirectoryPath)
          onlyZipFiles = [
               file for file in
               os.listdir(self.inputDirectoryPath) 
               if os.path.isfile(os.path.join(self.inputDirectoryPath,file))
               and ".zip" in file
          ]
          
          self._logAppInfo("Listing zip files in directory [" +  self.inputDirectoryPath+ "] :",newLineAtStart=True,isVerbose=True)
          for file in onlyZipFiles: 
               self._logAppInfo("File: "+ file,isVerbose=True)
          self._logAppInfo("Found " + str(len(onlyZipFiles)) + " zip files")
          return onlyZipFiles


     def getListOfTempDirectoryImageFiles(self,tmpZipFilePath):
          tempPath=self.getTempDirectoryPath()
          assert os.path.exists(tempPath)
          
          unzippedImagesDir= os.path.join(tempPath,Path(tmpZipFilePath).stem)
          
          onlyImageFiles = [
               os.path.join(unzippedImagesDir,file)
               for file in os.listdir(unzippedImagesDir) 
               if os.path.isfile(os.path.join(unzippedImagesDir,file))
               and any(extension in file for extension in self.SUPPORTED_IMAGE_FILE_TYPES)
          ]
          
          onlyImageFiles.sort()
          
          self._logAppInfo("Listing image files in directory, {} :".format(unzippedImagesDir), newLineAtStart=True, isVerbose=True)
          for file in onlyImageFiles: 
               self._logAppInfo("Image: "+ file,isVerbose=True)
          self._logAppInfo("Found " + str(len(onlyImageFiles)) + " image files")
          return onlyImageFiles


     def getAbsoluteFilePathsForFiles(self, filesList):
          
          absoluteFilePaths = [
               os.path.abspath( os.path.join(self.inputDirectoryPath, file)) 
               for file in filesList 
          ]
          self._logAppInfo("Listing absolute file paths for zip files: ",newLineAtStart=True)
          for file in absoluteFilePaths: 
               self._logAppInfo("File path: "+ file)
          return absoluteFilePaths


     def convertImageZipFilesToPdfs(self, imageZipFileList):
          self._logAppInfo("Starting image zip file conversion...",newLineAtEnd=True)
          failureList = []
          
          for index, zipFilePath in enumerate(imageZipFileList):
               self._logAppInfo("File #{} : Starting processing of {}".format(index+1,zipFilePath))
               try:
                    self.cleanTemporaryDir()
                    
                    pdfAlreadyExists = self.doesPDfExistInOutputDir(zipFilePath)
                    if pdfAlreadyExists is True:
                         self._logAppInfo(
                              "File #{} : PDf already created here: {}.\n Skipping to next file.".format(
                                   index+1,self.getPDFFilePathForInputZipFile(zipFilePath)
                              ),
                              newLineAtEnd=True
                         )
                         continue
                    
                    tmpZipFilePath = self.copyImageZipFileToTempDirectory(zipFilePath)
                    self.unzipImagesZipToDirectory(tmpZipFilePath)
                    
                    imageFiles = self.getListOfTempDirectoryImageFiles(tmpZipFilePath)
                    
                    newPdfPath = self.getPDFFilePathForInputZipFile(zipFilePath)
                    self.createPdfFromImages(newPdfPath,imageFiles)
                    
                    newPdfCreated = self.doesPDfExistInOutputDir(zipFilePath)
                    if newPdfCreated is not True:
                         self._logAppError("File #{} : PDf already created. Skipping to next file.".format(index+1,zipFilePath),newLineAtEnd=True)
                         continue
                    else:
                         self._logAppInfo("PDf succesfully created.",newLineAtEnd=True)
          
                    #input("\ncontinue?")
                    #time.sleep(1)
                    
                    self._logAppInfo("File #{} : Finished Processing of {}".format(index+1,zipFilePath),newLineAtEnd=True)
                    
               except:
                    self._logAppError("File #{} : Failed processing of {}. Attempting next file.".format(index+1,zipFilePath))
                    failureList.append(zipFilePath)                        
          
          self._logAppInfo("Completed all file conversions.",newLineAtStart=True,newLineAtEnd=True)
          self.reportFailures(failureList)
          self.deleteTemporaryDir()


     def doesPDfExistInOutputDir(self,inputZipFilePath):
          expectedPDFPath = self.getPDFFilePathForInputZipFile(inputZipFilePath)
          exists = os.path.exists(expectedPDFPath)
          if exists:
               self._logAppInfo("PDf exists for zipfile, {} , @ {}".format(inputZipFilePath,expectedPDFPath))
          else:
               self._logAppInfo("PDf does not exist for zipfile, {} , @ {}".format(inputZipFilePath,expectedPDFPath))
          
          return exists

     def getPDFFilePathForInputZipFile(self,inputZipFilePath):
          zipFileNameNoExtension = Path(inputZipFilePath).stem
          expectedPDFPath = os.path.join(self.outputDirectoryPath, zipFileNameNoExtension + ".pdf")
          return expectedPDFPath

     def getTempDirectoryPath(self):
          return os.path.join(self.outputDirectoryPath, self.TMP_DIR_NAME)

     def createTemporaryDir(self):
          tempDirectory = self.getTempDirectoryPath()
          Path(tempDirectory).mkdir(parents=True,exist_ok=True)
          os.chmod(tempDirectory,0o777)
          self._logAppInfo("Created temporary directory @ {}".format(tempDirectory),newLineAtEnd=True)

     def deleteTemporaryDir(self):
          tempDirectory = self.getTempDirectoryPath()
          if os.path.exists(tempDirectory):
               try:
                    shutil.rmtree(tempDirectory,onerror=self.handleTempDirectoryError)
                    self._logAppInfo("Deleted temporary directory.",newLineAtEnd=True)
               except Exception:
                    self._logAppError("Failed to delete the temporary directory @ {}".format(tempDirectory))
                    self._logAppError("Shutting down app...",newLineAtStart=True)
                    

     def cleanTemporaryDir(self):
          self.deleteTemporaryDir()
          self.createTemporaryDir()

     def handleTempDirectoryError(func,path,exceptionInfo):
          print("{} exception thrown when deleting {}".format(exceptionInfo,path))
          
     
     def copyImageZipFileToTempDirectory(self, imageZipFilePath):
          self._logAppInfo("Attempting to copy {} file to {}".format(imageZipFilePath,self.getTempDirectoryPath()))
          tmpFilePath = os.path.join(self.getTempDirectoryPath(),Path(imageZipFilePath).name)
          shutil.copyfile( imageZipFilePath , tmpFilePath)
          self._logAppInfo("Copied file to {}".format(tmpFilePath))
          return tmpFilePath

     def unzipImagesZipToDirectory(self,zipFilePath):
          with zipfile.ZipFile(zipFilePath, 'r') as zip_ref:
               zip_ref.extractall(self.getTempDirectoryPath())

               
     def createPdfFromImages(self,newPdfPath,imageFilePathsList):
          self._logAppInfo("Creating {} file from images.".format(newPdfPath),newLineAtStart=True,newLineAtEnd=True)
          
          images = [Image.open(imageFilePath) for imageFilePath in imageFilePathsList]
          images[0].save(
               newPdfPath,
               "PDF",
               resolution=100.0,
               save_all=True,
               append_images=images[1:]
          )
          
     def reportFailures(self, listOfFailedFiles):
          if not listOfFailedFiles:
               pass #if empty, skip
          else:
               self._logAppError("List of files that could not be processed:",newLineAtStart=True)
               self._logAppError(', '.join(listOfFailedFiles),newLineAtEnd=True)

          
          
def setupCommandLineArguments():
     desc = "Application for converting zip archives that contain image files into PDF files."
     parser = argparse.ArgumentParser(description=desc)
     
     parser.add_argument("inputDir", help="Input directory that contains image zip archive files")
     parser.add_argument("outputDir", help="Output directory to store generated PDF files.")
     
     parser.add_argument("-d","--debug", help="Show debug logging", action='store_true')
     parser.add_argument("-v","--verbose", help="Show verbose info logging", action='store_true')
     
     return parser.parse_args()


if __name__ == "__main__":
     #run normal script here     
     args = setupCommandLineArguments()
     
     print("Running " +os.path.basename( __file__))
     print("Required Arguments: input dir={}, output dir={}".format(args.inputDir,args.outputDir))
     print("Optional Arguments: debug logging={}, verbose logging={}".format(args.debug,args.verbose))
     
     newConverter = ImageZipToPdfConverter(args.inputDir,args.outputDir,args.debug,args.verbose)
     newConverter.processAllImageZipFiles()