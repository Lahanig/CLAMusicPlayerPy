import os, time, platform, shutil
if platform.system() == "Windows":
    print('Compiling project for windows:')
    time.sleep(1)
    os.system('pyinstaller --distpath ./bin -F player.py')
else:
    print('Compiling project for linux:')
    time.sleep(1)
    os.system('python3 -m PyInstaller --distpath ./bin -F player.py')

if os.path.exists(os.path.dirname(os.path.realpath(__file__)) + '/dist/') == True:
    shutil.rmtree(os.path.dirname(os.path.realpath(__file__)) + '/dist/')