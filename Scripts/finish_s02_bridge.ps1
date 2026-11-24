$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;

public static class S02BridgeLock {
    static int[][] palette = new int[][] {
        new int[]{255,255,255}, new int[]{8,10,11}, new int[]{170,193,207},
        new int[]{214,214,209}, new int[]{173,178,181}, new int[]{143,215,247}, new int[]{0,125,229}
    };
    static Color Flat(Color c) {
        if(c.R>242 && c.G>242 && c.B>242) return Color.White;
        int best=0,distance=int.MaxValue;
        for(int p=0;p<palette.Length;p++) {
            int dr=c.R-palette[p][0],dg=c.G-palette[p][1],db=c.B-palette[p][2];
            int d=dr*dr+dg*dg+db*db;
            if(d<distance){distance=d;best=p;}
        }
        return Color.FromArgb(palette[best][0],palette[best][1],palette[best][2]);
    }
    public static void Export(string originalPath,string editedPath,string outputPath,string maskPath) {
        using(var original=new Bitmap(originalPath))
        using(var edit=new Bitmap(editedPath))
        using(var output=new Bitmap(original))
        using(var maskImage=new Bitmap(original.Width,original.Height,PixelFormat.Format24bppRgb)) {
            if(original.Width!=edit.Width || original.Height!=edit.Height) throw new Exception("Edit canvas changed");
            int w=original.Width,h=original.Height;
            bool[] mask=new bool[w*h];
            // Above the railway, the only nonwhite original object is the road arch.
            for(int y=440;y<602;y++) for(int x=297;x<=727;x++) mask[y*w+x]=true;
            // Below that line, restrict the edit to the steel arch's colored footprint
            // and its marker contour, retaining the original railway and all piers.
            for(int y=596;y<=702;y++) for(int x=298;x<=725;x++) {
                double dx=(x-512.0)/208.0;
                double outer=447+230*dx*dx;
                double inner=561+116*Math.Pow((x-512.0)/178.0,2);
                if(y<outer-24 || y>inner+10) continue;
                var c=original.GetPixel(x,y);
                if(Math.Abs(c.R-170)>14 || Math.Abs(c.G-193)>14 || Math.Abs(c.B-207)>14) continue;
                for(int oy=-6;oy<=6;oy++) for(int ox=-6;ox<=6;ox++) {
                    if(ox*ox+oy*oy>36) continue;
                    int mx=x+ox,my=y+oy;
                    if(mx>=297 && mx<=727 && my>=440 && my<=702) mask[my*w+mx]=true;
                }
            }
            // Include the old arch's antialiased edge pixels in the empty gap.
            // Rear pier footprints are retained from the original without change.
            for(int y=628;y<=674;y++) for(int x=297;x<=727;x++) {
                bool rearPier=(x>=407 && x<=444)||(x>=571 && x<=611);
                if(!rearPier) mask[y*w+x]=true;
            }
            for(int y=675;y<=701;y++) for(int x=303;x<=720;x++) mask[y*w+x]=true;
            for(int y=702;y<=703;y++) for(int x=303;x<=720;x++) {
                bool frontPier=(x>=368 && x<=419)||(x>=594 && x<=645);
                if(!frontPier) mask[y*w+x]=true;
            }
            using(var g=Graphics.FromImage(maskImage))g.Clear(Color.Black);
            for(int y=440;y<=703;y++) for(int x=297;x<=727;x++) if(mask[y*w+x]) {
                output.SetPixel(x,y,Flat(edit.GetPixel(x,y)));
                maskImage.SetPixel(x,y,Color.White);
            }
            output.Save(outputPath,ImageFormat.Png);
            maskImage.Save(maskPath,ImageFormat.Png);
        }
    }
}
'@

$taskRoot = Join-Path $PSScriptRoot '..\Imagenes\Shorts\S02'
[S02BridgeLock]::Export(
    (Join-Path $taskRoot 'capas\bg_bridge.png'),
    (Join-Path $taskRoot '_imagegen\bg_bridge_broken.png'),
    (Join-Path $taskRoot 'capas\bg_bridge_broken.png'),
    (Join-Path $taskRoot '_imagegen\bridge_removal_mask.png')
)
Write-Output 'bg_bridge_broken.png: exported with original pixels retained outside the removal mask.'
