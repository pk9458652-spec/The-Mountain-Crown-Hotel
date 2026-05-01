Add-Type -AssemblyName System.Drawing

$files = @("c:\hotel site\hero.jpeg", "c:\hotel site\split1.jpeg", "c:\hotel site\split2.jpeg", "c:\hotel site\split3.jpeg", "c:\hotel site\split4.jpeg")

foreach ($file in $files) {
    if (Test-Path $file) {
        $img = [System.Drawing.Image]::FromFile($file)
        
        # Crop 80 pixels from right and bottom to remove the watermark
        $newW = $img.Width - 80
        $newH = $img.Height - 80
        
        if ($newW -gt 0 -and $newH -gt 0) {
            $bmp = New-Object System.Drawing.Bitmap($newW, $newH)
            $gfx = [System.Drawing.Graphics]::FromImage($bmp)
            $rect = New-Object System.Drawing.Rectangle(0, 0, $newW, $newH)
            $gfx.DrawImage($img, 0, 0, $rect, [System.Drawing.GraphicsUnit]::Pixel)
            
            $img.Dispose()
            $bmp.Save($file, [System.Drawing.Imaging.ImageFormat]::Jpeg)
            
            $gfx.Dispose()
            $bmp.Dispose()
            Write-Host "Cropped $file"
        } else {
            $img.Dispose()
        }
    }
}
Write-Host "Done"
