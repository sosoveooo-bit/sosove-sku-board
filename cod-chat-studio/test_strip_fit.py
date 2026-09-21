import sys
import tempfile
import unittest
from pathlib import Path
from io import BytesIO
from unittest.mock import patch
from PIL import Image, ImageDraw, ImageOps
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from sku_board import backend, cod_strip


class StripFitTests(unittest.TestCase):
    def test_all_four_corners_preserved_at_both_exact_sizes(self):
        colors=['#ff0000','#00ff00','#0000ff','#ffff00']
        for source_size in ((1000,600),(1000,1000),(750,100),(750,150)):
            source=Image.new('RGB',source_size,'white');draw=ImageDraw.Draw(source)
            sw,sh=source_size;cw,ch=sw//5,sh//5
            for box,color in zip([(0,0,cw,ch),(sw-cw,0,sw-1,ch),(0,sh-ch,cw,sh-1),(sw-cw,sh-ch,sw-1,sh-1)],colors):draw.rectangle(box,fill=color)
            for size in ((750,100),(750,150)):
                with self.subTest(source=source_size,target=size):
                    out=cod_strip.fit(source,size);self.assertEqual(out.size,size)
                    full_width=sw/sh>=2.5
                    fitted=Image.new('RGB',size) if full_width else ImageOps.contain(source,(size[0]-8,size[1]-8))
                    x,y=(size[0]-fitted.width)//2,(size[1]-fitted.height)//2
                    dx,dy=max(1,fitted.width//10),max(1,fitted.height//10)
                    positions=[(x+dx,y+dy),(x+fitted.width-dx-1,y+dy),(x+dx,y+fitted.height-dy-1),(x+fitted.width-dx-1,y+fitted.height-dy-1)]
                    for pos,expected in zip(positions,[(255,0,0),(0,255,0),(0,0,255),(255,255,0)]):
                        self.assertTrue(all(abs(a-b)<10 for a,b in zip(out.getpixel(pos),expected)))
                    self.assertGreaterEqual(x,0 if full_width else 4);self.assertGreaterEqual(y,0 if full_width else 4)

    def test_white_poster_matte_does_not_shrink_the_banner(self):
        source=Image.new('RGB',(1200,1200),'white');draw=ImageDraw.Draw(source)
        draw.rectangle((0,430,1199,769),fill='#a01010')
        draw.rectangle((1050,420,1110,460),fill='blue') # Cap protrudes above the background.
        box=cod_strip.content_box(source)
        self.assertLessEqual(box[1],420)
        self.assertGreaterEqual(box[3],770)
        self.assertEqual(box[0],0);self.assertEqual(box[2],1200)
        for target in ((750,100),(750,150)):
            out=cod_strip.fit(source,target)
            self.assertEqual(out.size,target)
            self.assertGreater(out.getpixel((10,target[1]//2))[0],100)
            self.assertLess(out.getpixel((10,target[1]//2))[1],40)
            self.assertGreater(out.getpixel((740,target[1]//2))[0],100)

    def test_source_saved_byte_for_byte(self):
        buffer=BytesIO();Image.new('RGB',(1000,600),'red').save(buffer,format='PNG');raw=buffer.getvalue()
        with tempfile.TemporaryDirectory() as tmp, patch.object(backend,'AD_LAUNCH_UPLOAD_DIR',Path(tmp)):
            materials=[{'id':'AI-0123456789'}]
            backend.preserve_ai_image_strip_originals(materials,[(raw,'image/png')],'750x100')
            self.assertEqual(Path(materials[0]['stripOriginalPath']).read_bytes(),raw)
            self.assertTrue(materials[0]['stripAspectMismatch'])

    def test_actual_compiled_prompt_keeps_geometry_rules(self):
        for size,limit in [('750x100','76px'),('750x150','114px')]:
            prompt=backend.compile_ai_image_cod_hook_text_prompt({'suiteBrief':'1瓶750，2瓶950，3瓶1150，产品保持一致',
                'suiteCountry':'KR','codHookType':'priceBar'},'',size)
            self.assertIn('PRICE STRIP GEOMETRY',prompt)
            self.assertIn(limit,prompt)
            self.assertIn('Place all supplied price tiers side by side',prompt)
            self.assertIn('3瓶1150',prompt)


if __name__=='__main__':unittest.main()
