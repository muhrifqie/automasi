# Read-screen: dump UI MuMu jadi list text + titik tap
# Pakai: .\read-screen.ps1              -> semua elemen ada text/desc
#        .\read-screen.ps1 -All         -> semua node
#        .\read-screen.ps1 -Find "cari" -> filter text/desc
param([string]$Device = "127.0.0.1:7555", [string]$Find = "", [switch]$All)

adb connect $Device | Out-Null
adb -s $Device shell uiautomator dump /sdcard/ui.xml | Out-Null
[xml]$xml = adb -s $Device exec-out cat /sdcard/ui.xml

$rows = foreach ($n in $xml.SelectNodes("//node")) {
    $t = $n.text; $desc = $n.'content-desc'
    if (-not $All -and -not $t -and -not $desc) { continue }
    $label = if ($t) { $t } else { $desc }
    if ($Find -and $label -notmatch [regex]::Escape($Find)) { continue }
    # bounds "[x1,y1][x2,y2]" -> titik tengah
    if ($n.bounds -match '\[(\d+),(\d+)\]\[(\d+),(\d+)\]') {
        $cx = [int](([int]$Matches[1] + [int]$Matches[3]) / 2)
        $cy = [int](([int]$Matches[2] + [int]$Matches[4]) / 2)
    } else { $cx = $cy = 0 }
    [PSCustomObject]@{
        Text = $label
        Tap  = "$cx,$cy"
        Click = if ($n.clickable -eq 'true') { 'Y' } else { '' }
        Id   = ($n.'resource-id' -replace '^.*/', '')
    }
}
$i = 0
foreach ($r in $rows) {
    $i++
    $flag = if ($r.Click -eq 'Y') { '[tap]' } else { '     ' }
    "{0,2}. {1} {2,-9} {3}" -f $i, $flag, $r.Tap, $r.Text
}
