# Original VotoAberto vector mark. MIT, like the project source.
# Windows / PowerShell: rebuild PNG/ICO assets from this small geometric design.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$appRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../apps/votoaberto_flutter'))

function New-MarkPng([int]$size) {
    $bitmap = [Drawing.Bitmap]::new($size, $size)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([Drawing.ColorTranslator]::FromHtml('#006962'))
    $pen = [Drawing.Pen]::new([Drawing.ColorTranslator]::FromHtml('#fafbf9'), $size * 0.085)
    $pen.StartCap = [Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [Drawing.Drawing2D.LineCap]::Round
    $pen.LineJoin = [Drawing.Drawing2D.LineJoin]::Round
    $points = [Drawing.PointF[]]@(
        [Drawing.PointF]::new($size * 0.29, $size * 0.37),
        [Drawing.PointF]::new($size * 0.48, $size * 0.66),
        [Drawing.PointF]::new($size * 0.72, $size * 0.30)
    )
    $graphics.DrawLines($pen, $points)
    $stream = [IO.MemoryStream]::new()
    $bitmap.Save($stream, [Drawing.Imaging.ImageFormat]::Png)
    $bytes = $stream.ToArray()
    $stream.Dispose(); $pen.Dispose(); $graphics.Dispose(); $bitmap.Dispose()
    return ,$bytes
}

foreach ($size in @(192, 512)) {
    $bytes = New-MarkPng $size
    [IO.File]::WriteAllBytes((Join-Path $appRoot "web/icons/Icon-$size.png"), $bytes)
    [IO.File]::WriteAllBytes((Join-Path $appRoot "web/icons/Icon-maskable-$size.png"), $bytes)
}
[IO.File]::WriteAllBytes((Join-Path $appRoot 'web/favicon.png'), (New-MarkPng 32))
foreach ($item in @(@('mdpi',48), @('hdpi',72), @('xhdpi',96), @('xxhdpi',144), @('xxxhdpi',192))) {
    [IO.File]::WriteAllBytes((Join-Path $appRoot "android/app/src/main/res/mipmap-$($item[0])/ic_launcher.png"), (New-MarkPng $item[1]))
}
$sizes = @(32, 48, 256)
$images = @($sizes | ForEach-Object { ,(New-MarkPng $_) })
$file = [IO.File]::Create((Join-Path $appRoot 'windows/runner/resources/app_icon.ico'))
$writer = [IO.BinaryWriter]::new($file)
$writer.Write([uint16]0); $writer.Write([uint16]1); $writer.Write([uint16]$sizes.Count)
$offset = 6 + 16 * $sizes.Count
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $dimension = if ($sizes[$i] -eq 256) { 0 } else { $sizes[$i] }
    $writer.Write([byte]$dimension); $writer.Write([byte]$dimension)
    $writer.Write([byte]0); $writer.Write([byte]0)
    $writer.Write([uint16]1); $writer.Write([uint16]32)
    $writer.Write([uint32]$images[$i].Length); $writer.Write([uint32]$offset)
    $offset += $images[$i].Length
}
foreach ($bytes in $images) { $writer.Write([byte[]]$bytes) }
$writer.Dispose(); $file.Dispose()
Write-Output 'Ícones VotoAberto atualizados (arte geométrica original).'
