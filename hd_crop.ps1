Add-Type -AssemblyName System.Drawing

$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$encoderParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
$encoderParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]100)

$src1 = "c:\Users\saksh\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\0FB1996E70DC2E45AB1F0FD67080C1D76C9B150D\transfers\2026-12\WhatsApp Image 2026-03-20 at 8.42.54 PM.jpeg"
$src2 = "c:\Users\saksh\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\0FB1996E70DC2E45AB1F0FD67080C1D76C9B150D\transfers\2026-12\WhatsApp Image 2026-03-20 at 8.52.44 PM.jpeg"

# Process hero.jpeg
$img1 = [System.Drawing.Image]::FromFile($src1)
$newW1 = $img1.Width - 80
$newH1 = $img1.Height - 80
$bmp1 = New-Object System.Drawing.Bitmap($newW1, $newH1)
$gfx1 = [System.Drawing.Graphics]::FromImage($bmp1)
$gfx1.DrawImage($img1, 0, 0, (New-Object System.Drawing.Rectangle(0, 0, $newW1, $newH1)), [System.Drawing.GraphicsUnit]::Pixel)
$bmp1.Save("c:\hotel site\hero.jpeg", $codec, $encoderParams)
$gfx1.Dispose(); $bmp1.Dispose(); $img1.Dispose()

# Process gallery2 splits
$img2 = [System.Drawing.Image]::FromFile($src2)
$w = $img2.Width / 2
$h = $img2.Height / 2

for ($row = 0; $row -lt 2; $row++) {
    for ($col = 0; $col -lt 2; $col++) {
        $bmpTemp = New-Object System.Drawing.Bitmap([int]$w, [int]$h)
        $gfxTemp = [System.Drawing.Graphics]::FromImage($bmpTemp)
        $rectSrc = New-Object System.Drawing.Rectangle([int]($col*$w), [int]($row*$h), [int]$w, [int]$h)
        $gfxTemp.DrawImage($img2, 0, 0, $rectSrc, [System.Drawing.GraphicsUnit]::Pixel)
        
        # Crop 80px to be safe
        $newW2 = $w - 80
        $newH2 = $h - 80
        $bmpFinal = New-Object System.Drawing.Bitmap([int]$newW2, [int]$newH2)
        $gfxFinal = [System.Drawing.Graphics]::FromImage($bmpFinal)
        $gfxFinal.DrawImage($bmpTemp, 0, 0, (New-Object System.Drawing.Rectangle(0, 0, $newW2, $newH2)), [System.Drawing.GraphicsUnit]::Pixel)
        
        $idx = $row * 2 + $col + 1
        $bmpFinal.Save("c:\hotel site\split$idx.jpeg", $codec, $encoderParams)
        
        $gfxFinal.Dispose(); $bmpFinal.Dispose()
        $gfxTemp.Dispose(); $bmpTemp.Dispose()
    }
}
$img2.Dispose()

Write-Host "HD rewrite complete!"
