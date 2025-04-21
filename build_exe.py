import os, subprocess, sys

def create_manifest():
    """Create a manifest file that requests administrator privileges"""
    manifest_content = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="1.0.0.0" processorArchitecture="*" name="BetterThanWindowsClocks" type="win32"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
    </application>
  </compatibility>
</assembly>'''
    manifest_path = "uac_manifest.xml"
    with open(manifest_path, "w") as f:
        f.write(manifest_content)
    return manifest_path
def create_version_info():
    """Create a version info file for the executable"""
    version_info = '''
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u''),
        StringStruct(u'FileDescription', u'Better Than Windows Clocks'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'BetterThanWindowsClocks'),
        StringStruct(u'LegalCopyright', u''),
        StringStruct(u'OriginalFilename', u'BetterThanWindowsClocks.exe'),
        StringStruct(u'ProductName', u'Better Than Windows Clocks'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    version_path = "file_version_info.txt"
    with open(version_path, "w") as f:
        f.write(version_info)
    return version_path
def build_executable():
    """Build the executable using PyInstaller"""
    print("Installing required packages...")
    subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    subprocess.call([sys.executable, "-m", "pip", "install", "pystray"])
    manifest_path = create_manifest()
    print(f"Created UAC manifest: {manifest_path}")
    version_path = create_version_info()
    print(f"Created version info: {version_path}")
    icon_path = "BTWC.ico"
    if not os.path.exists(icon_path):
        print(f"Warning: Custom icon {icon_path} not found. Using default icon.")
        icon_arg = "--icon=NONE"
    else:
        print(f"Using custom icon: {icon_path}")
        icon_arg = f"--icon={icon_path}"   
    print("\nBuilding executable...")
    build_command = [
        "pyinstaller",
        "--name=BetterThanWindowsClocks",
        "--onefile",
        "--windowed", 
        icon_arg,
        f"--add-data={icon_path};." if os.path.exists(icon_path) else "",
        "--add-data=clock_config.json;." if os.path.exists("clock_config.json") else "",
        f"--manifest={os.path.abspath(manifest_path)}", 
        "--uac-admin",  
        f"--version-file={version_path}",
        "desktop_clocks.py"
    ]
    build_command = [cmd for cmd in build_command if cmd]
    subprocess.call(build_command)
    print("\nBuild completed!")
    print("The executable can be found in the dist folder.")
    print("You can now run BetterThanWindowsClocks.exe to start the application.")
    if os.path.exists(manifest_path):
        os.remove(manifest_path)
if __name__ == "__main__":
    build_executable() 
