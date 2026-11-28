"""Recortes técnicos de los PNG generados: alfa limpio y sin halo rectangular."""
from pathlib import Path
from PIL import Image,ImageFilter
P=Path(__file__).resolve().parent
def run():
    for f in (P/'assets').glob('*.png'):
        if f.stem in ['benghazi','tartus']:continue
        im=Image.open(f).convert('RGBA')
        a=im.getchannel('A').point(lambda v:255 if v>=180 else 0).filter(ImageFilter.GaussianBlur(.5))
        im.putalpha(a)
        if im.getbbox():im.crop(im.getbbox()).save(P/'_prep'/('cut_el_'+f.stem+'.png'))
if __name__=='__main__':run()
