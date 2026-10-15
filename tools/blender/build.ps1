param([string]$BlenderPath, [switch]$SkipPreview, [ValidateSet('prototype','town','detail','environment','reference')][string]$Layout='prototype')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not $BlenderPath) {
  $aliasCommand=Get-Command blender-launcher -ErrorAction SilentlyContinue
  if($aliasCommand){$BlenderPath=$aliasCommand.Source}
  $store=Get-AppxPackage *Blender* | Select-Object -First 1
  if($store -and -not $BlenderPath) {
    foreach($relative in @('Blender/blender.exe','blender.exe')) {
      $candidate=Join-Path $store.InstallLocation $relative
      if(Test-Path -LiteralPath $candidate){$BlenderPath=$candidate;break}
    }
  }
  if(-not $BlenderPath){$command=Get-Command blender -ErrorAction SilentlyContinue;if($command){$BlenderPath=$command.Source}}
}
if(-not $BlenderPath){throw 'Blender not found. Pass -BlenderPath with the absolute path to blender.exe.'}
$os=Get-CimInstance Win32_OperatingSystem
if($os.FreePhysicalMemory -lt 1GB/1KB){throw 'Less than 1 GB free RAM. Close unused applications before generation.'}
$generator=if($Layout -eq 'reference'){'rebuild_reference.py'}elseif($Layout -eq 'environment'){'environment_town.py'}elseif($Layout -eq 'detail'){'detail_town.py'}else{'generate.py'}
$arguments=@('--background','--factory-startup','--threads','4','--python-exit-code','1','--python',"$PSScriptRoot/$generator",'--','--root',$projectRoot)
if($Layout -in @('prototype','town')){$arguments+=@('--layout',$Layout)}
if($SkipPreview){$arguments+='--skip-preview'}
$buildStarted=Get-Date
& $BlenderPath @arguments
if($LASTEXITCODE -ne 0){throw "Blender failed with exit code $LASTEXITCODE"}
$successFile=Join-Path $projectRoot $(if($Layout -eq 'reference'){'artifacts/reference-pass-05/build-success.json'}elseif($Layout -eq 'environment'){'artifacts/environment-pass-04/build-success.json'}elseif($Layout -eq 'detail'){'artifacts/detail-pass-03/build-success.json'}elseif($Layout -eq 'town'){'artifacts/layout-pass-02/build-success.json'}else{'artifacts/build-success.json'})
if(-not(Test-Path -LiteralPath $successFile) -or (Get-Item -LiteralPath $successFile).LastWriteTime -lt $buildStarted){throw 'Blender did not finish this build. See artifacts/generation.log.'}
