import urllib.request
import ssl
import os

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

target = os.path.join(r'C:\UE_Project\MCPGameProject\Content\TransformationVFX\SM2SM', 'FZXiaoZhuanTi.ttf')

urls = [
    'https://down.shufami.com/font/FZXiaoZhuanTi-R-GB.TTF',
    'https://img.zhaozi.cn/fonts/FZXiaoZhuanTi-R-GB.TTF',
    'https://dl.100font.com/font/foundertype/fzxz/fzxz.TTF',
    'https://font.jsfont.net/down/fzxz.TTF',
    'https://www.diyiziti.com/Download/484'
]

for url in urls:
    try:
        print(f'Trying: {url}')
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        resp = urllib.request.urlopen(req, timeout=20, context=ctx)
        data = resp.read()
        if len(data) > 500000:
            with open(target, 'wb') as f:
                f.write(data)
            print(f'Success! Size: {len(data)} bytes')
            break
        else:
            print(f'Too small: {len(data)} bytes')
    except Exception as e:
        print(f'Failed: {str(e)[:100]}')

if not os.path.exists(target):
    print('All downloads failed')
