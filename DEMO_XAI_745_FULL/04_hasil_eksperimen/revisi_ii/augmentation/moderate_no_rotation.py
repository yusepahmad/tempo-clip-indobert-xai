def aug(im,sid,mode):
 r=random.Random(int(hashlib.sha256(f'{sid}:{mode}:20261018'.encode()).hexdigest()[:16],16));im=im.convert('RGB')
 if mode=='light':br,co,q,rot,sig=(.92,1.08),(.92,1.08),(88,96),0,1.5
 else:br,co,q,rot,sig=(.85,1.15),(.85,1.15),(78,90),0.0*r.uniform(-2,2),3.
 im=ImageEnhance.Brightness(im).enhance(r.uniform(*br));im=ImageEnhance.Contrast(im).enhance(r.uniform(*co))
 if rot:im=im.rotate(rot,resample=Image.Resampling.BICUBIC,fillcolor=(255,255,255))
 b=io.BytesIO();im.save(b,'JPEG',quality=r.randint(*q));b.seek(0);arr=np.asarray(Image.open(b).convert('RGB')).astype(np.int16);noise=np.random.default_rng(r.randrange(2**32)).normal(0,sig,arr.shape);return Image.fromarray(np.clip(arr+noise,0,255).astype('uint8'))
