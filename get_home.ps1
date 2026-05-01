Add-Type -AssemblyName System.Drawing
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]100)

$src = "c:\Users\saksh\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\0FB1996E70DC2E45AB1F0FD67080C1D76C9B150D\transfers\2026-12\WhatsApp Image 2026-03-20 at 9.15.16 PM.jpeg"
$img = [System.Drawing.Image]::FromFile($src)
$nW = $img.Width - 80
$nH = $img.Height - 80

$bmp = New-Object System.Drawing.Bitmap($nW, $nH)
$gfx = [System.Drawing.Graphics]::FromImage($bmp)
$gfx.DrawImage($img, 0, 0, (New-Object System.Drawing.Rectangle(0, 0, $nW, $nH)), [System.Drawing.GraphicsUnit]::Pixel)

$bmp.Save("c:\hotel site\home.jpeg", $codec, $ep)
$gfx.Dispose(); $bmp.Dispose(); $img.Dispose()
Write-Host "HD extraction finished!"
