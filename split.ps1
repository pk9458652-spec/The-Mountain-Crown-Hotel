Add-Type -AssemblyName System.Drawing
$img = [System.Drawing.Image]::FromFile("c:\hotel site\gallery2.jpeg")
$w = $img.Width / 2
$h = $img.Height / 2

for ($row = 0; $row -lt 2; $row++) {
    for ($col = 0; $col -lt 2; $col++) {
        $bmp = New-Object System.Drawing.Bitmap([int]$w, [int]$h)
        $gfx = [System.Drawing.Graphics]::FromImage($bmp)
        $rect = New-Object System.Drawing.Rectangle([int]($col*$w), [int]($row*$h), [int]$w, [int]$h)
        $gfx.DrawImage($img, 0, 0, $rect, [System.Drawing.GraphicsUnit]::Pixel)
        $idx = $row * 2 + $col + 1
        $bmp.Save("c:\hotel site\split$idx.jpeg", [System.Drawing.Imaging.ImageFormat]::Jpeg)
        $gfx.Dispose()
        $bmp.Dispose()
    }
}
$img.Dispose()
echo "Success"
