#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Batch Image Modifier by JDHatten
    This script will modify one or more images changing various aspects based on selected options in coded presets.
    Currently some of those options include width, height, image format… more to come.

Usage:
    Simply drag and drop one or more image files or directories onto the script.
    Script can be opened directly but only one image file or directory may be dropped/added at once.

Requirements:
    skimage https://scikit-image.org/
    python -m pip install -U scikit-image

TODO:
    [] Upscale or Downscale only options
    [] Extra Options when saving images, i.e. jpeg quality slider, png transparency, etc.
    [] Choose where to save new image files.
    [] 
    
'''


import imghdr
import matplotlib.pyplot as plt
import os
from pathlib import Path, PurePath
from skimage import io
from skimage.transform import resize #, downscale_local_mean, rescale
import sys

os.system('mode con: cols=128 lines=64')
MIN_VERSION = (3,8,0)
MIN_VERSION_STR = '.'.join([str(n) for n in MIN_VERSION])

SHOW_ALL = 9999
NONE = -1

HEIGHT = 0
WIDTH = 1

# Preset Options
CHANGE_HEIGHT = 0
CHANGE_WIDTH = 1
KEEP_ASPECT_RATIO = 2
CHANGE_IMAGE_FORMAT = 3
IMAGE_FORMAT_OPTIONS = 4
OVERWRITE_IMAGE_FILE = 5
ADD_TO_FILENAME = 6
SAVE_FILE_FOLDER = 7

SEARCH_SUB_DIRS = 10

# Preset Modifiers
NO_CHANGE = 0
CHANGE_TO = 1
ADD = 2
SUBTRACT = 3
MULTIPLY = 4
DIVIDE = 5
UPSCALE = 6
DOWNSCALE = 7

SAME_DIR = 10

BMP = '.bmp'  # Windows bitmaps: *.bmp
EXR = '.exr'  # OpenEXR Image files: *.exr
HDR = '.hdr'  # Radiance HDR: *.hdr, *.pic
JPG = '.jpg'  # JPEG files: *.jpeg, *.jpg, *.jpe
JP2 = '.jp2'  # JPEG 2000 files: *.jp2
PBM = '.pbm'  # Portable image format: *.pbm, *.pgm, *.ppm *.pxm, *.pnm
PFM = '.pfm'  # PFM files: *.pfm
PNG = '.png'  # Portable Network Graphics: *.png
RAS = '.ras'  # Sun rasters: *.ras, *.sun, *.sr
TIF = '.tif'  # TIFF files: *.tiff, *.tif
WEB = '.webp' # WebP: *.webp

QUALITY = 0
OPTIMIZE = 1
PROGRESSIVE = 2
TRANSPARENCY = 3


### After initial drop and file renaming, ask for additional files or just quit the script.
loop = True

### Present Options - Used to skip questions and immediately start modifing all drop images.
### Make sure to select the correct preset (select_preset)
use_preset = True
select_preset = 3

preset0 = { #         : Defualts
  'HEIGHT'            : (NO_CHANGE),        # (Modify with, Number)
  'WIDTH'             : (NO_CHANGE),        # 0 = NO_CHANGE
  'KEEP_ASPECT_RATIO' : True,               # If Only One Size Changed
  'CHANGE_FORMAT'     : NO_CHANGE,          # Image Format
  'OVERWRITE_IMAGE'   : False,              # If Not CHANGE_FORMAT
  'ADD_TO_FILENAME'   : '_new',             # If OVERWRITE False
  'SEARCH_SUB_DIRS'   : False               # If Directory Dropped
}
preset1 = {
  'HEIGHT'            : (CHANGE_TO,1080),
  'WIDTH'             : NO_CHANGE,
  'KEEP_ASPECT_RATIO' : True,
  'CHANGE_FORMAT'     : NO_CHANGE,
  'OVERWRITE_IMAGE'   : False,
  'ADD_TO_FILENAME'   : '_[Modified]',
  'SEARCH_SUB_DIRS'   : False
}
preset2 = {
  'HEIGHT'            : 0,
  'WIDTH'             : (MULTIPLY,4),
  'KEEP_ASPECT_RATIO' : True,
  'CHANGE_FORMAT'     : PNG
}
preset3 = {
  'CHANGE_FORMAT'     : JPG,
  'OVERWRITE_IMAGE'   : False,
  'ADD_TO_FILENAME'   : '_[Modified]',
  'SEARCH_SUB_DIRS'   : False
}
preset4 = {
  'HEIGHT'            : (SUBTRACT,2034),
  'WIDTH'             : 0,
  'KEEP_ASPECT_RATIO' : True,
  'CHANGE_FORMAT'     : PNG
}
preset5 = {
  CHANGE_HEIGHT         : (DOWNSCALE, 1080),
  CHANGE_WIDTH          : NO_CHANGE,
  KEEP_ASPECT_RATIO     : True,
  CHANGE_IMAGE_FORMAT   : JPG,
  IMAGE_FORMAT_OPTIONS  : ((QUALITY,100),(OPTIMIZE,True),(PROGRESSIVE,True)),
  OVERWRITE_IMAGE_FILE  : False,
  ADD_TO_FILENAME       : '_[Modified]',
  SAVE_FILE_FOLDER      : SAME_DIR
}
preset_options = [preset0,preset1,preset2,preset3,preset4,preset5]
preset = preset_options[select_preset] # Pick which preset to use [#].


### 
###     () 
###     --> Returns a [] 
#def ():
#    return 0


### Display the image file modifications option in a preset.
###     (preset) A Dictonary with image file modifications to be made.
###     --> Returns a [0] 
def displayPreset(presets, number = -1):
    if number == -1:
        for ps in presets:
            number+=1
            print('\nPreset %s {' % str(number))
            for option, mod in ps.items():
                mod_str = getModifySizeText(mod)
                print('  %s : %s' % (option, mod_str))
            print('}')
    else:
        print('\nPreset %s {' % str(number))
        for option, mod in presets[number].items():
            mod_str = getModifySizeText(mod)
            print('  %s : %s' % (option, mod_str))
        print('}')
    return 0


### Get readable text from preset modifications.
###     (mod) The modification in a preset
###     --> Returns a [String] 
def getModifySizeText(mod):
    if type(mod) is tuple:
        if mod[0] == NO_CHANGE:
            text = 'No Change'
        elif mod[0] == CHANGE_TO:
            text = 'Change To '
        elif mod[0] == ADD:
            text = 'Add '
        elif mod[0] == SUBTRACT:
            text = 'Subtract '
        elif mod[0] == MULTIPLY:
            text = 'Multiply By '
        elif mod[0] == DIVIDE:
            text = 'Divide By '
        if len(mod) > 1:
            text += str(mod[1])
    elif mod == NO_CHANGE:
        text = 'No Change'
    else:
        text = str(mod)
    return text


### Iterate over all files in a directory for the purpose of modifing image files that........ matches the edit conditions.
###     (some_dir) The full path to a directory. Str("path\to\file")
###     (edit_details) All the dtials on how to proceed with the edits. List[EDIT_TYPE, ADD_TEXT, PLACEMENT, MATCH_TEXT, REPLACE_TEXT, RECURSIVE, SEARCH_FROM]
###     (include_sub_dirs) Search sub-directories for more files.  bool(True) or bool(False)
###     --> Returns a [Integer] Number of files renamed.
def modifyAllImagesInDirectory(some_dir, edit_details, include_sub_dirs = False):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir) # Error if not directory or doen't exist
    
    images_modified = 0
    for root, dirs, files in os.walk(some_dir):
    
        print('\n-Root: %s' % (root))
        
        #for dir in dirs:
            #print('--Directory: [ %s ]' % (dir))
            
        for file in files:
            #print('--File: [ %s ]' % (file))
            file_path = Path(PurePath().joinpath(root,file))
            image_modified = False
            
            if edit_details[EDIT_TYPE] == REPLACE:
                image_modified = modifyImage(file_path, edit_details)
            
            if image_modified:
                    images_modified+=1
            
        if not include_sub_dirs:
            break
    
    return images_modified


### Modify and save an image.
###     (file_path) The full path to an image file. Str("path\to\file")
###     (edit_details) 
###     --> Returns a [Boolean] 
def modifyImage(file_path, edit_details):
    image_modified = False
    image_path = Path(file_path)
    assert Path.is_file(image_path) # Error if not a file or doen't exist
    
    image_type = imghdr.what(image_path) # Is this an 'image' file?
    if image_type != None:
        org_image = io.imread(image_path)
    else:
        return image_modified
    
    height_mod = edit_details.get('HEIGHT',(0))
    width_mod = edit_details.get('WIDTH',(0))
    keep_aspect_ratio = edit_details.get('KEEP_ASPECT_RATIO',True)
    if edit_details.get('CHANGE_FORMAT',0) != NO_CHANGE:
        extension = edit_details['CHANGE_FORMAT']
        image_modified = True
    else:
        extension = image_path.suffix
    overwrite = edit_details.get('OVERWRITE_IMAGE',False)
    if not overwrite:
        new_file_name = image_path.stem + edit_details.get('ADD_TO_FILENAME','_new')
    else:
        new_file_name = image_path.stem
    
    new_image_shape = modifyImageSize(org_image.shape, (height_mod, width_mod), keep_aspect_ratio)
    
    if org_image.shape != new_image_shape:
        image_resized = resize(org_image, new_image_shape, anti_aliasing=True)
        image_modified = True
    
    if image_modified:
        new_image_path = PurePath().joinpath(image_path.parent, new_file_name+extension)
        # jpg: 
        if extension == JPG:
            io.imsave(str(new_image_path), image_resized, quality=100, optimize=True, progressive=True)
        else:
            io.imsave(str(new_image_path), image_resized)
    
    return image_modified


### Modify the size/shape of an image.
###     (org_image_shape) The height and width of the orginal image.
###     (image_size_modifications) How to modify the height and width of the orginal image. Tuple( Height: Tuple( Modifier, Number ), Width: Tuple( Modifier, Number ) )
###     (keep_aspect_ratio) True or False
###     --> Returns a [Tuple] (Height, Width)
def modifyImageSize(org_image_shape, image_size_modifications, keep_aspect_ratio = True):
    
    # Height
    if type(image_size_modifications[HEIGHT]) is tuple:
        
        
        if image_size_modifications[HEIGHT][0] == NO_CHANGE:
            new_height = org_image_shape[HEIGHT]
            
        if image_size_modifications[HEIGHT][0] == CHANGE_TO:
            new_height = image_size_modifications[HEIGHT][1]
        
        if image_size_modifications[HEIGHT][0] == ADD:
            new_height = org_image_shape[HEIGHT] + image_size_modifications[HEIGHT][1]
        
        if image_size_modifications[HEIGHT][0] == SUBTRACT:
            new_height = org_image_shape[HEIGHT] - image_size_modifications[HEIGHT][1]
            new_height = new_height if new_height >= 1 else 1
        
        if image_size_modifications[HEIGHT][0] == MULTIPLY:
            new_height = org_image_shape[HEIGHT] * image_size_modifications[HEIGHT][1]
        
        if image_size_modifications[HEIGHT][0] == DIVIDE:
            new_height = org_image_shape[HEIGHT] / image_size_modifications[HEIGHT][1]
        
    elif image_size_modifications[HEIGHT] != NO_CHANGE:
        
        new_height = image_size_modifications[HEIGHT]
        
    else:
        new_height = org_image_shape[HEIGHT]
    
    # Width
    if type(image_size_modifications[WIDTH]) is tuple:
        
        if image_size_modifications[WIDTH][0] == NO_CHANGE:
            new_width = org_image_shape[WIDTH]
        
        if image_size_modifications[WIDTH][0] == CHANGE_TO:
            new_width = image_size_modifications[WIDTH][1]
        
        if image_size_modifications[WIDTH][0] == ADD:
            new_width = org_image_shape[WIDTH] + image_size_modifications[WIDTH][1]
        
        if image_size_modifications[WIDTH][0] == SUBTRACT:
            new_width = org_image_shape[WIDTH] - image_size_modifications[WIDTH][1]
            new_width = new_width if new_width >= 1 else 1
        
        if image_size_modifications[WIDTH][0] == MULTIPLY:
            new_width = org_image_shape[WIDTH] * image_size_modifications[WIDTH][1]
        
        if image_size_modifications[WIDTH][0] == DIVIDE:
            new_width = org_image_shape[WIDTH] / image_size_modifications[WIDTH][1]
        
    elif image_size_modifications[WIDTH] != NO_CHANGE:
        
        new_width = image_size_modifications[WIDTH]
        
    else:
        new_width = org_image_shape[WIDTH]
    
    # Keeping Aspect Ratio
    if image_size_modifications[HEIGHT] == NO_CHANGE and image_size_modifications[WIDTH] != NO_CHANGE and keep_aspect_ratio:
        factor_h = org_image_shape[HEIGHT] / org_image_shape[WIDTH]
        new_height = org_image_shape[HEIGHT] - (org_image_shape[WIDTH] - new_width) * factor_h
    
    elif image_size_modifications[WIDTH] == NO_CHANGE and image_size_modifications[HEIGHT] != NO_CHANGE and keep_aspect_ratio:
        factor_w = org_image_shape[WIDTH] / org_image_shape[HEIGHT]
        new_width = org_image_shape[WIDTH] - (org_image_shape[HEIGHT] - new_height) * factor_w
        
    new_height = round(new_height)
    new_width = round(new_width)
    print('Height: [%s]  --  Width: [%s]' % (new_height, new_width))
    
    return (new_height, new_width)



### Change strings into an integers.
###     (string) The string to change into an integer.
###     --> Returns a [Integer]
def strNumberToInt(string):
    string = string.lower()
    
    if string == 'showall' or string == 'sa' or string == 'a' or string == 'all':
        number = SHOW_ALL
    
    elif string.find('show') > -1:
        number = string.partition('show')[2]
        number = strNumberToInt(str(int(number)+1000))
    
    elif string.isnumeric():
        number = int(string)
    
    else:
        number = NONE
    
    return number


### Drop one of more files and directories here to be renamed after answering a series of questions regarding how to properly rename said files.
###     (files) A [List] of files, which can include directories pointing to many more files.
###     --> Returns a [Integer] Number of files renamed.
def drop(files):
    
    # If script is ran on it's own then ask for an image file.
    if len(files) == 0:
        dropped_file = input('No image files or directories found, drop one here now to proceed: ')
        dropped_file = findReplace(dropped_file,'"','',ALL,LEFT,False)[0] # Remove the auto quotes
        
        if os.path.exists(dropped_file):
            files.append(dropped_file)
        else:
            print('\nNo Image Files or Directories Dropped')
            return 0
    
    elif not os.path.exists(files[0]):
        print('\nNo Image Files or Directories Dropped')
        return 0
    
    images_modified = 0
    
    try:
        # Check if at least one file or directory was dropped
        dropped_file = files[0]
        print('Number of Files or Directories Dropped: [ %s ]' % len(files))
        
        if use_preset:
            edit_details = preset
            
        else:
            preset_selection = NONE
            while preset_selection == NONE:
                
                print('\nNo Preset Option Selected, Select One Now. [ # ] ')
                preset_selection = input('Or Type [ Show# ] or [ ShowAll ] To Display Presets: ')
                preset_selection = strNumberToInt(preset_selection)
                #print('preset_selection: %s' % str(preset_selection))
                
                if preset_selection == SHOW_ALL:
                    #print(preset_options)
                    displayPreset(preset_options)
                    preset_selection = NONE
                    
                elif preset_selection > 999:
                    preset_selection -= 1000
                    if preset_selection < len(preset_options):
                        #print(preset_options[preset_selection])
                        displayPreset(preset_options, preset_selection)
                    preset_selection = NONE
                    
                elif preset_selection < len(preset_options) and preset_selection > NONE:
                    edit_details = preset_options[preset_selection]
                    print('Preset [ #%s ] Selected' % preset_selection)
                
                else:
                    preset_selection = NONE
        
        # Iterate over all dropped files including all files in dropped directories
        include_sub_dirs = -1
        for file_path in files:
            
            if os.path.isdir(file_path):
                
                if include_sub_dirs == -1 and not use_preset: # Only answer once
                    include_sub_dirs = input('Search through sub-directories too? [ Y / N ]: ')
                    include_sub_dirs = yesTrue(include_sub_dirs)
                else:
                    include_sub_dirs = preset[SUB_DIRS]
                
                images_modified = modifyAllImagesInDirectory(file_path, edit_details, include_sub_dirs)
            
            elif os.path.isfile(file_path):
                print('\n')
                
                is_image_modified = modifyImage(file_path, edit_details)
                    
                if is_image_modified:
                    images_modified+=1
            
            else:
                print("\nThis is not a normal file of directory (socket, FIFO, device file, etc.)." )
                
    except IndexError:
        print('\nNo Files or Directories Dropped')
    
    return images_modified


### Script Starts Here
if __name__ == '__main__':
    
    print(sys.version)
    print('\n================================')
    print('Batch Image Modifier by JDHatten')
    print('================================\n')
    assert sys.version_info >= MIN_VERSION, f"This Script Requires Python v{MIN_VERSION_STR} or Newer"
    
    # Testing: Simulating File Drops
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    #sys.argv.append(os.path.join(ROOT_DIR,'images\\01.jpg'))
    #sys.argv.append(os.path.join(ROOT_DIR,'images\\text.txt'))
    #sys.argv.append(os.path.join(ROOT_DIR,'images'))
    
    
    '''from PIL import Image
    pil_image = Image.open(file_path)
    print(pil_image)'''
    
    '''fig, axes = plt.subplots(nrows=2, ncols=2)

    ax = axes.ravel()

    ax[0].imshow(image_resized, cmap='gray')
    ax[0].set_title("Resized image (no aliasing)")
    
    ax[0].set_xlim(0, 512)
    ax[0].set_ylim(512, 0)
    plt.tight_layout()
    plt.show()'''
    
    #plt.imshow(image_resized)
    #plt.show()
    
    #print(io.available_plugins)
    
    
    images_modified = drop(sys.argv[1:])
    print('\nNumber of files renamed: [ %s ]' % (images_modified))
    
    if loop:
        newFile = 'startloop'
        prev_images_modified = 0
        while newFile != '':
            newFile = input('\nDrop another file or directory here to go again or press enter to quit: ')
            #newFile = newFile.replace('"','')
            newFile = findReplace(newFile,'"','',ALL,LEFT,False)[0] # Remove the auto quotes around file paths with spaces.
            images_modified += drop([newFile])
            if images_modified > prev_images_modified:
                print('\nNumber of all files renamed so far: [ %s ]' % (images_modified))
                prev_images_modified = images_modified
    
