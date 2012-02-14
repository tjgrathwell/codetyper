# python.exe setup.py py2exe
 
from distutils.core import setup
import py2exe, os
 
opts = { 
 "py2exe": { 
   # if you import .py files from subfolders of your project, then those are
   # submodules.  You'll want to declare those in the "includes"
   'includes':[],
 } 
} 
 
def filesinpath(path, ext):
  return [os.path.abspath(os.path.join(path,file)) for file in os.listdir(path) if file.endswith(ext)]
 
setup(
 windows = [
    {
    "script": "main.py",
    "icon_resources": [(1, "codetyper.ico")]
    }],
 
  #this is the file that is run when you start the game from the command line.  
  console=['main.py'],
 
  #options as defined above
  options=opts,

 
  #data files - these are the non-python files, like images and sounds
  data_files = [(os.path.join('.', 'snippets'), filesinpath(os.path.join('.', 'snippets'),".snp")),
                (os.path.join('.'), filesinpath('.',"codetyper.ico"))],
 
  #this will pack up a zipfile instead of having a glut of files sitting
  #in a folder.
  zipfile="lib/shared.zip"
)

os.rename('dist/main.exe','dist/codetyper.exe')
