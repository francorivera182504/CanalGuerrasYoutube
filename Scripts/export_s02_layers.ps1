param([Parameter(Mandatory=$true)][string]$ManifestPath)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class S02LayerExport {
    public static string Export(string sourcePath, string outputPath, string kind, int[][] palette) {
        using (var source = new Bitmap(sourcePath))
        using (var flat = new Bitmap(source.Width, source.Height, PixelFormat.Format24bppRgb)) {
            using (var g = Graphics.FromImage(flat)) { g.Clear(Color.White); g.DrawImageUnscaled(source, 0, 0); }
            var bounds = new Rectangle(0, 0, flat.Width, flat.Height);
            var data = flat.LockBits(bounds, ImageLockMode.ReadWrite, PixelFormat.Format24bppRgb);
            byte[] bytes = new byte[data.Stride * flat.Height];
            Marshal.Copy(data.Scan0, bytes, 0, bytes.Length);
            int left=flat.Width, top=flat.Height, right=-1, bottom=-1;
            for (int y=0; y<flat.Height; y++) for (int x=0; x<flat.Width; x++) {
                int offset = y*data.Stride + x*3;
                int b=bytes[offset], gr=bytes[offset+1], r=bytes[offset+2];
                int best=0, distance=int.MaxValue;
                if (r>242 && gr>242 && b>242) {
                    bytes[offset]=255; bytes[offset+1]=255; bytes[offset+2]=255;
                    continue;
                }
                for (int p=0; p<palette.Length; p++) {
                    int dr=r-palette[p][0], dg=gr-palette[p][1], db=b-palette[p][2];
                    int d=dr*dr+dg*dg+db*db;
                    if(d<distance) {distance=d;best=p;}
                }
                bytes[offset]=(byte)palette[best][2];
                bytes[offset+1]=(byte)palette[best][1];
                bytes[offset+2]=(byte)palette[best][0];
                if (palette[best][0]<250 || palette[best][1]<250 || palette[best][2]<250) {
                    left=Math.Min(left,x);top=Math.Min(top,y);right=Math.Max(right,x);bottom=Math.Max(bottom,y);
                }
            }
            Marshal.Copy(bytes,0,data.Scan0,bytes.Length);
            flat.UnlockBits(data);
            if(right<left) throw new Exception("No artwork found: "+sourcePath);
            int canvasW=1024, canvasH=kind=="element" ? 1024 : 1536;
            int maxW=kind=="element" ? 744 : kind=="map" ? 884 : 1024;
            int maxH=kind=="element" ? 744 : 710;
            int artW=right-left+1, artH=bottom-top+1;
            double scale=Math.Min((double)maxW/artW,(double)maxH/artH);
            int targetW=(int)Math.Round(artW*scale), targetH=(int)Math.Round(artH*scale);
            int targetX=(canvasW-targetW)/2;
            int targetY=kind=="element" ? (canvasH-targetH)/2 : 330+(710-targetH)/2;
            using(var output=new Bitmap(canvasW,canvasH,PixelFormat.Format24bppRgb)) {
                using(var g=Graphics.FromImage(output)) {
                    g.Clear(Color.White);
                    g.InterpolationMode=InterpolationMode.HighQualityBicubic;
                    g.PixelOffsetMode=PixelOffsetMode.HighQuality;
                    g.CompositingQuality=CompositingQuality.HighQuality;
                    using(var attributes=new ImageAttributes()) {
                        attributes.SetWrapMode(WrapMode.TileFlipXY);
                        g.DrawImage(flat,new Rectangle(targetX,targetY,targetW,targetH),left,top,artW,artH,GraphicsUnit.Pixel,attributes);
                    }
                }
                output.Save(outputPath,ImageFormat.Png);
            }
            return String.Format("{0}: {1}x{2}; art {3},{4},{5},{6}",System.IO.Path.GetFileName(outputPath),canvasW,canvasH,targetX,targetY,targetW,targetH);
        }
    }
}
'@

$taskManifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
foreach ($taskAsset in $taskManifest) {
    $taskPalette = [int[][]]@($taskAsset.palette | ForEach-Object { ,[int[]]$_ })
    [S02LayerExport]::Export($taskAsset.source, $taskAsset.output, $taskAsset.kind, $taskPalette)
}
