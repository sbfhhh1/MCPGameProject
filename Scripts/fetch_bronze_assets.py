"""
Download public-domain bronze-artifact photos (The Met Open Access, CC0 / Public Domain)
and procedurally generate ink-paper background + seal textures, then import them all
into /Game/BronzeExhibit/Visual so the exhibit widget can reference them.

Run from the UE Python console:
    C:/UE_Project/MCPGameProject/Scripts/fetch_bronze_assets.py
"""
import os
import io
import struct
import zlib
import urllib.request
import ssl
import unreal

PROJECT_DIR = unreal.Paths.project_dir()
SRC_DIR = os.path.join(PROJECT_DIR, "Content", "BronzeExhibit", "SourceArt")
DEST_PKG = "/Game/BronzeExhibit/Visual"
os.makedirs(SRC_DIR, exist_ok=True)

# Met Open Access (Public Domain) bronze artifacts — web-large JPEGs.
MET_IMAGES = {
    "T_Bronze_Ding":  "https://images.metmuseum.org/CRDImages/as/web-large/DP164965.jpg",  # Shang ding
    "T_Bronze_Zun":   "https://images.metmuseum.org/CRDImages/as/web-large/DP155112.jpg",  # Shang/Zhou zun
    "T_Bronze_Gui":   "https://images.metmuseum.org/CRDImages/as/web-large/DP218223.jpg",  # Western Zhou gui
}


def log(m):
    unreal.log("[FetchBronze] " + str(m))


def download(url, dest_path):
    if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 2000:
        log("cached " + os.path.basename(dest_path))
        return True
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            data = r.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        log("downloaded %s (%d bytes)" % (os.path.basename(dest_path), len(data)))
        return True
    except Exception as e:
        log("DOWNLOAD FAILED %s : %s" % (url, e))
        return False


# ---- minimal PNG writer (no PIL dependency) ----
def write_png(path, width, height, rgba_bytes):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    raw = bytearray()
    stride = width * 4
    for y in range(height):
        raw.append(0)
        raw.extend(rgba_bytes[y * stride:(y + 1) * stride])
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def gen_paper(path, w=1024, h=576):
    """Warm charcoal rice-paper grain, faintly mottled."""
    import random
    random.seed(20260611)
    base = (16, 15, 13)            # warm near-black
    px = bytearray(w * h * 4)
    for y in range(h):
        for x in range(w):
            # gentle vignette + fibrous grain
            n = random.randint(-6, 7)
            fib = 3 if (random.random() < 0.04) else 0
            r = max(0, min(255, base[0] + n + fib))
            g = max(0, min(255, base[1] + n + fib))
            b = max(0, min(255, base[2] + n))
            i = (y * w + x) * 4
            px[i] = r; px[i+1] = g; px[i+2] = b; px[i+3] = 255
    write_png(path, w, h, px)
    log("generated paper texture")


def gen_inkwash(path, w=768, h=768):
    """Soft radial ink splash, transparent background, for behind the artifact."""
    import random, math
    random.seed(777)
    cx, cy = w * 0.5, h * 0.52
    px = bytearray(w * h * 4)
    for y in range(h):
        for x in range(w):
            dx = (x - cx) / (w * 0.5)
            dy = (y - cy) / (h * 0.5)
            d = math.sqrt(dx * dx * 1.3 + dy * dy)
            a = max(0.0, 1.0 - d)
            a = a ** 2.2
            # ragged edge
            if random.random() < 0.06:
                a *= 0.4
            alpha = int(190 * a)
            i = (y * w + x) * 4
            px[i] = 8; px[i+1] = 7; px[i+2] = 6; px[i+3] = alpha
    write_png(path, w, h, px)
    log("generated inkwash texture")


def import_png(name, src_file, srgb=True):
    asset_path = "%s/%s" % (DEST_PKG, name)
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)
    task = unreal.AssetImportTask()
    task.filename = src_file
    task.destination_path = DEST_PKG
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.EditorAssetLibrary.load_asset(asset_path)
    if tex:
        log("imported " + asset_path)
    else:
        log("IMPORT FAILED " + asset_path)
    return tex


def run():
    results = {}
    # 1. Met bronze photos
    for name, url in MET_IMAGES.items():
        jpg = os.path.join(SRC_DIR, name + ".jpg")
        if download(url, jpg):
            import_png(name, jpg)
            results[name] = True
        else:
            results[name] = False

    # 2. procedural textures (always succeed, no network)
    paper = os.path.join(SRC_DIR, "T_Bronze_Paper.png")
    gen_paper(paper)
    import_png("T_Bronze_Paper", paper)

    ink = os.path.join(SRC_DIR, "T_Bronze_InkWash.png")
    gen_inkwash(ink)
    import_png("T_Bronze_InkWash", ink)

    unreal.EditorAssetLibrary.save_directory(DEST_PKG, only_if_is_dirty=False)
    log("DONE results=" + str(results))


run()
