import commands
import csv
import os
import repkg_apk
import explore_activity
import shutil
import sys

emulator = sys.argv[1] # Emulator name
#emulator = '192.168.57.106:5555' # Genymotion emulator
#emulator = 'emulator-5554' # Android Studio emulator

apkPath = sys.argv[2] # APK folder
#apkPath = "/home/senchen/Desktop/xbot/apks-101/"  # Store the original app
#apkPath = "/Users/chensen/Tools/xbot/icse-mulapks/"
#apkPath = "/home/senchen/Desktop/uicrawler/apks/"  # Store the original app
#apkPath = "/home/dell/Tools/Xbot/apks-1/"

#java_home_path = '/home/dell/tools/jdk1.8.0_45'
#java_home_path = '/usr/lib/jvm/jdk1.8.0_45' # For Ubuntu
java_home_path = '/Library/Java/JavaVirtualMachines/jdk1.8.0_211.jdk/Contents/Home/' # For Macbook

#sdk_platform_path = '/home/dell/Tools/Xbot/config/libs/android-platforms/'
#sdk_platform_path = '/home/senchen/Tools/xbot/config/libs/android-platforms/' # For Ubuntu
sdk_platform_path = '/Users/chensen/Tools/xbot/config/libs/android-platforms/' # For Macbook

#lib_home_path = '/home/dell/Tools/Xbot/config/libs/'
#lib_home_path = '/home/senchen/Tools/xbot/config/libs/' # For Ubuntu
lib_home_path = '/Users/chensen/Tools/xbot/config/libs/' # For Macbook

accessbility_folder = os.path.dirname(os.path.dirname(apkPath)) # Main folder of project

config_folder = os.path.join(accessbility_folder, "config")

results_folder = os.path.join(accessbility_folder, "results")

storydroid_folder = os.path.join(accessbility_folder, "storydroid")

decompilePath = os.path.join(results_folder, "apktool")  # decompiled app path (apktool handled)

repackagedAppPath = os.path.join(results_folder, "repackaged")  # store the repackaged apps

keyPath = os.path.join(config_folder, "coolapk.keystore") # pwd: 123456, private key path

results_outputs = os.path.join(results_folder, "outputs") # project results

tmp_file = os.path.join(results_folder, emulator) # tmp file for parallel execution

def createOutputFolder():
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)

    if not os.path.exists(storydroid_folder):
        os.makedirs(storydroid_folder)

    if not os.path.exists(decompilePath):
        os.makedirs(decompilePath)

    if not os.path.exists(repackagedAppPath):
        os.makedirs(repackagedAppPath)

    if not os.path.exists(results_outputs):
        os.makedirs(results_outputs)

def execute(apk_path, apk_name):

    # Repackge app
    if not os.path.exists(os.path.join(repackagedAppPath, apk_name + '.apk')):
        r = repkg_apk.startRepkg(apk_path, apk_name, results_folder, config_folder)

        if r == 'no manifest file' or r == 'build error' or  r == 'sign error':
            print 'apk not successfully recompiled! will use the original app to execute'

    new_apkpath = os.path.join(repackagedAppPath, apk_name + '.apk')

    if os.path.exists(new_apkpath):
        #if 'Xbot' in results_folder:
            ### Xbot, note that the para is results_folder instead of accessibility_folder

        explore_activity.exploreActivity(new_apkpath, apk_name, results_folder, emulator, tmp_file, paras_path)
        # else:
        #     ### UICrawler, note that the para is results_folder instead of accessibility_folder
        #     exploreAct_uicrawler.exploreActivity(new_apkpath, apk_name, results_folder, emulator, tmp_file, paras_path)

def run_soot(apk_path, pkg): # Get bundle data for UI page rendering
    getBundle = config_folder + '/run_soot.jar'
    os.chdir(config_folder)
    print java_home_path
    os.system('java -jar %s %s %s %s %s %s %s' % (getBundle, storydroid_folder, apk_path, pkg, java_home_path, sdk_platform_path, lib_home_path))

def get_pkg(apk_path): # This version has a problem about pkg, may inconsist to the real pkg
    cmd = "aapt dump badging %s | grep 'package' | awk -v FS=\"'\" '/package: name=/{print$2}'" % apk_path
    defined_pkg_name = commands.getoutput(cmd)

    launcher = commands.getoutput(r"aapt dump badging " + apk_path + " | grep launchable-activity | awk '{print $2}'")
    if launcher.startswith(".") or defined_pkg_name in launcher or launcher == '' or launcher == '':
        return defined_pkg_name
    else:
        used_pkg_name = launcher.replace('.' + launcher.split('.')[-1], '').split('\'')[1]
        return used_pkg_name

def remove_folder(apkname, decompilePath):
    folder = os.path.join(decompilePath, apkname)
    if not os.path.exists(folder):
        return
    for f in os.listdir(folder):
        if not f == 'AndroidManifest.xml':
            rm_path = os.path.join(folder, f)
            if os.path.isdir(rm_path):
                shutil.rmtree(rm_path)
            else:
                os.remove(rm_path)

if __name__ == '__main__':

    createOutputFolder()  # Create the folders if not exists

    out_csv = os.path.join(results_folder, 'log.csv')
    if not os.path.exists(out_csv):
        csv.writer(open(out_csv, 'a')).writerow(('apk_name', 'pkg_name', 'all_act_num', 'launched_act_num',
                                                 'act_not_launched','act_num_with_issue'))

    for apk in os.listdir(apkPath): # Run the apk one by one

        if not 'apks' in apk and 'apk' in apk:

            root = 'adb -s %s root' % (emulator) # root the emulator before running
            print commands.getoutput(root)

            apk_path = os.path.join(apkPath, apk) # Get apk path

            apk_name = apk.rstrip('.apk') # Get apk name
            pkg = get_pkg(apk_path) # Get pkg, this version has a problem about pkg, may inconsist to the real pkg

            print '======= Starting ' + apk_name + ' ========='

            '''Get Bundle Data'''
            #run_soot(apk_path, pkg) # get intent parameters

            global paras_path
            paras_path = storydroid_folder + '/outputs/' + apk_name + '/activity_paras.txt'

            if not os.path.exists(storydroid_folder + '/outputs/' + apk_name):
                os.mkdir(storydroid_folder + '/outputs/' + apk_name)
            if not os.path.exists(paras_path):
                ## os.mknod(paras_path) # It is not avaiable for macbook
                open(paras_path, 'w').close()

            '''
            Core
            '''
            execute(apk_path, apk_name)

            if os.path.exists(apk_path):
                os.remove(apk_path) # Delete the apk

            if os.path.exists(os.path.join(repackagedAppPath, apk_name + '.apk')):
                os.remove(os.path.join(repackagedAppPath, apk_name + '.apk'))

            # Remove the decompiled and modified resources
            remove_folder(apk_name, decompilePath)

#execute('/home/senchen/Desktop/storydroid_plus/apks/org.liberty.android.fantastischmemo_223.apk','org.liberty.android.fantastischmemo_223',
#        '/home/senchen/Desktop/storydroid_plus/outputs/org.liberty.android.fantastischmemo_223')