import mimetypes
import base64
import shutil
import subprocess
import tempfile
from pathlib import Path
from functools import lru_cache
from urllib.parse import urlsplit
from xml.etree import ElementTree

from django.conf import settings
from django.http import FileResponse
from PIL import Image, ImageDraw, ImageFont, ImageSequence


class WatermarkProcessingError(Exception):
    pass


def _brand_logo():
    from io import BytesIO

    with Image.open(BytesIO(_brand_logo_bytes())) as logo:
        logo.load()
        return logo.convert("RGBA")


@lru_cache(maxsize=1)
def _brand_logo_bytes():
    path = settings.BASE_DIR.parent / "follia-library" / "src" / "assets" / "logo" / "image.png"
    return path.read_bytes()


def _font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size=size)
    except OSError:
        return ImageFont.load_default(size=size)


def _watermark_png(username, site_url, width=680, height=136):
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((1, 1, width - 2, height - 2), radius=20, fill=(15, 17, 20, 190))

    logo = _brand_logo()
    logo.thumbnail((height - 32, height - 32), Image.Resampling.LANCZOS)
    canvas.alpha_composite(logo, (16, (height - logo.height) // 2))

    text_x = height + 4
    primary = _font(max(18, int(height * 0.2)))
    secondary = _font(max(13, int(height * 0.13)))
    draw.text((text_x, 28), "Follia Library  ·  @" + username, font=primary, fill=(255, 255, 255, 255))
    draw.text((text_x, 78), site_url, font=secondary, fill=(236, 239, 242, 255))
    return canvas


def _watermark_svg(source_path, output_path, username, site_url):
    tree = ElementTree.parse(source_path)
    root = tree.getroot()
    view_box = root.get("viewBox")
    if view_box:
        _, _, width, height = (float(part) for part in view_box.replace(",", " ").split())
    else:
        width = float(str(root.get("width", "1000")).replace("px", ""))
        height = float(str(root.get("height", "1000")).replace("px", ""))
        root.set("viewBox", f"0 0 {width:g} {height:g}")
    namespace = "{http://www.w3.org/2000/svg}"
    panel_width = width * 0.58
    panel_height = height * 0.16
    margin = min(width, height) * 0.025
    x = width - panel_width - margin
    y = height - panel_height - margin
    group = ElementTree.SubElement(root, namespace + "g", {"opacity": "0.84"})
    ElementTree.SubElement(group, namespace + "rect", {"x": f"{x:g}", "y": f"{y:g}", "width": f"{panel_width:g}", "height": f"{panel_height:g}", "rx": f"{panel_height * .14:g}", "fill": "#0f1114"})
    logo_width = panel_height * 0.72
    logo_x = x + panel_height * 0.15
    logo_y = y + (panel_height - logo_width) / 2
    ElementTree.SubElement(group, namespace + "image", {
        "x": f"{logo_x:g}", "y": f"{logo_y:g}", "width": f"{logo_width:g}", "height": f"{logo_width:g}",
        "preserveAspectRatio": "xMidYMid meet",
        "href": "data:image/png;base64," + base64.b64encode(_brand_logo_bytes()).decode("ascii"),
        "{http://www.w3.org/1999/xlink}href": "data:image/png;base64," + base64.b64encode(_brand_logo_bytes()).decode("ascii"),
    })
    text_x = logo_x + logo_width + panel_height * 0.12
    first_size = panel_height * 0.22
    second_size = panel_height * 0.14
    first = ElementTree.SubElement(group, namespace + "text", {"x": f"{text_x:g}", "y": f"{y + panel_height * .4:g}", "fill": "white", "font-family": "sans-serif", "font-size": f"{first_size:g}"})
    first.text = "Follia Library  ·  @" + username
    second = ElementTree.SubElement(group, namespace + "text", {"x": f"{text_x:g}", "y": f"{y + panel_height * .72:g}", "fill": "#eceff2", "font-family": "sans-serif", "font-size": f"{second_size:g}"})
    second.text = site_url
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def _temporary_response(temp_dir, path, filename, content_type):
    response = FileResponse(open(path, "rb"), as_attachment=True, filename=filename, content_type=content_type)
    response._resource_closers.append(temp_dir.cleanup)
    return response


def _copy_storage_file(field, path):
    with field.open("rb") as source, open(path, "wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)


def _public_site_url():
    site_url = (getattr(settings, "FOLLIA_PUBLIC_URL", "") or settings.FRONTEND_URL).rstrip("/")
    hostname = (urlsplit(site_url).hostname or "").lower()
    if not settings.DEBUG and (not hostname or hostname in {"localhost", "127.0.0.1", "::1"}):
        raise WatermarkProcessingError(
            "Set FOLLIA_PUBLIC_URL or FRONTEND_URL to the public Follia Library site before enabling media downloads."
        )
    return site_url


def watermarked_download(field, filename, username, supplied_content_type=""):
    """Return a watermarked download while leaving the stored original unchanged."""
    extension = Path(filename).suffix.lower()
    declared_type = (supplied_content_type or "").split(";", 1)[0].lower()
    guessed_type = mimetypes.guess_type(filename)[0]
    content_type = (guessed_type if declared_type == "application/octet-stream" else declared_type) or guessed_type or "application/octet-stream"
    site_url = _public_site_url()

    if content_type.startswith("image/"):
        temp_dir = tempfile.TemporaryDirectory(prefix="follia-watermark-")
        source_path = Path(temp_dir.name) / ("source" + extension)
        output_path = Path(temp_dir.name) / ("watermarked" + extension)
        try:
            _copy_storage_file(field, source_path)
            if extension == ".svg" or content_type == "image/svg+xml":
                _watermark_svg(source_path, output_path, username, site_url)
                return _temporary_response(temp_dir, output_path, filename, "image/svg+xml")
            with Image.open(source_path) as source:
                source.load()
                source_format = source.format or mimetypes.guess_extension(content_type, strict=False)
                fmt = source_format.upper() if source_format else "PNG"
                output_frames = []
                overlay_width = max(260, min(680, int(source.width * 0.56)))
                overlay_height = max(76, int(overlay_width * 0.2))
                overlay = _watermark_png(username, site_url, overlay_width, overlay_height)
                for frame in ImageSequence.Iterator(source):
                    image = frame.convert("RGBA")
                    fitted = overlay.copy()
                    fitted.thumbnail((max(1, image.width - 20), max(1, image.height - 20)), Image.Resampling.LANCZOS)
                    margin = max(10, int(min(image.size) * 0.025))
                    image.alpha_composite(fitted, (max(0, image.width - fitted.width - margin), max(0, image.height - fitted.height - margin)))
                    output_frames.append(image)
                if not output_frames:
                    raise WatermarkProcessingError("The image contains no readable frames.")
                options = {}
                if len(output_frames) > 1:
                    options.update(save_all=True, append_images=output_frames[1:], duration=source.info.get("duration", 100), loop=source.info.get("loop", 0))
                if fmt in {"JPEG", "JPG"}:
                    output_frames[0].convert("RGB").save(output_path, format="JPEG", quality=92, optimize=True, **options)
                else:
                    output_frames[0].save(output_path, format=fmt, optimize=True, **options)
            return _temporary_response(temp_dir, output_path, filename, content_type)
        except Exception:
            temp_dir.cleanup()
            raise

    if content_type == "application/pdf" or extension == ".pdf":
        try:
            import pymupdf as fitz
        except ImportError as error:
            raise WatermarkProcessingError("PDF watermarking is unavailable because PyMuPDF is not installed.") from error

        temp_dir = tempfile.TemporaryDirectory(prefix="follia-watermark-")
        source_path = Path(temp_dir.name) / "source.pdf"
        output_path = Path(temp_dir.name) / "watermarked.pdf"
        try:
            _copy_storage_file(field, source_path)
            document = fitz.open(source_path)
            for page in document:
                rect = page.rect
                overlay_width = min(420, max(190, rect.width * 0.46))
                overlay_height = overlay_width * 0.2
                overlay = _watermark_png(username, site_url, int(overlay_width * 2), int(overlay_height * 2))
                from io import BytesIO

                buffer = BytesIO()
                overlay.save(buffer, format="PNG", optimize=True)
                x = max(12, rect.width - overlay_width - 18)
                y = max(12, rect.height - overlay_height - 18)
                page.insert_image(fitz.Rect(x, y, x + overlay_width, y + overlay_height), stream=buffer.getvalue(), overlay=True, keep_proportion=True)
            document.save(output_path, garbage=3, deflate=True)
            document.close()
            return _temporary_response(temp_dir, output_path, filename, "application/pdf")
        except Exception:
            temp_dir.cleanup()
            raise

    if content_type.startswith("video/"):
        ffmpeg = getattr(settings, "FFMPEG_BINARY", "ffmpeg")
        temp_dir = tempfile.TemporaryDirectory(prefix="follia-watermark-")
        source_path = Path(temp_dir.name) / ("source" + extension)
        overlay_path = Path(temp_dir.name) / "watermark.png"
        output_path = Path(temp_dir.name) / "watermarked.mp4"
        try:
            _copy_storage_file(field, source_path)
            _watermark_png(username, site_url).save(overlay_path, format="PNG", optimize=True)
            command = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                "-i", str(source_path), "-i", str(overlay_path),
                "-filter_complex", "[1:v][0:v]scale2ref=w='min(420,main_w*0.42)':h=-1[wm][base];[base][wm]overlay=W-w-20:H-h-20:format=auto",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output_path),
            ]
            subprocess.run(command, check=True, timeout=300, capture_output=True)
            return _temporary_response(temp_dir, output_path, Path(filename).stem + "-follia.mp4", "video/mp4")
        except FileNotFoundError as error:
            temp_dir.cleanup()
            raise WatermarkProcessingError("Video downloads need FFmpeg installed on the server.") from error
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
            temp_dir.cleanup()
            raise WatermarkProcessingError("This video could not be watermarked for download.") from error
        except Exception:
            temp_dir.cleanup()
            raise

    return FileResponse(field.open("rb"), as_attachment=True, filename=filename, content_type=content_type)
