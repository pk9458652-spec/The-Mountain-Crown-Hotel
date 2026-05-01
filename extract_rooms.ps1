Add-Type -AssemblyName System.Drawing
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]100)

$src = "c:\Users\saksh\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\0FB1996E70DC2E45AB1F0FD67080C1D76C9B150D\transfers\2026-12\WhatsApp Image 2026-03-20 at 9.20.16 PM.jpeg"
$img = [System.Drawing.Image]::FromFile($src)
$w = $img.Width
$h = $img.Height

# Top Left (Room 1)
$r1w = [int]($w/2)
$r1h = [int]($h/2)
$bmp1 = New-Object System.Drawing.Bitmap($r1w, $r1h)
$gfx1 = [System.Drawing.Graphics]::FromImage($bmp1)
$gfx1.DrawImage($img, 0, 0, (New-Object System.Drawing.Rectangle(0, 0, $r1w, $r1h)), [System.Drawing.GraphicsUnit]::Pixel)
$bmp1.Save("c:\hotel site\room1.jpeg", $codec, $ep)
$gfx1.Dispose(); $bmp1.Dispose()

# Top Right (Room 2)
$bmp2 = New-Object System.Drawing.Bitmap($r1w, $r1h)
$gfx2 = [System.Drawing.Graphics]::FromImage($bmp2)
$gfx2.DrawImage($img, 0, 0, (New-Object System.Drawing.Rectangle($r1w, 0, $r1w, $r1h)), [System.Drawing.GraphicsUnit]::Pixel)
$bmp2.Save("c:\hotel site\room2.jpeg", $codec, $ep)
$gfx2.Dispose(); $bmp2.Dispose()

# Bottom Half (Gallery 3) - Crop 80 from bottom and right to remove the logo
$g3w = $w - 80
$g3h = [int]($h/2) - 80
$bmp3 = New-Object System.Drawing.Bitmap($g3w, $g3h)
$gfx3 = [System.Drawing.Graphics]::FromImage($bmp3)
$gfx3.DrawImage($img, 0, 0, (New-Object System.Drawing.Rectangle(0, [int]($h/2), $g3w, $g3h)), [System.Drawing.GraphicsUnit]::Pixel)
$bmp3.Save("c:\hotel site\gallery3.jpeg", $codec, $ep)
$gfx3.Dispose(); $bmp3.Dispose()

$img.Dispose()
Write-Host "Images extracted successfully!"
