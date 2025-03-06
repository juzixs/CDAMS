from PIL import Image, ImageDraw, ImageFont
import img2pdf
from io import BytesIO
import os
from app.models.pdf_settings import PDFSettings
from app.extensions import db

def draw_text_with_outline(draw, text, position, font, text_color, outline_color, outline_width):
    """绘制带描边的文字"""
    x, y = position
    # 绘制描边
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # 绘制文字
    draw.text(position, text, font=font, fill=text_color)

def generate_vehicle_pass_pdf(plate_numbers, output_path):
    """生成车辆通行证PDF"""
    # 获取PDF设置
    settings = PDFSettings.query.first()
    if not settings:
        settings = PDFSettings()
        db.session.add(settings)
        db.session.commit()

    # 检查字体文件和背景图片是否存在
    font_path = os.path.join('app', 'static', 'fonts', settings.font_path)
    bg_path = os.path.join('app', 'static', 'images', settings.background_image)
    
    if not os.path.exists(font_path):
        raise FileNotFoundError(f"字体文件不存在: {font_path}")
    if not os.path.exists(bg_path):
        raise FileNotFoundError(f"背景图片不存在: {bg_path}")

    # 加载字体和背景图片
    font = ImageFont.truetype(font_path, settings.font_size)
    base_img = Image.open(bg_path).convert("RGB")

    # 处理所有车牌生成图片
    images = []
    for plate in plate_numbers:
        img = base_img.copy()
        draw = ImageDraw.Draw(img)
        
        # 添加文字（带描边）
        draw_text_with_outline(
            draw=draw,
            text=plate,
            position=settings.position_tuple,
            font=font,
            text_color=settings.text_color_tuple,
            outline_color=settings.outline_color_tuple,
            outline_width=settings.outline_width
        )
        
        # 转换为PDF兼容格式
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG", quality=95)
        images.append(img_bytes.getvalue())

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 生成PDF
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(images))

    return len(images) 