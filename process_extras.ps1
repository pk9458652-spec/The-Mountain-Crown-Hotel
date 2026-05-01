Add-Type -AssemblyName System.Drawing
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq 'image/jpeg' }
$ep = New-Object System.Drawing.Imaging.EncoderParameters(1)
$ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]100)

$files = @(
    "WhatsApp Image 2026-03-20 at 9.00.12 PM (1).jpeg",
    "WhatsApp Image 2026-03-20 at 9.00.12 PM (2).jpeg",
    "WhatsApp Image 2026-03-20 at 9.00.12 PM.jpeg",
    "WhatsApp Image 2026-03-20 at 9.30.56 PM (1).jpeg",
    "WhatsApp Image 2026-03-20 at 9.30.56 PM.jpeg"
)

for ($i = 0; $i -lt $files.Length; $i++) {
    $src = "c:\hotel site\" + $files[$i]
    if (Test-Path $src) {
        $img = [System.Drawing.Image]::FromFile($src)
        $nW = $img.Width - 80
        $nH = $img.Height - 80
        if ($nW -gt 0 -and $nH -gt 0) {
            $bmp = New-Object System.Drawing.Bitmap($nW, $nH)
            $gfx = [System.Drawing.Graphics]::FromImage($bmp)
            $gfx.DrawImage($img, 0, 0, (New-Object System.Drawing.Rectangle(0, 0, $nW, $nH)), [System.Drawing.GraphicsUnit]::Pixel)
            
            $destName = "c:\hotel site\extra" + ($i + 1) + ".jpeg"
            $bmp.Save($destName, $codec, $ep)
            $gfx.Dispose(); $bmp.Dispose()
        }
        $img.Dispose()
    }
}
Write-Host "Processed extras!"
