from readinglistmanager.readinglist import ReadingList

def GenerateCBLReadingList(readingLists):

                arcName = ReadingArc[0]['StoryArc']
                logger.fdebug('Generating CBL file for ' + arcName)

                # !Replace root_path variable
                readingListDest = os.path.join(mylar.CONFIG.DESTINATION_DIR, 'ReadingLists')
                filename = arcName + ".cbl"
                fullPath = os.path.join(readingListDest, filename)

                if not os.path.exists(readingListDest):
                    logger.fdebug('making directory: %s' % readingListDest)
                    filechecker.validateAndCreateDirectory(readingListDest, True)

                logger.fdebug('Opening file: ' + fullPath)

