"""Fit complete COD strip artwork without cropping or changing proportions."""
from collections import Counter
from PIL import Image, ImageOps, ImageChops


def content_box(source):
    """Trim only a uniform light/transparent outer matte; never guess a center crop."""
    source = source.convert('RGBA')
    rgb = Image.new('RGB', source.size, 'white')
    rgb.paste(source, mask=source.getchannel('A'))
    corners = [rgb.getpixel(p) for p in ((0,0),(rgb.width-1,0),(0,rgb.height-1),(rgb.width-1,rgb.height-1))]
    # Conservative: a colored or complex edge belongs to the artwork.
    if any(min(pixel) < 230 for pixel in corners):
        return (0,0,source.width,source.height)
    background = tuple(sorted(pixel[channel] for pixel in corners)[1] for channel in range(3))
    difference = ImageChops.difference(rgb, Image.new('RGB', rgb.size, background))
    bands = difference.split()
    mask = ImageChops.lighter(ImageChops.lighter(bands[0], bands[1]), bands[2]).point(lambda p: 255 if p > 24 else 0)
    box = mask.getbbox()
    if not box:
        return (0,0,source.width,source.height)
    left,top,right,bottom=box
    pad=3
    return (max(0,left-pad),max(0,top-pad),min(source.width,right+pad),min(source.height,bottom+pad))


def fit(source, target_size):
    source = ImageOps.exif_transpose(source).convert('RGBA')
    source = source.crop(content_box(source))
    # A confirmed horizontal artwork is fitted across the output width/height,
    # retaining every foreground pixel rather than retaining the outer poster matte.
    if source.width / source.height >= 2.5:
        canvas = Image.new('RGBA', target_size, '#f8f8f8')
        canvas.alpha_composite(source.resize(target_size, Image.Resampling.LANCZOS))
        return canvas.convert('RGB')
    sample = source.resize((24, 24))
    edge_pixels = [sample.getpixel((x, y)) for x in range(24) for y in (0, 23)]
    edge_pixels += [sample.getpixel((x, y)) for y in range(1, 23) for x in (0, 23)]
    colors = Counter(tuple((v // 16) * 16 for v in pixel[:3]) for pixel in edge_pixels if pixel[3] >= 128)
    background = colors.most_common(1)[0][0] if colors else (248, 248, 248)
    canvas = Image.new('RGBA', target_size, (*background, 255))
    # Small processing guard; the larger 12/18px design safe zone is authored upstream.
    guard = 4
    fitted = ImageOps.contain(source, (target_size[0] - 2 * guard, target_size[1] - 2 * guard), Image.Resampling.LANCZOS)
    position = ((target_size[0] - fitted.width) // 2, (target_size[1] - fitted.height) // 2)
    canvas.alpha_composite(fitted, position)
    return canvas.convert('RGB')


def instruction(size):
    width, height = (int(part) for part in size.split('x'))
    margin = 12 if height == 100 else 18
    return (
        f'[PRICE STRIP GEOMETRY — exact {width}x{height}, ratio {width / height:g}:1] '
        f'Compose directly for this ultra-wide canvas, not a tall poster to crop later. '
        f'The actual colored artwork must have ratio {width / height:g}:1, not just the outer file. '
        'No white top/bottom poster matte, no small banner centered in a square canvas. '
        f'Background alone reaches every edge. All glyphs, prices, currency marks, quantity labels, '
        f'product caps and bases stay between y={margin} and y={height - margin}, and x=12 to x={width - 12}. '
        f'Product total height at most {height - 2 * margin}px, including its cap and base; preserve its aspect ratio. '
        'Arrange every supplied price tier side by side on one horizontal baseline; place each complete quantity label '
        'above its corresponding complete price inside the same tier. Price tiers have priority over decoration. '
        'If people or a comparison are requested, allocate a compact left zone and one product zone on the right; '
        'divide the remaining width across all supplied tiers. Keep photos, product and prices from overlapping. '
        'Fit text to its own zone by adjusting spacing and type size; never remove digits, currency, units, tiers or conditions. '
        'Do not place a second price row below the bottom edge or enlarge the bottle beyond the canvas. '
        'Preserve the exact user copy policy, product identity and values; add no unprovided price. '
        'This is a layout instruction, not visible copy. Text-free requests remain text-free.'
    )
