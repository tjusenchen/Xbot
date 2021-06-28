'''
Authors: Sen Chen and Lingling Fan
input: an apk
output: a repackaged apk
'''

import os
import shutil
import commands

#keyPath = os.path.join(os.path.split(os.path.realpath(__file__))[0], "coolapk.keystore")  # pwd: 123456, private key path
keyPath = ''

def decompile(eachappPath, decompileAPKPath):
    print "decompiling..."
    cmd = "apktool d {0} -f -o {1}".format(eachappPath, decompileAPKPath)
    os.system(cmd)

def modifyManifestAgain(line_num, decompileAPKPath):
    # in order to fix an error
    ManifestPath = os.path.join(decompileAPKPath, "AndroidManifest.xml")
    lines = open(ManifestPath,'r').readlines()
    if '@android' in lines[line_num-1]:
        #lines[line_num-1].replace('@android','@*android')
        lines[line_num-1] = lines[line_num-1].split('@android')[0] + '@*android' + lines[line_num-1].split('@android')[1]
    open(ManifestPath,'w').writelines(lines)

def recompile(decompileAPKPath):

    cmd = "apktool b {0}".format(decompileAPKPath)

    #W: /xxx/AndroidManifest.xml:156: error: Error: Resource is not public. (at 'enabled' with value '@android:bool/config_tether_upstream_automatic').
    output = commands.getoutput(cmd)

    return output


def sign_apk(apk_name, decompileAPKPath, repackagedAppPath):
    repackName = apk_name + ".apk"
    resign_appName = apk_name + "_sign" + ".apk"
    #optiName = repackapp + "_z" + ".apk"
    repackAppPath = os.path.join(decompileAPKPath + '/dist', repackName)
    sign_apk = os.path.join(repackagedAppPath, resign_appName)

    #optappPath = os.path.join(run.decompilePath, repackapp, "dist", optiName)
    #cmd = "zipalign -v 4 {0} {1}".format(repackAppPath, optappPath)
    #os.system(cmd)

    read, write = os.pipe()
    os.write(write, '123456')
    os.close(write)

    print keyPath, sign_apk, repackAppPath

    cmd = "jarsigner -verbose -keystore {0} -signedjar {1} {2} {3}".format(keyPath, sign_apk, repackAppPath, "coolapk")
    cmd1 = "echo '123456\r'|{0} ".format(cmd)

    #returncode = \
    os.system(cmd1)
    #return returncode

def rename(apkname, repackagedAppPath):

    oldNamePath = os.path.join(repackagedAppPath, apkname + '_sign.apk')
    newNamePath = os.path.join(repackagedAppPath, apkname+'.apk')
    os.rename(oldNamePath,newNamePath)

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

def addExportedTrue(line):
    if 'exported="true"' in line:
        return line
    if 'exported="false"' in line:
        return line.replace('exported="false"', 'exported="true"')
    if not 'exported' in line:
        return '<activity exported="true" ' + line.split('<activity ')[1]

def modifyManifest_00(decompileAPKPath):
    newlines = []
    ManifestPath = os.path.join(decompileAPKPath, "AndroidManifest.xml")

    if not os.path.exists(ManifestPath):
        return "NoManifest"
    else:
        flag = 0
        for line in open(ManifestPath,'r').readlines():
            if line.strip().startswith('<activity '):
                line = addExportedTrue(line)
                newlines.append(line)
            else:
                newlines.append(line)
        open(ManifestPath,'wb').writelines(newlines)

def startRepkg(apk_path, apkname, results_folder, config_folder):
    global keyPath
    keyPath = os.path.join(config_folder, "coolapk.keystore")

    noManifestAppPath = os.path.join(results_folder, "no-manifest-apks")
    buildErrorAppPath = os.path.join(results_folder, "build-error-apks")
    signErrorAppPath = os.path.join(results_folder, "sign-error-apks")
    decompilePath = os.path.join(results_folder, "apktool")  # decompiled app path (apktool handled)
    repackagedAppPath = os.path.join(results_folder, "repackaged")  # store the repackaged apps

    if not os.path.exists(noManifestAppPath):
        os.makedirs(noManifestAppPath)

    if not os.path.exists(buildErrorAppPath):
        os.makedirs(buildErrorAppPath)

    if not os.path.exists(signErrorAppPath):
        os.makedirs(signErrorAppPath)

    if not os.path.exists(decompilePath):
        os.makedirs(decompilePath)

    if not os.path.exists(repackagedAppPath):
        os.makedirs(repackagedAppPath)

    decompileAPKPath = os.path.join(decompilePath, apkname)

    # Decomplie original apk
    decompile(apk_path, decompileAPKPath)

    # Modify Manifest
    msg = modifyManifest_00(decompileAPKPath)

    if msg == "NoManifest":
        # Copy original app to repackage folder
        copy_org_apk = "mv %s %s"%(apk_path, repackagedAppPath)
        commands.getoutput(copy_org_apk)

        # Copy original app to no-manifest-apks
        copy_org_apk = "mv %s %s"%(apk_path, noManifestAppPath)
        commands.getoutput(copy_org_apk)
        return 'no manifest file'

    # Recompile modified apk
    recompileInfo = recompile(decompileAPKPath)
    print "recompiling..."

    builtApk = False
    for line in recompileInfo.split('\n'):
        if "Error: Resource is not public." in line:
            line_num = int(line.split('AndroidManifest.xml:')[1].split(': error')[0])
            modifyManifestAgain(line_num, decompileAPKPath)
            recompileInfo = recompile(decompileAPKPath)
            break
        if "Built apk..." in line:
            builtApk = True
            print "Successfully recompile an apk!!!"

    if not builtApk:
        # Copy original app to repackage folder
        copy_org_apk = "mv %s %s"%(apk_path, repackagedAppPath)
        commands.getoutput(copy_org_apk)

        # Copy original app to build-error-apks
        copy_org_apk = "mv %s %s"%(apk_path, buildErrorAppPath)
        commands.getoutput(copy_org_apk)

        return 'build error'

    print "signing..."
    # Sign the modified apk
    sign_apk(apkname, decompileAPKPath, repackagedAppPath)

    # if not msg == "0":
    #     # Copy original app to repackage folder
    #     copy_org_apk = "mv %s %s"%(apk_path, repackagedAppPath)
    #     commands.getoutput(copy_org_apk)
    #
    #     # Copy original app to build-error-apks
    #     copy_org_apk = "mv %s %s"%(apk_path, signErrorAppPath)
    #     commands.getoutput(copy_org_apk)
    #
    #     return 'sign error'

    # Rename the signed apk
    rename(apkname, repackagedAppPath)

    # Remove the decompiled and modified resources
    # remove_folder(apkname, decompilePath)

# if __name__ == '__main__':
#     global keyPath
#     keyPath = os.path.join('/home/senchen/Desktop/xbot/config/', "coolapk.keystore")
#     sign_apk('MSTG-Android-Jav', '/home/senchen/Desktop/xbot/results/apktool/MSTG-Android-Jav', '/home/senchen/Desktop/xbot/results/repackaged')